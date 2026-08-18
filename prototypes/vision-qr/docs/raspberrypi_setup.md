# 树莓派4 + Camera Module 3 Wide 配置指南

## 硬件配置

| 组件 | 规格 |
|------|------|
| **主机** | 树莓派4 (4GB RAM) |
| **摄像头** | Camera Module 3 Wide (IMX708) |
| **分辨率** | 1200万像素 (4608×2592) |
| **视角** | 120° 广角 |
| **安装方式** | 俯视安装，垂直向下拍摄 |

## 树莓派系统设置

### 1. 启用摄像头

```bash
# 使用 raspi-config 启用摄像头
sudo raspi-config

# 选择: Interface Options → Camera → Enable
# 重启树莓派
sudo reboot
```

### 2. 安装依赖

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Python 依赖
sudo apt install -y python3-pip python3-opencv libopencv-dev

# 安装 libcamera (Camera Module 3 必需)
sudo apt install -y python3-libcamera python3-picamera2

# 安装其他依赖
pip3 install numpy pyyaml
```

### 3. 安装 OpenCV 4.10+ (带 ArUco 支持)

```bash
# 检查 OpenCV 版本
python3 -c "import cv2; print(cv2.__version__)"

# 如果版本低于 4.10，需要编译安装
# 下载并编译 OpenCV (需要较长时间)
sudo apt install -y cmake g++ wget unzip

# 或使用预编译版本
pip3 install opencv-python==4.10.0.84 opencv-contrib-python==4.10.0.84
```

## 摄像头配置

### Camera Module 3 Wide 参数

| 参数 | 值 |
|------|-----|
| 传感器 | Sony IMX708 |
| 分辨率 | 4608 × 2592 (11.9MP) |
| 视角 | 120° 对角线 |
| 焦距 | 2.75mm (等效 15mm) |
| 光圈 | f/2.2 |
| 对焦 | 自动对焦 (5cm - ∞) |

### 推荐工作分辨率

由于1200万像素处理开销大，建议使用较低分辨率：

| 用途 | 分辨率 | FPS | 说明 |
|------|--------|-----|------|
| 高精度定位 | 1920×1080 | ~30 | 平衡精度与性能 |
| 实时控制 | 1280×720 | ~60 | 优先帧率 |
| 大范围跟踪 | 2560×1440 | ~15 | 更多机器人 |

### picamera2 配置示例

```python
from picamera2 import Picamera2
import cv2

# 初始化相机
picam2 = Picamera2()

# 配置相机参数
config = picam2.create_video_configuration(
    main={"size": (1920, 1080), "format": "RGB888"},
    lores={"size": (640, 480)},
    display="lores"
)
picam2.configure(config)

# 设置相机控制参数
picam2.set_controls({
    "AfMode": 0,  # 手动对焦 (0=手动, 1=自动)
    "LensPosition": 0.0,  # 对焦位置 (0=无穷远, 10=10cm)
    "ExposureTime": 10000,  # 曝光时间 (微秒)
    "AnalogueGain": 1.0,  # 模拟增益
})

picam2.start()

# 捕获图像
frame = picam2.capture_array()
frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

# 处理图像...
```

## 相机标定

### 1. 准备棋盘格

打印棋盘格标定板，建议使用 9×6 内角点，每个方格 25mm：

```bash
cd tools
python generate_chessboard.py --rows 9 --cols 6 --size 25
```

### 2. 拍摄标定图像

```bash
cd tests
python capture_calibration_rpi.py --output calibration_images/
```

**capture_calibration_rpi.py**:
```python
from picamera2 import Picamera2
import cv2
import os
from pathlib import Path

def main():
    output_dir = Path("calibration_images")
    output_dir.mkdir(exist_ok=True)
    
    picam2 = Picamera2()
    config = picam2.create_video_configuration(
        main={"size": (1920, 1080), "format": "RGB888"}
    )
    picam2.configure(config)
    picam2.start()
    
    print("相机标定图像采集")
    print("按 'c' 捕获图像 (至少10张)")
    print("按 'q' 退出")
    
    count = 0
    while True:
        frame = picam2.capture_array()
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        cv2.imshow("Calibration", frame_bgr)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('c'):
            filename = output_dir / f"calib_{count:03d}.jpg"
            cv2.imwrite(str(filename), frame_bgr)
            print(f"保存: {filename}")
            count += 1
        elif key == ord('q'):
            break
    
    picam2.stop()
    cv2.destroyAllWindows()
    print(f"共采集 {count} 张图像")

