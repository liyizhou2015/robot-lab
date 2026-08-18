# robot-lab - 机器人快速实验平台

利用各种开放软件，快速实现机器人原型的实验项目。

## 项目目标

- 快速验证机器人概念和设计
- 整合开源软硬件资源
- 降低机器人开发门槛
- 积累可复用的原型方案

## 原型项目

| 项目 | 描述 | 状态 |
|------|------|------|
| **robot-2link** | 2连杆机器人臂控制（运动学、动力学、PID控制） | ✅ 完成 |
| **vision-qr** | 第三视角单相机AprilTag二维码定位 | ✅ 完成 |
| **vision-qr/multi-robot** | 多机器人视觉控制系统 | 🔄 开发中 |

## 原型项目详情

### 1. robot-2link - 2连杆机器人臂控制

完整的2连杆机器人臂控制系统，包含运动学和动力学仿真。

**功能**:
- 正/逆运动学
- 雅可比矩阵计算
- 关节空间PID控制
- 任务空间控制
- 动力学仿真
- 可视化与轨迹动画

**位置**: `prototypes/robot-2link/`

### 2. vision-qr - 二维码视觉定位

基于第三视角单相机的 AprilTag 二维码视觉定位与3D位姿估计。

**功能**:
- AprilTag 36h11 检测
- 3D位姿估计（PnP算法）
- 相机标定
- 亚厘米级定位精度

**位置**: `prototypes/vision-qr/`

### 3. multi-robot - 多机器人视觉控制系统 (新增)

基于第三视角单相机的**地面多机器人定位与集中控制**。

**系统架构**:
```
相机(俯视) → 视觉检测 → 世界坐标映射 → 机器人管理 → 命令下发 → 机器人
```

**核心功能**:
- 多机器人实时定位（AprilTag双标签方案）
- 世界坐标系映射
- 机器人注册与状态管理
- 目标点分配与路径跟踪
- 命令下发（UDP/TCP/ROS）
- 可视化监控界面

**技术参数**:
- 最大机器人数: ~50（受ID数量限制）
- 定位精度: ~1-5mm @ 1m
- 检测帧率: ~30 FPS

**位置**: `prototypes/vision-qr/src/multi_robot/`

**使用**:
```bash
cd prototypes/vision-qr/src
python multi_robot_controller.py --mock  # 模拟模式
```

**文档**: `prototypes/vision-qr/docs/multi_robot.md`

## 目录结构

```
robot-lab/
├── README.md                    # 本文件
├── prototypes/                  # 原型项目
│   ├── robot-2link/            # 2连杆机器人控制
│   └── vision-qr/              # 视觉定位与多机器人控制
│       ├── src/
│       │   ├── detector.py     # AprilTag检测
│       │   ├── pose_estimator.py # 位姿估计
│       │   ├── multi_robot/    # 多机器人控制（新增）
│       │   │   ├── robot.py
│       │   │   ├── robot_manager.py
│       │   │   ├── world_mapper.py
│       │   │   └── commander.py
│       │   └── multi_robot_controller.py
│       ├── tests/              # 测试脚本
│       ├── tools/              # 工具脚本
│       ├── config/             # 配置文件
│       └── docs/               # 文档
├── tools/                       # 通用工具
├── resources/                   # 资源收集
└── docs/                        # 项目文档
```

## 实验记录

| 日期 | 实验 | 项目 | 结果 | 笔记 |
|------|------|------|------|------|
| 2026-04-27 | 项目初始化 | robot-lab | ✅ | 创建项目结构 |
| 2026-04-27 | 2连杆机器人控制系统 | robot-2link | ✅ | 完整2R机器人控制系统 |
| 2026-04-27 | 二维码视觉定位系统 | vision-qr | ✅ | AprilTag检测与位姿估计 |
| 2026-08-18 | 多机器人视觉控制系统 | vision-qr/multi-robot | 🔄 | 框架搭建完成，待测试 |

## 开发计划

### 近期 (1-2周)
- [ ] 多机器人系统实际测试
- [ ] 路径规划与避障算法
- [ ] ROS2 接口封装

### 中期 (1-2月)
- [ ] 实际机器人平台集成
- [ ] Web 监控界面
- [ ] 多相机融合

### 长期
- [ ] SLAM 地图构建
- [ ] 多机器人协同任务规划
- [ ] 虚实结合的仿真环境

---

**创建日期**: 2026-04-27  
**最后更新**: 2026-08-18 (添加多机器人视觉控制系统)
