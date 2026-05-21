"""
2连杆机器人控制器
包含PID控制、速度控制和力控制
"""
import numpy as np
from robot_arm import Robot2Link, RobotConfig
from typing import Callable, Optional


class PIDController:
    """PID控制器"""
    
    def __init__(self, Kp: float, Ki: float, Kd: float, 
                 dt: float = 0.01, output_limit: Optional[tuple] = None):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.dt = dt
        self.output_limit = output_limit
        
        self.integral = 0.0
        self.prev_error = 0.0
        
    def reset(self):
        """重置控制器状态"""
        self.integral = 0.0
        self.prev_error = 0.0
        
    def compute(self, setpoint: float, measurement: float) -> float:
        """计算控制输出"""
        error = setpoint - measurement
        
        # 比例项
        P = self.Kp * error
        
        # 积分项
        self.integral += error * self.dt
        self.integral = np.clip(self.integral, -10, 10)  # 抗积分饱和
        I = self.Ki * self.integral
        
        # 微分项
        derivative = (error - self.prev_error) / self.dt
        D = self.Kd * derivative
        self.prev_error = error
        
        output = P + I + D
        
        # 输出限制
        if self.output_limit:
            output = np.clip(output, self.output_limit[0], self.output_limit[1])
            
        return output


class RobotController:
    """机器人关节空间控制器"""
    
    def __init__(self, robot: Robot2Link, dt: float = 0.01):
        self.robot = robot
        self.dt = dt
        
        # 为每个关节创建PID控制器
        self.pid_q1 = PIDController(Kp=10.0, Ki=0.1, Kd=1.0, dt=dt, 
                                     output_limit=(-5, 5))
        self.pid_q2 = PIDController(Kp=10.0, Ki=0.1, Kd=1.0, dt=dt,
                                     output_limit=(-5, 5))
        
    def joint_space_control(self, q1_target: float, q2_target: float) -> tuple:
        """
        关节空间位置控制
        返回: (tau1, tau2) 关节力矩
        """
        tau1 = self.pid_q1.compute(q1_target, self.robot.q1)
        tau2 = self.pid_q2.compute(q2_target, self.robot.q2)
        return tau1, tau2
    
    def task_space_control(self, x_target: float, y_target: float) -> tuple:
        """
        任务空间位置控制 (使用雅可比转置)
        返回: (tau1, tau2) 关节力矩
        """
        # 当前末端位置
        _, current_pos = self.robot.forward_kinematics()
        
        # 位置误差
        error = np.array([x_target - current_pos[0], 
                         y_target - current_pos[1]])
        
        # 计算雅可比
        J = self.robot.jacobian()
        
        # 雅可比转置控制: tau = J^T * F
        # 其中 F 是笛卡尔空间的力 (这里用P控制)
        Kp_cartesian = np.array([[10, 0], [0, 10]])
        F = Kp_cartesian @ error
        
        tau = J.T @ F
        return tau[0], tau[1]
    
    def velocity_control(self, vx: float, vy: float) -> tuple:
        """
        笛卡尔速度控制
        输入: 期望末端速度 (vx, vy)
        返回: (dq1, dq2) 关节速度
        """
        J = self.robot.jacobian()
        
        # 使用伪逆计算关节速度: dq = J^+ * v
        v_desired = np.array([vx, vy])
        
        # 阻尼最小二乘伪逆
        damping = 0.01
        J_pinv = J.T @ np.linalg.inv(J @ J.T + damping * np.eye(2))
        
        dq = J_pinv @ v_desired
        return dq[0], dq[1]
    
    def reset(self):
        """重置所有控制器"""
        self.pid_q1.reset()
        self.pid_q2.reset()


class Simulation:
    """机器人动力学仿真"""
    
    def __init__(self, robot: Robot2Link, controller: RobotController,
                 m1: float = 1.0, m2: float = 1.0, 
                 I1: float = 0.1, I2: float = 0.1):
        """
        参数:
            m1, m2: 连杆质量
            I1, I2: 连杆转动惯量
        """
        self.robot = robot
        self.controller = controller
        
        # 动力学参数
        self.m1, self.m2 = m1, m2
        self.I1, self.I2 = I1, I2
        
        # 状态变量
        self.dq1, self.dq2 = 0.0, 0.0  # 关节速度
        self.ddq1, self.ddq2 = 0.0, 0.0  # 关节加速度
        
    def compute_dynamics(self, tau1: float, tau2: float) -> tuple:
        """
        计算关节加速度 (简化动力学模型)
        M(q) * ddq + C(q, dq) * dq + G(q) = tau
        """
        q1, q2 = self.robot.q1, self.robot.q2
        dq1, dq2 = self.dq1, self.dq2
        
        L1, L2 = self.robot.config.L1, self.robot.config.L2
        m1, m2 = self.m1, self.m2
        
        # 质量矩阵 M(q)
        M11 = self.I1 + self.I2 + m1*(L1/2)**2 + m2*(L1**2 + (L2/2)**2 + L1*L2*np.cos(q2))
        M12 = self.I2 + m2*((L2/2)**2 + L1*L2/2*np.cos(q2))
        M22 = self.I2 + m2*(L2/2)**2
        
        M = np.array([[M11, M12], [M12, M22]])
        
        # 科氏力和离心力 C(q, dq)
        h = -m2 * L1 * L2/2 * np.sin(q2)
        C = np.array([[h * dq2, h * (dq1 + dq2)],
                      [-h * dq1, 0]])
        
        # 重力项 G(q)
        g = 9.81
        G1 = (m1*L1/2 + m2*L1) * g * np.cos(q1) + m2*L2/2 * g * np.cos(q1 + q2)
        G2 = m2 * L2/2 * g * np.cos(q1 + q2)
        G = np.array([G1, G2])
        
        # 计算加速度
        tau = np.array([tau1, tau2])
        ddq = np.linalg.inv(M) @ (tau - C @ np.array([dq1, dq2]) - G)
        
        return ddq[0], ddq[1]
    
    def step(self, tau1: float, tau2: float):
        """仿真一步"""
        # 计算加速度
        self.ddq1, self.ddq2 = self.compute_dynamics(tau1, tau2)
        
        # 数值积分 (欧拉法)
        dt = self.controller.dt
        self.dq1 += self.ddq1 * dt
        self.dq2 += self.ddq2 * dt
        
        # 速度阻尼
        self.dq1 *= 0.99
        self.dq2 *= 0.99
        
        # 更新位置
        new_q1 = self.robot.q1 + self.dq1 * dt
        new_q2 = self.robot.q2 + self.dq2 * dt
        
        # 检查关节限制
        cfg = self.robot.config
        new_q1 = np.clip(new_q1, cfg.q1_min, cfg.q1_max)
        new_q2 = np.clip(new_q2, cfg.q2_min, cfg.q2_max)
        
        self.robot.set_joint_angles(new_q1, new_q2)
        
    def get_state(self) -> dict:
        """获取当前状态"""
        _, end_pos = self.robot.forward_kinematics()
        return {
            'q1': self.robot.q1,
            'q2': self.robot.q2,
            'dq1': self.dq1,
            'dq2': self.dq2,
            'x': end_pos[0],
            'y': end_pos[1]
        }


