"""
二维码检测模块
支持 AprilTag (OpenCV 4.10+ 版本)
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class MarkerDetection:
    """检测结果数据类"""
    marker_id: int
    corners: np.ndarray  # 4x2 角点坐标
    center: np.ndarray   # 中心点坐标
    pose: Optional[Tuple[np.ndarray, np.ndarray]] = None  # (rvec, tvec)


class AprilTagDetector:
    """AprilTag 二维码检测器 (OpenCV 4.10+ 版本)"""
    
    def __init__(self, marker_size: float = 0.05):  # 默认5cm
        """
        初始化检测器
        
        Args:
            marker_size: 二维码实际边长（米）
        """
        self.marker_size = marker_size
        
        # OpenCV 4.10+ 新 API
        self.dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
        self.parameters = cv2.aruco.DetectorParameters()
        
        # 创建检测器
        self.detector = cv2.aruco.ArucoDetector(self.dictionary, self.parameters)
        
    def detect(self, frame: np.ndarray) -> List[MarkerDetection]:
        """
        检测二维码
        
        Args:
            frame: 输入图像
            
        Returns:
            检测结果列表
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, rejected = self.detector.detectMarkers(gray)
        
        detections = []
        if ids is not None:
            for i, marker_id in enumerate(ids.flatten()):
                corner = corners[i].reshape(4, 2)
                center = np.mean(corner, axis=0)
                detections.append(MarkerDetection(
                    marker_id=int(marker_id),
                    corners=corner,
                    center=center
                ))
                
        return detections
    
    def estimate_pose(self, detection: MarkerDetection,
                     camera_matrix: np.ndarray,
                     dist_coeffs: Optional[np.ndarray] = None) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        估计单个二维码的位姿
        
        Args:
            detection: 检测结果
            camera_matrix: 相机内参矩阵
            dist_coeffs: 畸变系数
            
        Returns:
            (rvec, tvec) 旋转矢量和平移矢量
        """
        if dist_coeffs is None:
            dist_coeffs = np.zeros((4, 1))
            
        # 3D 角点（二维码坐标系）
        half_size = self.marker_size / 2
        obj_points = np.array([
            [-half_size, half_size, 0],
            [half_size, half_size, 0],
            [half_size, -half_size, 0],
            [-half_size, -half_size, 0]
        ], dtype=np.float32)
        
        # PnP 求解
        success, rvec, tvec = cv2.solvePnP(
            obj_points, detection.corners.astype(np.float32),
            camera_matrix, dist_coeffs
        )
        
        if success:
            detection.pose = (rvec, tvec)
            return rvec, tvec
        return None
    
    def detect_and_estimate(self, frame: np.ndarray,
                           camera_matrix: np.ndarray,
                           dist_coeffs: Optional[np.ndarray] = None) -> List[MarkerDetection]:
        """
        检测并估计所有二维码位姿
        
        Args:
            frame: 输入图像
            camera_matrix: 相机内参矩阵
            dist_coeffs: 畸变系数
            
        Returns:
            带位姿的检测结果列表
        """
        detections = self.detect(frame)
        for det in detections:
            self.estimate_pose(det, camera_matrix, dist_coeffs)
        return detections
    
    def draw_detections(self, frame: np.ndarray,
                       detections: List[MarkerDetection],
                       draw_axes: bool = False,
                       camera_matrix: Optional[np.ndarray] = None,
                       dist_coeffs: Optional[np.ndarray] = None) -> np.ndarray:
        """
        绘制检测结果
        
        Args:
            frame: 原始图像
            detections: 检测结果
            draw_axes: 是否绘制坐标轴
            camera_matrix: 相机内参（绘制坐标轴需要）
            dist_coeffs: 畸变系数
            
        Returns:
            绘制后的图像
        """
        img = frame.copy()
        
        for det in detections:
            # 绘制边框
            corners = det.corners.astype(np.int32)
            cv2.polylines(img, [corners], True, (0, 255, 0), 2)
            
            # 绘制中心
            center = tuple(det.center.astype(int))
            cv2.circle(img, center, 5, (0, 0, 255), -1)
            
            # 绘制ID
            cv2.putText(img, f"ID: {det.marker_id}",
                       (center[0] + 10, center[1]),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            
            # 绘制位姿信息
            if det.pose:
                rvec, tvec = det.pose
                # 绘制距离
                distance = np.linalg.norm(tvec)
                cv2.putText(img, f"D: {distance:.3f}m",
                           (center[0] + 10, center[1] + 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                
                # 绘制坐标轴
                if draw_axes and camera_matrix is not None:
                    if dist_coeffs is None:
                        dist_coeffs = np.zeros((4, 1))
                    cv2.drawFrameAxes(img, camera_matrix, dist_coeffs,
                                     rvec, tvec, self.marker_size / 2)
        
        return img


if __name__ == "__main__":
    print("AprilTag 检测器模块 (OpenCV 4.10+)")
    print("使用示例: python test_detection_offline.py")
