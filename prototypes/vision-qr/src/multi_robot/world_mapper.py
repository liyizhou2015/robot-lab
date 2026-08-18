"""
世界坐标映射器

将像素坐标转换为地面世界坐标系
"""

import numpy as np
from typing import Tuple, Optional
import cv2


class WorldMapper:
    """
    世界坐标映射器
    
    假设相机垂直向下拍摄（俯视），建立像素坐标到世界坐标的映射
    """
    
    def __init__(self, 
                 camera_height: float = 2.0,     # 相机高度（米）
                 camera_matrix: Optional[np.ndarray] = None,
                 dist_coeffs: Optional[np.ndarray] = None):
        """
        初始化世界坐标映射器
        
        Args:
            camera_height: 相机离地面高度（米）
            camera_matrix: 相机内参矩阵 (3x3)
            dist_coeffs: 畸变系数
        """
        self.camera_height = camera_height
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs
        
        # 如果提供了相机内参，提取焦距和主点
        if camera_matrix is not None:
            self.fx = camera_matrix[0, 0]
            self.fy = camera_matrix[1, 1]
            self.cx = camera_matrix[0, 2]
            self.cy = camera_matrix[1, 2]
        else:
            # 默认值（需要标定）
            self.fx = 800.0
            self.fy = 800.0
            self.cx = 640.0
            self.cy = 360.0
    
    def pixel_to_world(self, 
                       pixel_point: Tuple[float, float],
                       z_world: float = 0.0) -> Tuple[float, float, float]:
        """
        将像素坐标转换为世界坐标
        
        假设相机垂直向下拍摄，世界坐标系原点在相机正下方地面
        X轴指向相机右方，Y轴指向相机下方（图像下方）
        
        Args:
            pixel_point: (u, v) 像素坐标
            z_world: 物体在世界坐标系中的高度（默认0，地面）
            
        Returns:
            (x, y, z) 世界坐标（米）
        """
        u, v = pixel_point
        
        # 将像素坐标转换为以主点为中心的坐标
        x_norm = (u - self.cx) / self.fx
        y_norm = (v - self.cy) / self.fy
        
        # 计算射线与地面的交点
        # 假设相机垂直向下，光轴与地面垂直
        # 世界坐标：Z轴向上，X轴向右，Y轴向前（相机前方）
        
        # 相机高度为 H，地面在 Z = 0，相机在 Z = H
        # 像素点对应的射线参数方程: P = C + t * d
        # 其中 C = (0, 0, H), d = (x_norm, y_norm, -1)
        # 与地面 Z=0 相交: H + t*(-1) = 0 => t = H
        
        x_world = x_norm * (self.camera_height - z_world)
        y_world = y_norm * (self.camera_height - z_world)
        z_world_actual = z_world
        
        return (x_world, y_world, z_world_actual)
    
    def world_to_pixel(self, 
                       world_point: Tuple[float, float, float]) -> Tuple[int, int]:
        """
        将世界坐标转换为像素坐标
        
        Args:
            world_point: (x, y, z) 世界坐标
            
        Returns:
            (u, v) 像素坐标
        """
        x, y, z = world_point
        
        # 计算归一化坐标
        # 假设相机垂直向下
        x_norm = x / (self.camera_height - z)
        y_norm = y / (self.camera_height - z)
        
        # 转换为像素坐标
        u = int(self.fx * x_norm + self.cx)
        v = int(self.fy * y_norm + self.cy)
        
        return (u, v)
    
    def calculate_orientation(self,
                             tag_center: Tuple[float, float],
                             aux_point: Tuple[float, float]) -> float:
        """
        通过主标签和辅助标签计算机器人朝向
        
        Args:
            tag_center: 主标签中心像素坐标
            aux_point: 辅助标签中心像素坐标（用于确定方向）
            
        Returns:
            theta: 朝向角度（度，0度为X轴正方向）
        """
        # 转换为世界坐标
        world_center = self.pixel_to_world(tag_center)
        world_aux = self.pixel_to_world(aux_point)
        
        # 计算朝向角度
        dx = world_aux[0] - world_center[0]
        dy = world_aux[1] - world_center[1]
        
        theta = np.degrees(np.arctan2(dy, dx))
        
        return theta
    
    def create_ground_grid(self, 
                          image_shape: Tuple[int, int],
                          grid_size: float = 0.5,
                          grid_range: Tuple[float, float] = (5.0, 5.0)) -> np.ndarray:
        """
        创建地面网格可视化图像
        
        Args:
            image_shape: (height, width) 图像尺寸
            grid_size: 网格间距（米）
            grid_range: (x_range, y_range) 网格范围
            
        Returns:
            网格可视化图像
        """
        grid_img = np.zeros((image_shape[0], image_shape[1], 3), dtype=np.uint8)
        
        # X方向网格线
        x = -grid_range[0]
        while x <= grid_range[0]:
            p1 = self.world_to_pixel((x, -grid_range[1], 0))
            p2 = self.world_to_pixel((x, grid_range[1], 0))
            cv2.line(grid_img, p1, p2, (50, 50, 50), 1)
            x += grid_size
        
        # Y方向网格线
        y = -grid_range[1]
        while y <= grid_range[1]:
            p1 = self.world_to_pixel((-grid_range[0], y, 0))
            p2 = self.world_to_pixel((grid_range[0], y, 0))
            cv2.line(grid_img, p1, p2, (50, 50, 50), 1)
            y += grid_size
        
        # 绘制坐标轴
        origin = self.world_to_pixel((0, 0, 0))
        x_axis = self.world_to_pixel((0.5, 0, 0))
        y_axis = self.world_to_pixel((0, 0.5, 0))
        
        cv2.arrowedLine(grid_img, origin, x_axis, (0, 0, 255), 2)  # X轴 - 红色
        cv2.arrowedLine(grid_img, origin, y_axis, (0, 255, 0), 2)  # Y轴 - 绿色
        cv2.putText(grid_img, "X", x_axis, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv2.putText(grid_img, "Y", y_axis, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        return grid_img


class HomographyMapper:
    """
    使用单应性矩阵的坐标映射器
    
    通过4个以上的标定点计算像素坐标到世界坐标的映射
    适用于相机不完全垂直的情况
    """
    
    def __init__(self):
        self.H = None  # 单应性矩阵 (3x3)
        self.H_inv = None
    
    def calibrate(self, 
                  pixel_points: np.ndarray,  # Nx2 像素坐标
                  world_points: np.ndarray):  # Nx2 世界坐标 (X, Y)
        """
        通过标定点计算单应性矩阵
        
        至少需要4个不共线的点
        """
        if len(pixel_points) < 4:
            raise ValueError("至少需要4个标定点")
        
        # 计算单应性矩阵
        self.H, _ = cv2.findHomography(pixel_points, world_points)
        self.H_inv, _ = cv2.findHomography(world_points, pixel_points)
        
        return self.H is not None
    
    def pixel_to_world(self, pixel_point: Tuple[float, float]) -> Tuple[float, float]:
        """像素坐标转世界坐标"""
        if self.H is None:
            raise RuntimeError("尚未标定，请先调用 calibrate()")
        
        pt = np.array([[pixel_point[0], pixel_point[1], 1.0]])
        world_pt = self.H @ pt.T
        world_pt = world_pt / world_pt[2]
        
        return (world_pt[0, 0], world_pt[1, 0])
    
    def world_to_pixel(self, world_point: Tuple[float, float]) -> Tuple[int, int]:
        """世界坐标转像素坐标"""
        if self.H_inv is None:
            raise RuntimeError("尚未标定，请先调用 calibrate()")
        
        pt = np.array([[world_point[0], world_point[1], 1.0]])
        pixel_pt = self.H_inv @ pt.T
        pixel_pt = pixel_pt / pixel_pt[2]
        
        return (int(pixel_pt[0, 0]), int(pixel_pt[1, 0]))