def demo_joint_control():
    """关节空间控制演示"""
    print("=" * 50)
    print("关节空间PID控制演示")
    print("=" * 50)
    
    robot = Robot2Link()
    controller = RobotController(robot, dt=0.01)
    sim = Simulation(robot, controller)
    
    # 目标关节角度
    q1_target, q2_target = np.pi/3, np.pi/4
    
    print(f"目标角度: q1={np.degrees(q1_target):.1f}°, q2={np.degrees(q2_target):.1f}°")
    print("\n仿真中...")
    
    history = []
    for i in range(500):
        tau1, tau2 = controller.joint_space_control(q1_target, q2_target)
        sim.step(tau1, tau2)
        
        state = sim.get_state()
        history.append(state)
        
        if i % 100 == 0:
            print(f"  t={i*0.01:.1f}s: q1={np.degrees(state['q1']):.2f}°, "
                  f"q2={np.degrees(state['q2']):.2f}°")
    
    print("\n控制完成!")
    final = history[-1]
    print(f"最终位置: q1={np.degrees(final['q1']):.2f}°, q2={np.degrees(final['q2']):.2f}°")
    print(f"末端位置: ({final['x']:.3f}, {final['y']:.3f})")
    
    return history


def demo_task_space_control():
    """任务空间控制演示"""
    print("\n" + "=" * 50)
    print("任务空间控制演示")
    print("=" * 50)
    
    robot = Robot2Link()
    controller = RobotController(robot, dt=0.01)
    sim = Simulation(robot, controller)
    
    # 初始位置
    robot.set_joint_angles(0, 0)
    
    # 目标末端位置
    x_target, y_target = 1.2, 0.8
    print(f"目标末端位置: ({x_target}, {y_target})")
    
    # 先计算逆运动学得到目标关节角
    result = robot.inverse_kinematics(x_target, y_target)
    if result:
        print(f"目标关节角: q1={np.degrees(result[0]):.2f}°, q2={np.degrees(result[1]):.2f}°")
    
    print("\n仿真中...")
    history = []
    for i in range(500):
        tau1, tau2 = controller.task_space_control(x_target, y_target)
        sim.step(tau1, tau2)
        
        state = sim.get_state()
        history.append(state)
        
        if i % 100 == 0:
            print(f"  t={i*0.01:.1f}s: ({state['x']:.3f}, {state['y']:.3f})")
    
    print("\n控制完成!")
    final = history[-1]
    print(f"最终末端位置: ({final['x']:.4f}, {final['y']:.4f})")
    print(f"误差: ({abs(final['x']-x_target):.4f}, {abs(final['y']-y_target):.4f})")
    
    return history


def demo_trajectory_tracking():
    """轨迹跟踪演示"""
    print("\n" + "=" * 50)
    print("轨迹跟踪控制演示")
    print("=" * 50)
    
    robot = Robot2Link()
    controller = RobotController(robot, dt=0.01)
    sim = Simulation(robot, controller)
    
    # 生成轨迹点
    t = np.linspace(0, 2*np.pi, 200)
    x_traj = 1.0 + 0.5 * np.cos(t)
    y_traj = 0.5 + 0.3 * np.sin(t)
    
    print("圆形轨迹跟踪")
    print(f"轨迹点数: {len(t)}")
    
    history = []
    for i in range(len(t)):
        tau1, tau2 = controller.task_space_control(x_traj[i], y_traj[i])
        sim.step(tau1, tau2)
        
        state = sim.get_state()
        history.append(state)
    
    # 计算跟踪误差
    errors = []
    for i, state in enumerate(history):
        err = np.sqrt((state['x'] - x_traj[i])**2 + (state['y'] - y_traj[i])**2)
        errors.append(err)
    
    print(f"平均跟踪误差: {np.mean(errors):.4f} m")
    print(f"最大跟踪误差: {np.max(errors):.4f} m")
    
    return history, x_traj, y_traj


if __name__ == "__main__":
    # 运行演示
    demo_joint_control()
    demo_task_space_control()
    demo_trajectory_tracking()
