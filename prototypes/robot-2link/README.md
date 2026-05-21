# 2连杆机器人控制

一个完整的2连杆机器人臂控制系统，包含运动学和动力学仿真。

## 功能特性

### 运动学
- ✅ 正运动学 (Forward Kinematics)
- ✅ 逆运动学 (Inverse Kinematics) - 几何法
- ✅ 雅可比矩阵计算
- ✅ 工作空间分析

### 控制算法
- ✅ 关节空间PID控制
- ✅ 任务空间控制 (雅可比转置法)
- ✅ 笛卡尔速度控制
- ✅ 轨迹跟踪

### 动力学
- ✅ 2R机器人动力学模型
- ✅ 质量矩阵、科氏力、重力项
- ✅ 实时仿真

### 可视化
- ✅ 静态姿态显示
- ✅ 轨迹动画
- ✅ 工作空间可视化

## 文件结构

```
robot-2link/
├── robot_arm.py      # 核心运动学和可视化
├── controller.py     # 控制器和动力学仿真
└── README.md         # 本文件
```

## 快速开始

### 1. 运行运动学演示

```bash
python3 robot_arm.py
```

输出示例：
```
==================================================
正运动学演示
==================================================

关节角度: q1=0.0°, q2=0.0°
  中间关节: (1.000, 0.000)
  末端位置: (2.000, 0.000)

关节角度: q1=45.0°, q2=45.0°
  中间关节: (0.707, 0.707)
  末端位置: (0.259, 1.707)
...
```

### 2. 运行控制演示

```bash
python3 controller.py
```

输出示例：
```
==================================================
关节空间PID控制演示
==================================================
目标角度: q1=60.0°, q2=45.0°

仿真中...
  t=0.0s: q1=0.00°, q2=0.00°
  t=1.0s: q1=23.45°, q2=17.82°
  ...
```

## API 使用示例

### 基本运动学

```python
from robot_arm import Robot2Link, RobotConfig

# 创建机器人 (默认连杆长度=1.0)
robot = Robot2Link()

# 设置关节角度 (弧度)
robot.set_joint_angles(np.pi/4, np.pi/4)

# 正运动学
joint1_pos, end_pos = robot.forward_kinematics()
print(f"末端位置: {end_pos}")

# 逆运动学
result = robot.inverse_kinematics(1.5, 0.5)
if result:
    q1, q2 = result
    print(f"关节角度: q1={q1}, q2={q2}")
```

### 控制器

```python
from robot_arm import Robot2Link
from controller import RobotController, Simulation

robot = Robot2Link()
controller = RobotController(robot, dt=0.01)
sim = Simulation(robot, controller)

# 关节空间控制
for _ in range(100):
    tau1, tau2 = controller.joint_space_control(q1_target, q2_target)
    sim.step(tau1, tau2)

# 任务空间控制
for _ in range(100):
    tau1, tau2 = controller.task_space_control(x_target, y_target)
    sim.step(tau1, tau2)
```

### 轨迹规划

```python
from robot_arm import TrajectoryPlanner

planner = TrajectoryPlanner()

# 圆形轨迹
trajectory = planner.circular_trajectory(
    center=np.array([1.0, 0.5]), 
    radius=0.5, 
    num_points=100
)

# 线性插值
start = np.array([1.0, 0.0])
end = np.array([0.5, 1.0])
traj = planner.linear_interpolation(start, end, num_points=50)
```

### 可视化

```python
from robot_arm import visualize_robot, animate_trajectory

# 静态显示
visualize_robot(robot, target=[1.5, 0.5], save_path="pose.png")

# 动画
anim = animate_trajectory(robot, trajectory)
anim.save('animation.gif', writer='pillow', fps=20)
```

## 参数配置

```python
from robot_arm import RobotConfig

config = RobotConfig(
    L1=1.5,        # 连杆1长度
    L2=1.0,        # 连杆2长度
    q1_min=-np.pi, # 关节1最小角度
    q1_max=np.pi,  # 关节1最大角度
    q2_min=-np.pi/2, # 关节2最小角度
    q2_max=np.pi/2   # 关节2最大角度
)

robot = Robot2Link(config)
```

## 数学原理

### 正运动学

```
x₁ = L₁·cos(q₁)
y₁ = L₁·sin(q₁)

x₂ = x₁ + L₂·cos(q₁+q₂)
y₂ = y₁ + L₂·sin(q₁+q₂)
```

### 逆运动学 (几何法)

```
cos(q₂) = (x² + y² - L₁² - L₂²) / (2·L₁·L₂)
q₂ = ±arccos(cos(q₂))  # 肘部向上/向下

q₁ = atan2(y, x) - atan2(L₂·sin(q₂), L₁ + L₂·cos(q₂))
```

### 雅可比矩阵

```
J = [-L₁·sin(q₁) - L₂·sin(q₁+q₂),  -L₂·sin(q₁+q₂)]
    [ L₁·cos(q₁) + L₂·cos(q₁+q₂),   L₂·cos(q₁+q₂)]
```

## 扩展建议

1. **添加更多轨迹类型**: 贝塞尔曲线、样条曲线
2. **障碍物避障**: 实现势场法或RRT算法
3. **力控制**: 添加导纳/阻抗控制
4. **3D扩展**: 扩展到3连杆或6自由度
5. **ROS集成**: 与ROS/ROS2对接

## 依赖

```
numpy
matplotlib
```

安装：
```bash
pip install numpy matplotlib
```
