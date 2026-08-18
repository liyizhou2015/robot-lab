"""
命令下发模块

负责与机器人通信，下发控制命令
"""

from typing import Optional, Tuple, Dict
from enum import Enum, auto
import socket
import json
from dataclasses import dataclass

from .robot import Robot, RobotState


class CommandType(Enum):
    """命令类型"""
    VELOCITY = auto()       # 速度控制 (v, omega)
    POSITION = auto()       # 位置控制 (x, y, theta)
    STOP = auto()           # 停止
    RESET = auto()          # 复位
    HEARTBEAT = auto()      # 心跳


@dataclass
class Command:
    """命令数据类"""
    cmd_type: CommandType
    robot_id: int
    data: Dict  # 命令参数
    timestamp: float  # 发送时间戳


class Commander:
    """
    命令下发器
    
    支持多种通信方式：
    1. UDP/TCP Socket (WiFi)
    2. 串口 (USB/蓝牙)
    3. ROS Topic
    """
    
    def __init__(self, protocol: str = "udp"):
        """
        初始化命令下发器
        
        Args:
            protocol: 通信协议 ("udp", "tcp", "serial", "ros")
        """
        self.protocol = protocol
        self.socket: Optional[socket.socket] = None
        self.is_connected = False
        
        # 统计
        self.commands_sent = 0
        self.commands_failed = 0
    
    def connect(self, **kwargs) -> bool:
        """
        建立连接
        
        UDP: connect(port=12345)
        TCP: connect(host="192.168.1.100", port=12345)
        """
        try:
            if self.protocol == "udp":
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.socket.settimeout(1.0)
                self.is_connected = True
                print(f"UDP 通信已初始化")
                return True
            
            elif self.protocol == "tcp":
                host = kwargs.get("host", "localhost")
                port = kwargs.get("port", 12345)
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((host, port))
                self.socket.settimeout(1.0)
                self.is_connected = True
                print(f"TCP 连接已建立: {host}:{port}")
                return True
            
            else:
                print(f"不支持的协议: {self.protocol}")
                return False
        
        except Exception as e:
            print(f"连接失败: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.socket:
            self.socket.close()
            self.socket = None
        self.is_connected = False
        print("连接已断开")
    
    def send_velocity(self, robot: Robot, v: float, omega: float) -> bool:
        """
        发送速度命令
        
        Args:
            robot: 机器人实例
            v: 线速度 (m/s)
            omega: 角速度 (deg/s)
        """
        if not self.is_connected:
            return False
        
        cmd = {
            "type": "velocity",
            "robot_id": robot.robot_id,
            "v": v,
            "omega": omega,
            "timestamp": self._get_timestamp()
        }
        
        return self._send_command(robot, cmd)
    
    def send_position(self, robot: Robot, x: float, y: float, theta: Optional[float] = None) -> bool:
        """
        发送位置目标命令
        
        Args:
            robot: 机器人实例
            x: 目标X坐标
            y: 目标Y坐标
            theta: 目标朝向（可选）
        """
        if not self.is_connected:
            return False
        
        cmd = {
            "type": "position",
            "robot_id": robot.robot_id,
            "x": x,
            "y": y,
            "timestamp": self._get_timestamp()
        }
        
        if theta is not None:
            cmd["theta"] = theta
        
        return self._send_command(robot, cmd)
    
    def send_stop(self, robot: Robot) -> bool:
        """发送停止命令"""
        if not self.is_connected:
            return False
        
        cmd = {
            "type": "stop",
            "robot_id": robot.robot_id,
            "timestamp": self._get_timestamp()
        }
        
        return self._send_command(robot, cmd)
    
    def update_robot(self, robot: Robot) -> bool:
        """
        根据机器人当前状态发送相应命令
        
        这通常在每个控制周期调用
        """
        if robot.state == RobotState.MOVING and robot.target_pose is not None:
            # 计算速度命令
            v, omega = robot.get_velocity_command()
            return self.send_velocity(robot, v, omega)
        
        elif robot.state == RobotState.IDLE:
            # 发送停止命令
            return self.send_stop(robot)
        
        return True
    
    def _send_command(self, robot: Robot, cmd: Dict) -> bool:
        """底层发送命令"""
        if robot.ip_address is None or robot.port is None:
            # 模拟模式：打印命令但不发送
            print(f"[模拟] 发送到 {robot.name}: {cmd}")
            self.commands_sent += 1
            return True
        
        try:
            message = json.dumps(cmd).encode('utf-8')
            
            if self.protocol == "udp":
                self.socket.sendto(message, (robot.ip_address, robot.port))
            elif self.protocol == "tcp":
                self.socket.sendall(message)
            
            self.commands_sent += 1
            return True
        
        except Exception as e:
            print(f"发送失败 ({robot.name}): {e}")
            self.commands_failed += 1
            return False
    
    def _get_timestamp(self) -> float:
        """获取当前时间戳"""
        import time
        return time.time()
    
    def get_stats(self) -> Dict:
        """获取通信统计"""
        return {
            "protocol": self.protocol,
            "connected": self.is_connected,
            "commands_sent": self.commands_sent,
            "commands_failed": self.commands_failed,
            "success_rate": (self.commands_sent - self.commands_failed) / max(self.commands_sent, 1) * 100
        }


class MockCommander(Commander):
    """
    模拟命令下发器
    
    用于测试，不实际发送命令，只打印日志
    """
    
    def __init__(self):
        super().__init__(protocol="mock")
        self.is_connected = True
    
    def connect(self, **kwargs) -> bool:
        print("[模拟] 命令器已连接")
        return True
    
    def _send_command(self, robot: Robot, cmd: Dict) -> bool:
        print(f"[模拟] {robot.name} <- {cmd}")
        self.commands_sent += 1
        return True
