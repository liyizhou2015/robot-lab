"""
机器人实体类

定义单个机器人的状态和行为
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple
from enum import Enum, auto
import numpy as np
from datetime import datetime


class RobotState(Enum):
    """机器人状态"""
    IDLE = auto()           # 空闲
    MOVING = auto()         # 运动中
    ARRIVED = auto()        # 已到达目标
    ERROR = auto()          # 错误状态
    OFFLINE = auto()        # 离线


@dataclass
class RobotPose:
    """机器人位姿"""
    x: float = 0.0          # 世界坐标 X (米)
    y: float = 0.0          # 世界坐标 Y (米)
    theta: float = 0.0      # 朝向角度 (度，0度为X轴正方向)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.theta)
    
    def distance_to(self, other: 'RobotPose') -> float:
        """计算到另一个位姿的欧氏距离"""
        return np.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


@dataclass
class Robot:
    """
    机器人类
    
    每个机器人通过唯一的 AprilTag ID 识别
    可以有一个主标签(ID)和一个辅助标签用于确定方向
    """
    # 标识信息
    robot_id: int                           # 机器人ID
    name: str                               # 机器人名称
    tag_id: int                             # 主 AprilTag ID
    aux_tag_id: Optional[int] = None        # 辅助标签ID（用于确定朝向）
    
    # 状态信息
    state: RobotState = RobotState.IDLE
    current_pose: RobotPose = field(default_factory=RobotPose)
    target_pose: Optional[RobotPose] = None
    
    # 历史轨迹
    trajectory: list = field(default_factory=list)
    max_trajectory_length: int = 100        # 最大轨迹点数
    
    # 通信信息
    ip_address: Optional[str] = None        # IP地址（WiFi控制）
    port: Optional[int] = None              # 端口号
    last_heartbeat: Optional[datetime] = None
    
    def update_pose(self, x: float, y: float, theta: float):
        """更新当前位姿并记录轨迹"""
        # 保存历史轨迹
        if len(self.trajectory) >= self.max_trajectory_length:
            self.trajectory.pop(0)
        self.trajectory.append(self.current_pose)
        
        # 更新位姿
        self.current_pose = RobotPose(x=x, y=y, theta=theta)
        self.last_heartbeat = datetime.now()
    
    def set_target(self, x: float, y: float, theta: Optional[float] = None):
        """设置目标点"""
        self.target_pose = RobotPose(x=x, y=y, theta=theta or self.current_pose.theta)
        self.state = RobotState.MOVING
    
    def check_arrived(self, threshold: float = 0.05) -> bool:
        """检查是否到达目标点"""
        if self.target_pose is None:
            return False
        
        distance = self.current_pose.distance_to(self.target_pose)
        if distance < threshold:
            self.state = RobotState.ARRIVED
            return True
        return False
    
    def get_velocity_command(self) -> Tuple[float, float]:
        """
        计算速度指令 (v, omega)
        
        简单的比例控制器
        """
        if self.target_pose is None or self.state != RobotState.MOVING:
            return (0.0, 0.0)
        
        # 计算到目标的距离和角度
        dx = self.target_pose.x - self.current_pose.x
        dy = self.target_pose.y - self.current_pose.y
        
        target_angle = np.degrees(np.arctan2(dy, dx))
        angle_diff = target_angle - self.current_pose.theta
        
        # 归一化角度到 [-180, 180]
        while angle_diff > 180:
            angle_diff -= 360
        while angle_diff < -180:
            angle_diff += 360
        
        distance = np.sqrt(dx**2 + dy**2)
        
        # 简单的比例控制
        Kp_v = 0.5      # 线速度增益
        Kp_w = 0.1      # 角速度增益
        
        v = min(Kp_v * distance, 0.5)  # 最大线速度 0.5 m/s
        omega = Kp_w * angle_diff      # 角速度
        
        return (v, omega)
    
    def __repr__(self):
        return f"Robot({self.name}, ID={self.robot_id}, Tag={self.tag_id}, State={self.state.name})"
