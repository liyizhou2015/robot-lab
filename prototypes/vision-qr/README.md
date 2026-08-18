# Vision QR - 第三视角单相机二维码视觉定位

利用单相机从第三视角（俯视/侧视）通过 AprilTag 二维码实现机器人/物体的视觉定位与3D位姿估计。

## 项目概述

### 目标
- 通过单相机实现亚厘米级定位精度
- 支持多二维码同时检测与跟踪
- 实时输出3D位姿（位置+姿态）信息

### 应用场景
- 机器人导航与定位
- AGV 路径跟踪
- 物体抓取位姿估计
- 多机器人协同定位

## 多机器人视觉控制系统 (新增)

### 项目目标
基于第三视角单相机，实现**地面多机器人的视觉定位与集中控制**。

### 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    第三视角相机 (俯视)                        │
│                      (USB/WebCam/IP)                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    视觉定位层 (Vision Layer)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ AprilTag     │  │ 多目标跟踪   │  │ 坐标转换     │       │
│  │ 检测器       │  │ (Multi-Obj)  │  │ (像素→世界)  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    机器人管理层 (Robot Manager)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ 机器人注册   │  │ 状态监控     │  │ 任务分配     │       │
│  │ (ID↔Robot)   │  │ (位置/姿态)  │  │ (目标点)     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    通信控制层 (Control Layer)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ 命令下发     │  │ 协议适配     │  │ 反馈接收     │       │
│  │ (目标位置)   │  │ (ROS/串口)   │  │ (里程计)     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │ Robot 1 │   │ Robot 2 │   │ Robot N │
   │(ID: 0)  │   │(ID: 1)  │   │(ID: N)  │
   └─────────┘   └─────────┘   └─────────┘
```

### 核心功能模块

| 模块 | 功能 | 状态 |
|------|------|------|
| **多目标检测** | 同时跟踪多个 AprilTag | ✅ 已有 |
| **世界坐标系** | 像素坐标 → 地面世界坐标 | 🔄 待开发 |
| **机器人注册** | ID 与机器人实例绑定 | 🔄 待开发 |
| **路径规划** | 多机器人路径生成与避障 | 🔄 待开发 |
| **通信协议** | 命令下发与状态反馈 | 🔄 待开发 |
| **可视化界面** | 实时地图显示与监控 | 🔄 待开发 |

### 机器人识别方案

每个机器人贴有不同 ID 的 AprilTag：
- Robot 1: ID 0 (主标签) + ID 100 (方向辅助)
- Robot 2: ID 1 (主标签) + ID 101 (方向辅助)
- Robot N: ID N (主标签) + ID 100+N (方向辅助)

通过双标签确定位置和朝向。

## 硬件需求

| 组件 | 规格 | 说明 |
|------|------|------|
| 相机 | USB/WebCam/IP | 建议 720p 以上，俯视安装 |
| 二维码 | AprilTag 36h11 | 每个机器人2个标签 |
| 地面机器人 | 轮式移动平台 | 带通信模块 |
| 计算平台 | PC/笔记本 | 实时处理 |

## 软件依赖

### 环境要求
- Python 3.8+
- OpenCV 4.10+ (推荐)
- NumPy

### 安装
```bash
# 创建conda环境（推荐）
conda create -n bot-lab python=3.13
conda activate bot-lab

# 安装依赖
pip install opencv-python opencv-contrib-python numpy pyyaml
```

## 快速开始

### 1. 生成二维码

```bash
cd tools
python generate_apriltag.py --id 0 --size 200
python generate_apriltag.py --sheet --range 0-5
```

### 2. 相机标定（必需）

```bash
# 拍摄棋盘格图像到 calibration_images/ 目录
# 然后运行标定
cd tests
python test_3d_pose.py --calibrate calibration_images/ -c camera.yaml
```

### 3. 多机器人视觉控制

```bash
# 启动多机器人控制系统
cd src
python multi_robot_controller.py --config config/camera.yaml
```

## 项目结构

```
vision-qr/
├── README.md                 # 本文件
├── requirements.txt          # 依赖列表
├── src/                      # 核心源码
│   ├── camera.py            # 相机接口
│   ├── detector.py          # AprilTag 检测器
│   ├── pose_estimator.py    # 3D位姿估计
│   ├── multi_robot/         # 多机器人控制 (新增)
│   │   ├── __init__.py
│   │   ├── robot.py         # 机器人实体类
│   │   ├── robot_manager.py # 机器人管理器
│   │   ├── world_mapper.py  # 世界坐标映射
│   │   ├── path_planner.py  # 路径规划
│   │   └── commander.py     # 命令下发
│   └── main.py              # 主程序
├── tools/                    # 工具脚本
│   └── generate_apriltag.py # 二维码生成器
├── tests/                    # 测试脚本
├── config/                   # 配置文件
└── docs/                     # 文档
    └── multi_robot.md       # 多机器人系统文档 (新增)