if __name__ == "__main__":
    main()
```

### 3. 运行标定

```bash
python test_3d_pose.py --calibrate calibration_images/ -c config/camera_rpi.yaml
```

### 4. 验证标定结果

标定完成后会生成 `camera_rpi.yaml`:

```yaml
camera_matrix:
  - [1500.0, 0.0, 960.0]
  - [0.0, 1500.0, 540.0]
  - [0.0, 0.0, 1.0]
dist_coeffs:
  - [0.1, -0.2, 0.0, 0.0, 0.0]
image_size: [1920, 1080]
camera_height: 2.0  # 相机离地面高度，手动测量填入
```

## 树莓派4 性能优化

### 1. 分辨率优化

```python
# 根据场景选择分辨率
SCENE_CONFIG = {
    "small_arena": {      # 2m × 2m 场地
        "resolution": (1280, 720),
        "fps": 30,
        "max_robots": 10
    },
    "medium_arena": {     # 5m × 5m 场地
        "resolution": (1920, 1080),
        "fps": 30,
        "max_robots": 20
    },
    "large_arena": {      # 10m × 10m 场地
        "resolution": (2560, 1440),
        "fps": 15,
        "max_robots": 50
    }
}
```

### 2. 跳帧处理

```python
class FrameSkipper:
    """跳帧器，降低处理频率"""
    def __init__(self, process_every_n=2):
        self.n = process_every_n
        self.counter = 0
    
    def should_process(self) -> bool:
        self.counter += 1
        if self.counter >= self.n:
            self.counter = 0
            return True
        return False

# 使用
skipper = FrameSkipper(process_every_n=2)  # 每2帧处理1次

while True:
    frame = camera.capture()
    if skipper.should_process():
        detections = detector.detect(frame)
        # 处理...
```

### 3. 降低 CPU 占用

```bash
# 限制 CPU 频率（减少发热）
echo "powersave" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# 或使用性能模式（最大化性能）
echo "performance" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### 4. 使用硬件加速 (可选)

```bash
# 启用 GPU 加速 (如果 OpenCV 编译时支持)
export OPENCV_ENABLE_MEM_OPTIMIZATION=1
```

## 网络配置

### 树莓派作为 AP (机器人连接)

```bash
# 安装 hostapd 和 dnsmasq
sudo apt install -y hostapd dnsmasq

# 配置静态 IP
sudo nano /etc/dhcpcd.conf
# 添加:
# interface wlan0
# static ip_address=192.168.4.1/24
# nohook wpa_supplicant

# 配置 hostapd
sudo nano /etc/hostapd/hostapd.conf
# 添加:
# interface=wlan0
# ssid=RobotLab
# wpa_passphrase=your_password
# channel=7
```

### 或使用 WiFi 连接路由器

```bash
# 配置 wpa_supplicant
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf

network={
    ssid="YourWiFi"
    psk="YourPassword"
}
```

## 启动脚本

创建开机自启服务：

```bash
sudo nano /etc/systemd/system/multi-robot.service
```

```ini
[Unit]
Description=Multi-Robot Vision Control
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/robot-lab/prototypes/vision-qr/src
ExecStart=/usr/bin/python3 multi_robot_controller.py --config config/camera_rpi.yaml
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
sudo systemctl enable multi-robot.service
sudo systemctl start multi-robot.service
sudo systemctl status multi-robot.service
```

## 常见问题

### Q: Camera Module 3 无法识别
**A**:
```bash
# 检查摄像头连接
libcamera-hello --list-cameras

# 测试摄像头
libcamera-hello

# 更新固件
sudo rpi-update
```

### Q: 帧率过低
**A**:
- 降低分辨率到 1280×720
- 使用跳帧处理
- 关闭不必要的可视化

### Q: 图像模糊
**A**:
- 调整对焦位置：`picam2.set_controls({"LensPosition": 5.0})`
- 检查相机是否固定牢固
- 增加光照

### Q: 检测距离受限
**A**:
- Camera Module 3 Wide 广角特性适合近距离大范围
- 对于远距离，考虑使用标准镜头版本
- 增大桥贴二维码尺寸

## 参考

- [Camera Module 3 文档](https://www.raspberrypi.com/documentation/accessories/camera.html)
- [picamera2 手册](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf)
- [树莓派性能优化](https://www.raspberrypi.com/documentation/computers/configuration.html)
