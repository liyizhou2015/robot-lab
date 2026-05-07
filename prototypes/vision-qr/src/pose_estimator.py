"""
位姿估计与3D定位模块
支持相机标定和二维码3D位姿估计
"""

import cv2
import numpy as np
from typing import Tuple, Optional, List
from dataclasses import dataclass


@dataclass
class CameraCalibration:
    """相机标定参数"""
    camera_matrix: np.ndarray      # 3x3 内参矩阵
    dist_coeffs: np.ndarray        # 畸变系数
    image_size: Tuple[int, int]    # 图像尺寸 (width, height)


@dataclass
class Pose3D:
    """3D位姿"""
    position: np.ndarray      # 平移向量 tvec [x, y, z]
    rotation: np.ndarray      # 旋转向量 rvec
    rotation_matrix: np.ndarray  # 3x3 旋转矩阵
    euler_angles: np.ndarray  # 欧拉角 [roll, pitch, yaw] (度)


class PoseEstimator:
    """3D位姿估计器"""
    
    def __init__(self, marker_size: float = 0.05):
        """
        初始化
        
        Args:
            marker_size: 二维码实际边长（米）
        """
        self.marker_size = marker_size
        
        # 二维码3D角点（物体坐标系，中心在原点）
        half = marker_size / 2
        self.obj_points = np.array([
            [-half,  half, 0],   # 左上
            [ half,  half, 0],   # 右上
            [ half, -half, 0],   # 右下
            [-half, -half, 0]    # 左下
        ], dtype=np.float32)
    
    def estimate_pose(self, corners: np.ndarray,
                     camera_matrix: np.ndarray,
                     dist_coeffs: Optional[np.ndarray] = None) -> Optional[Pose3D]:
        """
        估计二维码的3D位姿
        
        Args:
            corners: 4x2 图像角点坐标
            camera_matrix: 3x3 相机内参矩阵
            dist_coeffs: 畸变系数
            
        Returns:
            Pose3D 位姿信息
        """
        if dist_coeffs is None:
            dist_coeffs = np.zeros((4, 1))
        
        # PnP求解
        success, rvec, tvec = cv2.solvePnP(
            self.obj_points,
            corners.astype(np.float32),
            camera_matrix,
            dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )
        
        if not success:
            return None
        
        # 转换为旋转矩阵
        R, _ = cv2.Rodrigues(rvec)
        
        # 计算欧拉角
        euler = self.rotation_matrix_to_euler_angles(R)
        
        return Pose3D(
            position=tvec.flatten(),
            rotation=rvec.flatten(),
            rotation_matrix=R,
            euler_angles=euler
        )
    
    @staticmethod
    def rotation_matrix_to_euler_angles(R: np.ndarray) -> np.ndarray:
        """
        旋转矩阵转欧拉角（ZYX顺序，单位：度）
        
        Args:
            R: 3x3 旋转矩阵
            
        Returns:
            [roll, pitch, yaw] 欧拉角
        """
        sy = np.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
        
        singular = sy < 1e-6
        
        if not singular:
            x = np.arctan2(R[2, 1], R[2, 2])
            y = np.arctan2(-R[2, 0], sy)
            z = np.arctan2(R[1, 0], R[0, 0])
        else:
            x = np.arctan2(-R[1, 2], R[1, 1])
            y = np.arctan2(-R[2, 0], sy)
            z = 0
        
        return np.degrees([x, y, z])  # 转换为度
    
    def project_point(self, point_3d: np.ndarray,
                     camera_matrix: np.ndarray,
                     dist_coeffs: Optional[np.ndarray] = None,
                     rvec: Optional[np.ndarray] = None,
                     tvec: Optional[np.ndarray] = None) -> np.ndarray:
        """
        将3D点投影到图像平面
        
        Args:
            point_3d: 3D点坐标
            camera_matrix: 相机内参
            dist_coeffs: 畸变系数
            rvec: 旋转向量（世界到相机）
            tvec: 平移向量（世界到相机）
            
        Returns:
            2D图像坐标
        """
        if dist_coeffs is None:
            dist_coeffs = np.zeros((4, 1))
        if rvec is None:
            rvec = np.zeros((3, 1))
        if tvec is None:
            tvec = np.zeros((3, 1))
        
        point_2d, _ = cv2.projectPoints(
            point_3d.reshape(1, 3).astype(np.float32),
            rvec, tvec, camera_matrix, dist_coeffs
        )
        return point_2d.reshape(2)


