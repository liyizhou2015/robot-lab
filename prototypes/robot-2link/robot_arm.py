"""
2连杆机器人臂控制
包含正运动学、逆运动学和轨迹规划
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class RobotConfig:
    """机器人配置参数"""
    L1: float = 1.0  # 连杆1长度
    L2: float = 1.0  # 连杆2长度
    q1_min: float = -np.pi  # 关节1角度限制
    q1_max: float = np.pi
    q2_min: float = -np.pi  # 关节2角度限制
    q2_max: float = np.pi


class Robot2Link:
    """2连杆机器人臂类"""
    
    def __init__(self, config: Optional[RobotConfig] = None):
        self.config = config or RobotConfig()
        self.q1 = 0.0  # 关节1角度
        self.q2 = 0.0  # 关节2角度
        
    def forward_kinematics(self, q1: Optional[float] = None, 
                           q2: Optional[float] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        正运动学计算
        输入: 关节角度 (弧度)
        输出: 末端执行器位置 (x, y) 和中间关节位置
        """
        q1 = q1 if q1 is not None else self.q1
        q2 = q2 if q2 is not None else self.q2
        
        L1, L2 = self.config.L1, self.config.L2
        
        # 中间关节位置
        x1 = L1 * np.cos(q1)
        y1 = L1 * np.sin(q1)
        
        # 末端执行器位置
        x2 = x1 + L2 * np.cos(q1 + q2)
        y2 = y1 + L2 * np.sin(q1 + q2)
        
        return np.array([x1, y1]), np.array([x2, y2])
    
    def inverse_kinematics(self, x: float, y: float, 
                          elbow_up: bool = True) -> Optional[Tuple[float, float]]:
        """
        逆运动学计算 (几何法)
        输入: 目标位置 (x, y)
        输出: 关节角度 (q1, q2)
        """
        L1, L2 = self.config.L1, self.config.L2
        
        # 检查可达性
        r = np.sqrt(x**2 + y**2)
        if r > L1 + L2 or r < abs(L1 - L2):
            return None  # 目标不可达
        
        # 计算 q2 (肘关节角度)
        cos_q2 = (x**2 + y**2 - L1**2 - L2**2) / (2 * L1 * L2)
        cos_q2 = np.clip(cos_q2, -1, 1)  # 数值稳定性
        
        if elbow_up:
            q2 = np.arccos(cos_q2)
        else:
            q2 = -np.arccos(cos_q2)
        
        # 计算 q1 (肩关节角度)
        k1 = L1 + L2 * np.cos(q2)
        k2 = L2 * np.sin(q2)
        
        q1 = np.arctan2(y, x) - np.arctan2(k2, k1)
        
        # 检查关节限制
        if not (self.config.q1_min <= q1 <= self.config.q1_max and
                self.config.q2_min <= q2 <= self.config.q2_max):
            return None
            
        return q1, q2
    
    def jacobian(self, q1: Optional[float] = None, 
                 q2: Optional[float] = None) -> np.ndarray:
        """
        计算雅可比矩阵
        J = [dx/dq1, dx/dq2]
            [dy/dq1, dy/dq2]
        """
        q1 = q1 if q1 is not None else self.q1
        q2 = q2 if q2 is not None else self.q2
        
        L1, L2 = self.config.L1, self.config.L2
        
        J = np.array([
            [-L1*np.sin(q1) - L2*np.sin(q1+q2), -L2*np.sin(q1+q2)],
            [ L1*np.cos(q1) + L2*np.cos(q1+q2),  L2*np.cos(q1+q2)]
        ])
        
        return J
    
    def set_joint_angles(self, q1: float, q2: float):
        """设置关节角度"""
        self.q1 = q1
        self.q2 = q2
    
    def get_joint_positions(self) -> Tuple[np.ndarray, np.ndarray]:
        """获取关节位置"""
        return self.forward_kinematics()


