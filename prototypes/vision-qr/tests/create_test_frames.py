"""
生成测试图像序列 - 模拟相机视角的二维码
用于无相机环境测试
"""

import cv2
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def create_test_frame(frame_idx, total_frames, dictionary):
    """创建单帧测试图像"""
    width, height = 1280, 720
    tag_size = 150
    
    # 创建白色背景
    frame = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # 计算时间参数 (0-1)
    t = frame_idx / total_frames
    
    # 二维码 0: 水平移动 (保持在安全区域内)
    margin = 50
    safe_width = width - tag_size - 2 * margin
    x0 = margin + int(safe_width * (0.5 + 0.4 * np.sin(2 * np.pi * t)))
    y0 = 200
    tag0 = cv2.aruco.generateImageMarker(dictionary, 0, tag_size)
    tag0 = cv2.cvtColor(tag0, cv2.COLOR_GRAY2BGR)
    frame[y0:y0+tag_size, x0:x0+tag_size] = tag0
    cv2.putText(frame, "ID: 0", (x0, y0-10),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    # 二维码 1: 垂直移动
    x1 = 600
    safe_height = height - tag_size - 2 * margin
    y1 = margin + int(safe_height * (0.3 + 0.4 * np.cos(2 * np.pi * t)))
    tag1 = cv2.aruco.generateImageMarker(dictionary, 1, tag_size)
    tag1 = cv2.cvtColor(tag1, cv2.COLOR_GRAY2BGR)
    frame[y1:y1+tag_size, x1:x1+tag_size] = tag1
    cv2.putText(frame, "ID: 1", (x1, y1-10),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    # 二维码 2: 缩放效果（模拟距离变化）
    x2 = 900
    y2 = 450
    scale = 0.6 + 0.3 * np.sin(2 * np.pi * t)  # 0.6 - 0.9
    scaled_size = int(tag_size * scale)
    tag2 = cv2.aruco.generateImageMarker(dictionary, 2, scaled_size)
    tag2 = cv2.cvtColor(tag2, cv2.COLOR_GRAY2BGR)
    frame[y2:y2+scaled_size, x2:x2+scaled_size] = tag2
    cv2.putText(frame, "ID: 2", (x2, y2-10),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    # 添加帧信息
    info_text = f"Frame: {frame_idx}/{total_frames}"
    cv2.putText(frame, info_text, (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    return frame


def main():
    import cv2.aruco as aruco
    
    # AprilTag 字典 (OpenCV 4.10+)
    dictionary = aruco.getPredefinedDictionary(aruco.DICT_APRILTAG_36h11)
    
    # 创建输出目录
    output_dir = Path('../test_data')
    output_dir.mkdir(exist_ok=True)
    
    # 生成 100 帧测试图像
    total_frames = 100
    print(f"生成 {total_frames} 帧测试图像...")
    
    for i in range(total_frames):
        frame = create_test_frame(i, total_frames, dictionary)
        filename = output_dir / f"frame_{i:04d}.png"
        cv2.imwrite(str(filename), frame)
        
        if i % 20 == 0:
            print(f"进度: {i}/{total_frames}")
    
    print(f"测试图像已保存到: {output_dir}")
    print(f"共 {total_frames} 帧")
    
    # 同时生成一个示例图用于查看
    sample = create_test_frame(0, total_frames, dictionary)
    cv2.imwrite(str(output_dir / "sample.png"), sample)
    print("示例图像: sample.png")


if __name__ == "__main__":
    main()