class CameraCalibrator:
    """相机标定器"""
    
    def __init__(self, checkerboard_size: Tuple[int, int] = (9, 6),
                 square_size: float = 0.025):
        """
        初始化
        
        Args:
            checkerboard_size: 棋盘格内角点数量 (width, height)
            square_size: 棋盘格方格边长（米）
        """
        self.checkerboard_size = checkerboard_size
        self.square_size = square_size
        
        # 准备3D角点模板
        self.objp = np.zeros((checkerboard_size[0] * checkerboard_size[1], 3), np.float32)
        self.objp[:, :2] = np.mgrid[0:checkerboard_size[0], 0:checkerboard_size[1]].T.reshape(-1, 2)
        self.objp *= square_size
    
    def calibrate_from_images(self, image_paths: List[str]) -> Optional[CameraCalibration]:
        """
        从棋盘格图像标定相机
        
        Args:
            image_paths: 棋盘格图像路径列表
            
        Returns:
            相机标定参数
        """
        obj_points = []  # 3D点
        img_points = []  # 2D点
        image_size = None
        
        print(f"处理 {len(image_paths)} 张标定图像...")
        
        for img_path in image_paths:
            img = cv2.imread(img_path)
            if img is None:
                continue
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            if image_size is None:
                image_size = (gray.shape[1], gray.shape[0])
            
            # 检测棋盘格角点
            ret, corners = cv2.findChessboardCorners(gray, self.checkerboard_size, None)
            
            if ret:
                # 精细化角点位置
                corners2 = cv2.cornerSubPix(
                    gray, corners, (11, 11), (-1, -1),
                    criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
                )
                
                obj_points.append(self.objp)
                img_points.append(corners2)
                print(f"  ✓ {img_path}: 检测到角点")
            else:
                print(f"  ✗ {img_path}: 未检测到角点")
        
        if len(obj_points) < 3:
            print("错误: 有效标定图像太少（至少需要3张）")
            return None
        
        # 执行标定
        print("\n执行相机标定...")
        ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            obj_points, img_points, image_size, None, None
        )
        
        if ret:
            print("标定成功!")
            print(f"相机内参:\n{camera_matrix}")
            print(f"畸变系数:\n{dist_coeffs.flatten()}")
            
            # 计算重投影误差
            total_error = 0
            for i in range(len(obj_points)):
                img_points2, _ = cv2.projectPoints(
                    obj_points[i], rvecs[i], tvecs[i], camera_matrix, dist_coeffs
                )
                error = cv2.norm(img_points[i], img_points2, cv2.NORM_L2) / len(img_points2)
                total_error += error
            
            avg_error = total_error / len(obj_points)
            print(f"平均重投影误差: {avg_error:.4f} 像素")
            
            return CameraCalibration(
                camera_matrix=camera_matrix,
                dist_coeffs=dist_coeffs,
                image_size=image_size
            )
        else:
            print("标定失败!")
            return None


def load_calibration(calibration_file: str) -> Optional[CameraCalibration]:
    """从文件加载标定参数"""
    import yaml
    
    try:
        with open(calibration_file, 'r') as f:
            data = yaml.safe_load(f)
        
        return CameraCalibration(
            camera_matrix=np.array(data['camera_matrix']),
            dist_coeffs=np.array(data['dist_coeffs']),
            image_size=tuple(data['image_size'])
        )
    except Exception as e:
        print(f"加载标定文件失败: {e}")
        return None


def save_calibration(calibration: CameraCalibration, calibration_file: str):
    """保存标定参数到文件"""
    import yaml
    
    data = {
        'camera_matrix': calibration.camera_matrix.tolist(),
        'dist_coeffs': calibration.dist_coeffs.tolist(),
        'image_size': list(calibration.image_size)
    }
    
    with open(calibration_file, 'w') as f:
        yaml.dump(data, f)
    
    print(f"标定参数已保存: {calibration_file}")


if __name__ == "__main__":
    print("位姿估计与相机标定模块")
    print("使用示例:")
    print("  from pose_estimator import PoseEstimator, CameraCalibrator")
