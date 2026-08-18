# 多机器人视觉控制系统文档

## 概述

基于第三视角单相机的地面多机器人定位与控制系统。

## 系统架构

```
相机(俯视) → 视觉检测 → 世界坐标映射 → 机器人管理 → 命令下发 → 机器人
```

## 快速开始

### 1. 硬件准备

#### 推荐配置: 树莓派4 + Camera Module 3 Wide

| 组件 | 规格 | 说明 |
|------|------|------|
| **主机** | 树莓派4 (4GB) | 作为主控制器 |
| **摄像头** | Camera Module 3 Wide | 120°广角，IMX708传感器 |
| **分辨率** | 1920×1080 | 工作分辨率（降低以提高帧率） |
| **安装** | 俯视 | 离地面2-3米 |

详细配置请参考 [raspberrypi_setup.md](raspberrypi_setup.md)

#### 通用配置

- **相机**: 安装在天花板或支架上，垂直向下拍摄
- **地面机器人**: 每个机器人贴有两个 AprilTag
  - 主标签: ID 0-99 (确定位置)
  - 辅助标签: ID 100-199 (确定朝向)
- **场地**: 平坦地面，光线均匀

### 2. 相机标定

```bash
cd tests

# 拍摄棋盘格图像
python test_3d_pose.py --capture-calibration

# 运行标定
python test_3d_pose.py --calibrate calibration_images/ -c camera.yaml
```

### 3. 配置机器人

编辑 `config/robots.json`:

```json
{
  "robots": [
    {
      "robot_id": 0,
      "name": "Robot-1",
      "tag_id": 0,
      "aux_tag_id": 100,
      "ip_address": "192.168.1.101",
      "port": 12345
    },
    {
      "robot_id": 1,
      "name": "Robot-2",
      "tag_id": 1,
      "aux_tag_id": 101,
      "ip_address": "192.168.1.102",
      "port": 12345
    }
  ],
  "world_mapper": {
    "camera_height": 2.0
  }
}
```

### 4. 启动系统

```bash
cd src

# 模拟模式（测试用）
python multi_robot_controller.py --mock

# 实际运行
python multi_robot_controller.py --camera 0 --camera-height 2.0
```

## 坐标系定义

### 世界坐标系

- **原点**: 相机正下方地面
- **X轴**: 指向相机右方
- **Y轴**: 指向相机前方（图像下方）
- **Z轴**: 向上

### 机器人朝向

- **0°**: 朝向X轴正方向
- **90°**: 朝向Y轴正方向
- **-90°**: 朝向Y轴负方向

## API 使用

### 基础用法

```python
from multi_robot import RobotManager, WorldMapper, Commander

# 初始化
world_mapper = WorldMapper(camera_height=2.0, camera_matrix=K)
manager = RobotManager(world_mapper)
commander = Commander(protocol="udp")
commander.connect()

# 注册机器人
manager.register_robot(
    robot_id=0,
    name="Robot-1",
    tag_id=0,
    aux_tag_id=100,
    ip_address="192.168.1.101",
    port=12345
)

# 主循环
while True:
    # 1. 获取图像
    frame = camera.read()
    
    # 2. 检测二维码
    detections = detector.detect(frame)
    
    # 3. 更新机器人位置
    detection_infos = [...]  # 转换为 DetectionInfo
    manager.update_from_detections(detection_infos)
    
    # 4. 发送控制命令
    for robot in manager.get_active_robots():
        commander.update_robot(robot)
```

### 发送目标点

```python
# 单个机器人
manager.send_goal(robot_id=0, target=(1.0, 2.0, 90.0))

# 批量发送
goals = {
    0: (1.0, 0.0, 0.0),
    1: (1.0, 1.0, 90.0),
    2: (0.0, 1.0, 180.0)
}
manager.send_goals(goals)
```

### 紧急停止

```python
# 停止单个机器人
manager.emergency_stop(robot_id=0)

# 停止所有机器人
manager.emergency_stop()
```

## 通信协议

### 命令格式 (JSON)

**速度控制**:
```json
{
  "type": "velocity",
  "robot_id": 0,
  "v": 0.5,
  "omega": 30.0,
  "timestamp": 1234567890.123
}
```

**位置控制**:
```json
{
  "type": "position",
  "robot_id": 0,
  "x": 1.0,
  "y": 2.0,
  "theta": 90.0,
  "timestamp": 1234567890.123
}
```

**停止**:
```json
{
  "type": "stop",
  "robot_id": 0,
  "timestamp": 1234567890.123
}
```

## 性能优化

### 提高检测精度

1. **相机标定**: 准确标定相机内参
2. **相机高度**: 精确测量相机离地面高度
3. **二维码尺寸**: 确保实际尺寸与代码中一致
4. **辅助标签**: 使用双标签确定朝向

### 提高帧率

1. **降低分辨率**: 适当降低相机分辨率
2. **减少检测区域**: 只检测感兴趣区域
3. **跳帧处理**: 每隔N帧处理一次

## 常见问题

### Q: 机器人位置跳动
**A**: 
- 检查相机是否固定牢固
- 增加卡尔曼滤波平滑轨迹
- 检查光照是否均匀

### Q: 朝向计算不准确
**A**:
- 确保辅助标签与主标签距离适当（10-20cm）
- 检查辅助标签ID是否正确（主标签+100）

### Q: 通信延迟高
**A**:
- 使用有线网络代替WiFi
- 优化控制周期（建议20-50Hz）
- 考虑使用ROS2进行通信

## 扩展开发

### 添加路径规划

```python
from multi_robot.path_planner import PathPlanner

planner = PathPlanner()
path = planner.plan(start, goal, obstacles)
```

### 添加避障

```python
# 检测机器人间距
for r1, r2 in combinations(manager.get_active_robots(), 2):
    if r1.current_pose.distance_to(r2.current_pose) < safety_distance:
        # 触发避障
        pass
```

### 集成ROS2

```python
import rclpy
from geometry_msgs.msg import Twist, PoseStamped

# 发布机器人位置
publisher = node.create_publisher(PoseStamped, '/robot_pose', 10)
```

## 参考

- [AprilTag 官方](https://april.eecs.umich.edu/software/apriltag)
- [OpenCV ArUco](https://docs.opencv.org/4.x/d5/dae/tutorial_aruco_detection.html)