class TrajectoryPlanner:
    """轨迹规划器"""
    
    @staticmethod
    def linear_interpolation(start: np.ndarray, end: np.ndarray, 
                            num_points: int = 100) -> np.ndarray:
        """线性插值轨迹"""
        t = np.linspace(0, 1, num_points)
        return start[:, np.newaxis] * (1 - t) + end[:, np.newaxis] * t
    
    @staticmethod
    def cubic_polynomial(start: float, end: float, 
                        duration: float, dt: float = 0.01) -> np.ndarray:
        """三次多项式轨迹规划"""
        t = np.arange(0, duration, dt)
        T = duration
        
        # 边界条件: 起始/终止位置和速度都为0
        a0 = start
        a1 = 0
        a2 = 3 * (end - start) / T**2
        a3 = -2 * (end - start) / T**3
        
        return a0 + a1*t + a2*t**2 + a3*t**3
    
    @staticmethod
    def circular_trajectory(center: np.ndarray, radius: float, 
                           num_points: int = 100) -> np.ndarray:
        """圆形轨迹"""
        theta = np.linspace(0, 2*np.pi, num_points)
        x = center[0] + radius * np.cos(theta)
        y = center[1] + radius * np.sin(theta)
        return np.vstack([x, y])


def visualize_robot(robot: Robot2Link, target: Optional[np.ndarray] = None,
                   trajectory: Optional[np.ndarray] = None,
                   save_path: Optional[str] = None):
    """可视化机器人"""
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # 设置坐标轴
    max_reach = robot.config.L1 + robot.config.L2
    ax.set_xlim(-max_reach - 0.5, max_reach + 0.5)
    ax.set_ylim(-max_reach - 0.5, max_reach + 0.5)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='k', linewidth=0.5)
    ax.axvline(x=0, color='k', linewidth=0.5)
    
    # 绘制工作空间
    theta = np.linspace(0, 2*np.pi, 100)
    ax.plot(max_reach * np.cos(theta), max_reach * np.sin(theta), 
            'g--', alpha=0.3, label='Workspace')
    
    # 获取当前关节位置
    joint1, end_effector = robot.get_joint_positions()
    
    # 绘制连杆
    ax.plot([0, joint1[0]], [0, joint1[1]], 'b-', linewidth=4, label='Link 1')
    ax.plot([joint1[0], end_effector[0]], [joint1[1], end_effector[1]], 
            'b-', linewidth=4, label='Link 2')
    
    # 绘制关节
    ax.plot(0, 0, 'ko', markersize=10, label='Base')
    ax.plot(joint1[0], joint1[1], 'go', markersize=8, label='Joint 1')
    ax.plot(end_effector[0], end_effector[1], 'ro', markersize=8, label='End Effector')
    
    # 绘制目标点
    if target is not None:
        ax.plot(target[0], target[1], 'm*', markersize=15, label='Target')
    
    # 绘制轨迹
    if trajectory is not None:
        ax.plot(trajectory[0, :], trajectory[1, :], 'r--', alpha=0.5, label='Trajectory')
    
    ax.legend(loc='upper right')
    ax.set_title(f'2-Link Robot Arm\nq1={np.degrees(robot.q1):.1f}°, q2={np.degrees(robot.q2):.1f}°')
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved to {save_path}")
    
    return fig, ax


def animate_trajectory(robot: Robot2Link, trajectory: np.ndarray, 
                      interval: int = 50):
    """动画演示轨迹跟踪"""
    fig, ax = plt.subplots(figsize=(8, 8))
    
    max_reach = robot.config.L1 + robot.config.L2
    ax.set_xlim(-max_reach - 0.5, max_reach + 0.5)
    ax.set_ylim(-max_reach - 0.5, max_reach + 0.5)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    
    # 初始化绘图元素
    line1, = ax.plot([], [], 'b-', linewidth=4)
    line2, = ax.plot([], [], 'b-', linewidth=4)
    joint_dot, = ax.plot([], [], 'go', markersize=8)
    end_dot, = ax.plot([], [], 'ro', markersize=8)
    path_line, = ax.plot([], [], 'r--', alpha=0.5)
    
    ax.plot(0, 0, 'ko', markersize=10)
    ax.plot(trajectory[0, :], trajectory[1, :], 'g--', alpha=0.2)
    
    def init():
        line1.set_data([], [])
        line2.set_data([], [])
        joint_dot.set_data([], [])
        end_dot.set_data([], [])
        path_line.set_data([], [])
        return line1, line2, joint_dot, end_dot, path_line
    
    path_x, path_y = [], []
    
    def update(frame):
        target = trajectory[:, frame]
        result = robot.inverse_kinematics(target[0], target[1])
        
        if result:
            q1, q2 = result
            robot.set_joint_angles(q1, q2)
            joint1, end = robot.get_joint_positions()
            
            line1.set_data([0, joint1[0]], [0, joint1[1]])
            line2.set_data([joint1[0], end[0]], [joint1[1], end[1]])
            joint_dot.set_data([joint1[0]], [joint1[1]])
            end_dot.set_data([end[0]], [end[1]])
            
            path_x.append(end[0])
            path_y.append(end[1])
            path_line.set_data(path_x, path_y)
        
        return line1, line2, joint_dot, end_dot, path_line
    
    anim = FuncAnimation(fig, update, frames=trajectory.shape[1],
                        init_func=init, blit=True, interval=interval)
    
    ax.set_title('2-Link Robot Trajectory Tracking')
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    
    plt.tight_layout()
    return anim


