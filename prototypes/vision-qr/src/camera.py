"""
相机接口模块
支持USB相机和网络相机
"""

import cv2
import numpy as np
from typing import Tuple, Optional


class Camera:
    """相机基类"""
    
    def __init__(self, camera_id: int = 0, width: int = 1280, height: int = 720,
                 video_path: str = None):
        """
        初始化相机
        
        Args:
            camera_id: 相机ID (0为默认相机)
            width: 图像宽度
            height: 图像高度
            video_path: 视频文件路径（用于测试）
        """
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.video_path = video_path
        self.cap = None
        self.is_opened = False
        
    def open(self) -> bool:
        """打开相机或视频文件"""
        if self.video_path:
            # 打开视频文件
            self.cap = cv2.VideoCapture(self.video_path)
            source = f"视频文件 {self.video_path}"
        else:
            # 打开相机
            self.cap = cv2.VideoCapture(self.camera_id)
            source = f"相机 {self.camera_id}"
        
        if not self.cap.isOpened():
            print(f"无法打开 {source}")
            return False
        
        # 获取实际分辨率
        if not self.video_path:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        self.is_opened = True
        print(f"{source} 已打开: {actual_width}x{actual_height}")
        return True
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        读取一帧图像
        
        Returns:
            (success, frame): 是否成功和图像帧
        """
        if not self.is_opened:
            return False, None
        return self.cap.read()
    
    def release(self):
        """释放相机资源"""
        if self.cap:
            self.cap.release()
            self.is_opened = False
            print(f"相机 {self.camera_id} 已释放")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.release()


class CalibratedCamera(Camera):
    """带标定参数的相机"""
    
    def __init__(self, camera_id: int = 0, width: int = 1280, height: int = 720,
                 camera_matrix: Optional[np.ndarray] = None,
                 dist_coeffs: Optional[np.ndarray] = None):
        """
        初始化带标定的相机
        
        Args:
            camera_matrix: 3x3 相机内参矩阵
            dist_coeffs: 畸变系数 [k1, k2, p1, p2, k3]
        """
        super().__init__(camera_id, width, height)
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs
        self.new_camera_matrix = None
        self.roi = None
        
    def undistort(self, frame: np.ndarray) -> np.ndarray:
        """
        去畸变
        
        Args:
            frame: 原始图像
            
        Returns:
            去畸变后的图像
        """
        if self.camera_matrix is None or self.dist_coeffs is None:
            return frame
            
        # 计算最优新相机矩阵
        if self.new_camera_matrix is None:
            h, w = frame.shape[:2]
            self.new_camera_matrix, self.roi = cv2.getOptimalNewCameraMatrix(
                self.camera_matrix, self.dist_coeffs, (w, h), 1, (w, h)
            )
        
        # 去畸变
        undistorted = cv2.undistort(
            frame, self.camera_matrix, self.dist_coeffs,
            None, self.new_camera_matrix
        )
        
        # 裁剪有效区域
        if self.roi:
            x, y, w, h = self.roi
            undistorted = undistorted[y:y+h, x:x+w]
            
        return undistorted
    
    def read_undistorted(self) -> Tuple[bool, Optional[np.ndarray]]:
        """读取并去畸变"""
        success, frame = self.read()
        if not success:
            return False, None
        return True, self.undistort(frame)


def list_cameras(max_index: int = 10) -> list:
    """
    列出可用的相机
    
    Args:
        max_index: 最大检测索引
        
    Returns:
        可用相机ID列表
    """
    available = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                available.append(i)
        cap.release()
    return available


if __name__ == "__main__":
    # 测试相机
    print("检测可用相机...")
    cameras = list_cameras()
    print(f"可用相机: {cameras}")
    
    if cameras:
        with Camera(cameras[0]) as cam:
            print("按 'q' 退出")
            while True:
                success, frame = cam.read()
                if not success:
                    break
                    
                cv2.imshow("Camera Test", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        cv2.destroyAllWindows()