```

## 核心功能

### 1. AprilTag 检测
- 支持 AprilTag 36h11 字典（ID 0-586）
- 实时检测多二维码
- 子像素级角点定位

### 2. 3D位姿估计
- 基于 PnP 算法求解位姿
- 输出位置 (x, y, z) 和姿态（欧拉角）
- 支持相机标定参数

### 3. 相机标定
- 棋盘格标定法
- 自动计算内参和畸变系数
- 保存/加载标定文件

### 4. 多机器人管理 (新增)
- 机器人自动注册与识别
- 实时位置跟踪
- 目标点分配与路径规划
- 集中控制命令下发

### 5. 可视化
- 检测框和中心点标记
- 3D坐标轴显示（红X/绿Y/蓝Z）
- 实时地图显示多机器人位置

## 使用示例

### 基础检测
```python
from detector import AprilTagDetector
import cv2

detector = AprilTagDetector(marker_size=0.05)  # 5cm二维码
frame = cv2.imread('image.jpg')
detections = detector.detect(frame)

for det in detections:
    print(f"ID: {det.marker_id}, Center: {det.center}")
```

### 3D位姿估计
```python
from detector import AprilTagDetector
from pose_estimator import PoseEstimator
import numpy as np

detector = AprilTagDetector(marker_size=0.05)
pose_est = PoseEstimator(marker_size=0.05)

# 相机内参（示例值，实际应标定）
camera_matrix = np.array([[800, 0, 640],
                          [0, 800, 360],
                          [0, 0, 1]])

detections = detector.detect(frame)
for det in detections:
    pose = pose_est.estimate_pose(det.corners, camera_matrix)
    if pose:
        print(f"Position: {pose.position}")
        print(f"Euler angles: {pose.euler_angles}")
```

### 多机器人控制 (新增)
```python
from multi_robot import RobotManager, WorldMapper

# 初始化
manager = RobotManager(camera_matrix, dist_coeffs)
mapper = WorldMapper(camera_height=2.0)  # 相机高度2米

# 注册机器人
manager.register_robot(robot_id=0, name="Robot-1")
manager.register_robot(robot_id=1, name="Robot-2")

# 更新位置（从视觉检测）
for det in detections:
    world_pos = mapper.pixel_to_world(det.center)
    manager.update_position(det.marker_id, world_pos)

# 发送目标点
manager.send_goal(robot_id=0, target=(1.0, 2.0))
```

## 技术参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 二维码类型 | AprilTag 36h11 | 586个可用ID |
| 检测速度 | ~30 FPS | 取决于图像分辨率 |
| 定位精度 | ~1-5mm @ 1m | 取决于标定质量 |
| 支持距离 | 0.1m - 5m | 取决于二维码尺寸和相机分辨率 |
| 最大机器人数 | ~50 | 受ID数量限制 |

## 注意事项

1. **相机标定**: 未标定的相机使用默认参数，3D定位精度会降低
2. **二维码尺寸**: 实际打印尺寸需与代码中 `marker_size` 参数一致
3. **光照条件**: 避免过强反光或阴影，保持均匀照明
4. **角度限制**: 二维码平面与相机光轴夹角建议 < 45°
5. **遮挡处理**: 多机器人运行时注意避免标签相互遮挡

## 待完善功能

### 基础功能
- [x] AprilTag 检测
- [x] 3D位姿估计
- [x] 相机标定

### 多机器人系统
- [ ] 世界坐标系映射
- [ ] 机器人注册管理
- [ ] 多目标跟踪
- [ ] 路径规划与避障
- [ ] 通信协议实现
- [ ] 可视化监控界面
- [ ] 多相机融合

### 扩展功能
- [ ] 二维码地图构建与SLAM
- [ ] 实时跟踪滤波（卡尔曼滤波）
- [ ] ROS2 接口封装
- [ ] Web 远程监控

## 参考资料

- [OpenCV ArUco 文档](https://docs.opencv.org/4.x/d5/dae/tutorial_aruco_detection.html)
- [AprilTag 官方](https://april.eecs.umich.edu/software/apriltag)
- [AprilTag 图像库](https://github.com/AprilRobotics/apriltag-imgs)
- [多机器人系统综述](https://en.wikipedia.org/wiki/Multi-agent_system)

---

**创建日期**: 2026-04-27  
**最后更新**: 2026-08-18 (添加多机器人视觉控制系统)