# ============== 演示和测试 ==============

def demo_forward_kinematics():
    """正运动学演示"""
    print("=" * 50)
    print("正运动学演示")
    print("=" * 50)
    
    robot = Robot2Link()
    
    test_angles = [
        (0, 0),
        (np.pi/4, np.pi/4),
        (np.pi/2, 0),
        (np.pi/2, np.pi/2),
        (np.pi/4, -np.pi/2),
    ]
    
    for q1, q2 in test_angles:
        robot.set_joint_angles(q1, q2)
        joint1, end = robot.forward_kinematics()
        print(f"\n关节角度: q1={np.degrees(q1):.1f}°, q2={np.degrees(q2):.1f}°")
        print(f"  中间关节: ({joint1[0]:.3f}, {joint1[1]:.3f})")
        print(f"  末端位置: ({end[0]:.3f}, {end[1]:.3f})")


def demo_inverse_kinematics():
    """逆运动学演示"""
    print("\n" + "=" * 50)
    print("逆运动学演示")
    print("=" * 50)
    
    robot = Robot2Link()
    
    test_positions = [
        (1.5, 0.5),
        (1.0, 1.0),
        (0, 1.5),
        (-1.0, 0.5),
        (2.0, 0),  # 边界
        (2.5, 0),  # 不可达
    ]
    
    for x, y in test_positions:
        result = robot.inverse_kinematics(x, y)
        print(f"\n目标位置: ({x}, {y})")
        if result:
            q1, q2 = result
            # 验证
            robot.set_joint_angles(q1, q2)
            _, end = robot.forward_kinematics()
            print(f"  解: q1={np.degrees(q1):.2f}°, q2={np.degrees(q2):.2f}°")
            print(f"  验证: ({end[0]:.4f}, {end[1]:.4f})")
        else:
            print("  不可达!")


def demo_trajectory():
    """轨迹规划演示"""
    print("\n" + "=" * 50)
    print("轨迹规划演示")
    print("=" * 50)
    
    robot = Robot2Link()
    planner = TrajectoryPlanner()
    
    # 圆形轨迹
    center = np.array([1.0, 0.5])
    radius = 0.5
    trajectory = planner.circular_trajectory(center, radius, num_points=50)
    
    print(f"圆形轨迹: 中心({center[0]}, {center[1]}), 半径{radius}")
    print(f"轨迹点数: {trajectory.shape[1]}")
    
    # 计算逆运动学
    joint_angles = []
    for i in range(trajectory.shape[1]):
        result = robot.inverse_kinematics(trajectory[0, i], trajectory[1, i])
        if result:
            joint_angles.append(result)
    
    print(f"成功计算逆运动学的点数: {len(joint_angles)}")
    
    return robot, trajectory


if __name__ == "__main__":
    # 运行演示
    demo_forward_kinematics()
    demo_inverse_kinematics()
    robot, trajectory = demo_trajectory()
    
    # 可视化
    print("\n生成可视化...")
    robot.set_joint_angles(np.pi/4, np.pi/4)
    visualize_robot(robot, save_path="robot_pose.png")
    
    # 动画
    print("生成轨迹动画...")
    anim = animate_trajectory(robot, trajectory)
    anim.save('trajectory.gif', writer='pillow', fps=20)
    print("已保存 trajectory.gif")
    
    plt.show()
