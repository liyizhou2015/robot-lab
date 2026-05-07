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

## 硬件需求

| 组件 | 规格 | 说明 |
|------|------|------|
| 相机 | USB/WebCam | 建议 720p 以上 |
| 二维码 | AprilTag 36h11 | 打印或屏幕显示 |
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

### 2. 测试检测（使用视频文件）

```bash
cd tests

# 命令行输出检测结果
python test_3d_pose.py VID_20260427_172500.mp4

# 保存可视化结果
python test_3d_pose.py VID_20260427_172500.mp4 --save-vis -n 10

# 或保存对比图像
python save_visualization.py VID_20260427_172500.mp4 -n 10
```

### 3. 相机标定（提高精度）

```bash
# 拍摄棋盘格图像（9x6内角点）到 calibration_images/ 目录
# 然后运行标定
python test_3d_pose.py --calibrate calibration_images/ -c camera.yaml

# 使用标定参数进行3D定位
python test_3d_pose.py VID_20260427_172500.mp4 -c camera.yaml --save-vis
```

## 项目结构

```
vision-qr/
├── README.md                 # 本文件
├── requirements.txt          # 依赖列表
├── src/                      # 核心源码
│   ├── camera.py            # 相机接口（USB/视频文件）
│   ├── detector.py          # AprilTag 检测器
│   └── pose_estimator.py    # 3D位姿估计与相机标定
├── tools/                    # 工具脚本
│   └── generate_apriltag.py # 二维码生成器
├── tests/                    # 测试脚本
│   ├── test_3d_pose.py      # 3D位姿估计测试
│   ├── test_detection_offline.py  # 离线检测测试
│   ├── save_visualization.py      # 保存可视化结果
│   └── create_test_frames.py      # 生成测试图像
├── config/                   # 配置文件（相机标定参数）
└── docs/                     # 文档
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

### 4. 可视化
- 检测框和中心点标记
- 3D坐标轴显示（红X/绿Y/蓝Z）
- 位置/距离信息叠加

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

## 技术参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 二维码类型 | AprilTag 36h11 | 586个可用ID |
| 检测速度 | ~30 FPS | 取决于图像分辨率 |
| 定位精度 | ~1-5mm @ 1m | 取决于标定质量 |
| 支持距离 | 0.1m - 5m | 取决于二维码尺寸和相机分辨率 |

## 注意事项

1. **相机标定**: 未标定的相机使用默认参数，3D定位精度会降低
2. **二维码尺寸**: 实际打印尺寸需与代码中 `marker_size` 参数一致
3. **光照条件**: 避免过强反光或阴影，保持均匀照明
4. **角度限制**: 二维码平面与相机光轴夹角建议 < 45°

## 待完善功能

- [ ] 多相机标定与融合
- [ ] 二维码地图构建与SLAM
- [ ] 实时跟踪滤波（卡尔曼滤波）
- [ ] ROS2 接口封装
- [ ] 与机械臂控制集成

## 参考资料

- [OpenCV ArUco 文档](https://docs.opencv.org/4.x/d5/dae/tutorial_aruco_detection.html)
- [AprilTag 官方](https://april.eecs.umich.edu/software/apriltag)
- [AprilTag 图像库](https://github.com/AprilRobotics/apriltag-imgs)

---

**创建日期**: 2026-04-27  
**最后更新**: 2026-04-27
