"""
机器人管理器

管理多个机器人的注册、状态更新和任务分配
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from datetime import datetime, timedelta

from .robot import Robot, RobotState, RobotPose
from .world_mapper import WorldMapper


@dataclass
class DetectionInfo:
    """检测信息"""
    tag_id: int
    center: Tuple[float, float]  # 像素坐标
    corners: np.ndarray
    aux_tag_id: Optional[int] = None
    aux_center: Optional[Tuple[float, float]] = None


class RobotManager:
    """
    机器人管理器
    
    管理所有机器人的注册、状态更新和任务分配
    """
    
    def __init__(self, 
                 world_mapper: WorldMapper,
                 robot_timeout: float = 5.0):  # 机器人超时时间（秒）
        self.world_mapper = world_mapper
        self.robot_timeout = robot_timeout
        
        # 机器人字典: {robot_id: Robot}
        self.robots: Dict[int, Robot] = {}
        
        # 标签到机器人的映射: {tag_id: robot_id}
        self.tag_to_robot: Dict[int, int] = {}
        
        # 检测统计
        self.detection_count = 0
        self.last_detection_time = None
    
    def register_robot(self, 
                       robot_id: int,
                       name: str,
                       tag_id: int,
                       aux_tag_id: Optional[int] = None,
                       ip_address: Optional[str] = None,
                       port: Optional[int] = None) -> Robot:
        """
        注册新机器人
        
        Args:
            robot_id: 机器人唯一ID
            name: 机器人名称
            tag_id: 主 AprilTag ID
            aux_tag_id: 辅助标签ID（可选，用于确定朝向）
            ip_address: IP地址（WiFi控制）
            port: 端口号
            
        Returns:
            创建的 Robot 实例
        """
        if robot_id in self.robots:
            raise ValueError(f"机器人 ID {robot_id} 已存在")
        
        if tag_id in self.tag_to_robot:
            raise ValueError(f"标签 ID {tag_id} 已被机器人使用")
        
        robot = Robot(
            robot_id=robot_id,
            name=name,
            tag_id=tag_id,
            aux_tag_id=aux_tag_id,
            ip_address=ip_address,
            port=port
        )
        
        self.robots[robot_id] = robot
        self.tag_to_robot[tag_id] = robot_id
        
        print(f"注册机器人: {robot}")
        return robot
    
    def unregister_robot(self, robot_id: int):
        """注销机器人"""
        if robot_id not in self.robots:
            return
        
        robot = self.robots[robot_id]
        del self.tag_to_robot[robot.tag_id]
        del self.robots[robot_id]
        
        print(f"注销机器人: {robot.name}")
    
    def update_from_detections(self, detections: List[DetectionInfo]):
        """
        从视觉检测结果更新所有机器人位置
        
        Args:
            detections: 检测结果列表
        """
        self.detection_count += 1
        self.last_detection_time = datetime.now()
        
        # 标记所有机器人为离线（稍后更新检测到的）
        for robot in self.robots.values():
            if robot.last_heartbeat and \
               (datetime.now() - robot.last_heartbeat).seconds > self.robot_timeout:
                robot.state = RobotState.OFFLINE
        
        # 处理检测结果
        for det in detections:
            if det.tag_id not in self.tag_to_robot:
                # 未注册的标签，可能是新机器人或干扰
                continue
            
            robot_id = self.tag_to_robot[det.tag_id]
            robot = self.robots[robot_id]
            
            # 转换到世界坐标
            world_pos = self.world_mapper.pixel_to_world(det.center)
            
            # 计算朝向
            if det.aux_tag_id is not None and det.aux_center is not None:
                # 使用辅助标签计算朝向
                theta = self.world_mapper.calculate_orientation(
                    det.center, det.aux_center
                )
            else:
                # 无法确定朝向，使用之前的朝向或0
                theta = robot.current_pose.theta
            
            # 更新机器人位姿
            robot.update_pose(world_pos[0], world_pos[1], theta)
            
            # 检查是否到达目标
            if robot.state == RobotState.MOVING:
                robot.check_arrived()
    
    def get_robot(self, robot_id: int) -> Optional[Robot]:
        """获取机器人实例"""
        return self.robots.get(robot_id)
    
    def get_robot_by_tag(self, tag_id: int) -> Optional[Robot]:
        """通过标签ID获取机器人"""
        if tag_id not in self.tag_to_robot:
            return None
        return self.robots.get(self.tag_to_robot[tag_id])
    
    def get_all_robots(self) -> List[Robot]:
        """获取所有机器人列表"""
        return list(self.robots.values())
    
    def get_active_robots(self) -> List[Robot]:
        """获取在线的机器人列表"""
        return [r for r in self.robots.values() 
                if r.state not in [RobotState.OFFLINE, RobotState.ERROR]]
    
    def send_goal(self, robot_id: int, target: Tuple[float, float, Optional[float]]):
        """
        发送目标点到指定机器人
        
        Args:
            robot_id: 机器人ID
            target: (x, y, theta) 目标位姿，theta可选
        """
        robot = self.get_robot(robot_id)
        if robot is None:
            print(f"错误: 机器人 {robot_id} 不存在")
            return False
        
        x, y = target[0], target[1]
        theta = target[2] if len(target) > 2 else None
        
        robot.set_target(x, y, theta)
        print(f"发送目标点到 {robot.name}: ({x:.2f}, {y:.2f}, {theta if theta else '保持'})")
        return True
    
    def send_goals(self, goals: Dict[int, Tuple[float, float, Optional[float]]]):
        """
        批量发送目标点
        
        Args:
            goals: {robot_id: (x, y, theta)} 目标字典
        """
        for robot_id, target in goals.items():
            self.send_goal(robot_id, target)
    
    def emergency_stop(self, robot_id: Optional[int] = None):
        """
        紧急停止
        
        Args:
            robot_id: 指定机器人，None表示全部
        """
        if robot_id is not None:
            robot = self.get_robot(robot_id)
            if robot:
                robot.state = RobotState.IDLE
                robot.target_pose = None
                print(f"紧急停止: {robot.name}")
        else:
            for robot in self.robots.values():
                robot.state = RobotState.IDLE
                robot.target_pose = None
            print("紧急停止: 所有机器人")
    
    def get_status_report(self) -> str:
        """获取状态报告"""
        lines = ["=" * 60, "机器人状态报告", "=" * 60]
        
        lines.append(f"注册机器人数量: {len(self.robots)}")
        lines.append(f"在线机器人数量: {len(self.get_active_robots())}")
        lines.append(f"总检测次数: {self.detection_count}")
        lines.append("")
        
        for robot in self.robots.values():
            pose = robot.current_pose
            lines.append(f"  {robot.name} (ID={robot.robot_id})")
            lines.append(f"    状态: {robot.state.name}")
            lines.append(f"    位置: ({pose.x:.3f}, {pose.y:.3f}) m")
            lines.append(f"    朝向: {pose.theta:.1f}°")
            if robot.target_pose:
                lines.append(f"    目标: ({robot.target_pose.x:.3f}, {robot.target_pose.y:.3f}) m")
            lines.append("")
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    def save_configuration(self, filepath: str):
        """保存机器人配置到文件"""
        import json
        
        config = {
            'robots': [],
            'world_mapper': {
                'camera_height': self.world_mapper.camera_height
            }
        }
        
        for robot in self.robots.values():
            config['robots'].append({
                'robot_id': robot.robot_id,
                'name': robot.name,
                'tag_id': robot.tag_id,
                'aux_tag_id': robot.aux_tag_id,
                'ip_address': robot.ip_address,
                'port': robot.port
            })
        
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"配置已保存: {filepath}")
    
    def load_configuration(self, filepath: str):
        """从文件加载机器人配置"""
        import json
        
        with open(filepath, 'r') as f:
            config = json.load(f)
        
        # 清空现有机器人
        self.robots.clear()
        self.tag_to_robot.clear()
        
        # 加载机器人
        for robot_config in config.get('robots', []):
            self.register_robot(**robot_config)
        
        print(f"配置已加载: {filepath}")
