"""
二维码检测模块 - 模拟版本（用于无 ArUco 支持的环境）
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class MarkerDetection:
    """检测结果数据类"""
    marker_id: int
    corners: np.ndarray
    center: np.ndarray
    pose: Optional[Tuple[np.ndarray, np.ndarray]] = None


class AprilTagDetector:
    """AprilTag 检测器 - 模拟版本"""
    
    def __init__(self, marker_size: float = 0.05):
        self.marker_size = marker_size
        self._initialized = False
        
    def _try_init_aruco(self):
        """尝试初始化 ArUco"""
        if self._initialized:
            return True
        try:
            self._dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
            self._parameters = cv2.aruco.DetectorParameters()
            self._initialized = True
            return True
        except Exception as e:
            print(f"ArUco 初始化失败: {e}")
            return False
    
    def detect(self, frame: np.ndarray) -> List[MarkerDetection]:
        """检测二维码"""
        if not self._try_init_aruco():
            # 模拟检测：返回假数据用于测试
            return self._mock_detect(frame)
        
        # 真实检测
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, rejected = cv2.aruco.detectMarkers(
            gray, self._dictionary, parameters=self._parameters
        )
        
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
    
    def _mock_detect(self, frame: np.ndarray) -> List[MarkerDetection]:
        """模拟检测 - 用于测试"""
        # 在图像中心返回一个模拟的检测结果
        h, w = frame.shape[:2]
        center = np.array([w/2, h/2])
        size = 50
        corners = np.array([
            [center[0]-size, center[1]-size],
            [center[0]+size, center[1]-size],
            [center[0]+size, center[1]+size],
            [center[0]-size, center[1]+size]
        ])
        return [MarkerDetection(marker_id=0, corners=corners, center=center)]
    
    def draw_detections(self, frame: np.ndarray,
                       detections: List[MarkerDetection],
                       **kwargs) -> np.ndarray:
        """绘制检测结果"""
        img = frame.copy()
        for det in detections:
            corners = det.corners.astype(np.int32)
            cv2.polylines(img, [corners], True, (0, 255, 0), 2)
            center = tuple(det.center.astype(int))
            cv2.circle(img, center, 5, (0, 0, 255), -1)
            cv2.putText(img, f"ID: {det.marker_id}",
                       (center[0] + 10, center[1]),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        return img
