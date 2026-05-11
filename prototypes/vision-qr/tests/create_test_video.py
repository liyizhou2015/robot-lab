"""
生成测试视频 - 模拟相机视角的二维码运动
用于无相机环境测试
"""

import cv2
import numpy as np
import sys
sys.path.insert(0, '../src')

from detector import AprilTagDetector


def create_test_video(output_path: str = "test_video.mp4", 
                     duration: int = 10, 
                     fps: int = 30):
    """
    生成测试视频
    
    Args:
        output_path: 输出视频路径
        duration: 视频时长（秒）
        fps: 帧率
    """
    width, height = 1280, 720
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    detector = AprilTagDetector()
    dictionary = detector.dictionary
    
    # 生成几个二维码
    tag_size = 150
    tags = {}
    for tag_id in [0, 1, 2]:
        tag_img = cv2.aruco.generateImageMarker(dictionary, tag_id, tag_size)
        tags[tag_id] = cv2.cvtColor(tag_img, cv2.COLOR_GRAY2BGR)
    
    total_frames = duration * fps
    
    print(f"生成测试视频: {output_path}")
    print(f"时长: {duration}s, 帧率: {fps}fps, 总帧数: {total_frames}")
    
    for frame_idx in range(total_frames):
        # 创建白色背景
        frame = np.ones((height, width, 3), dtype=np.uint8) * 255
        
        # 计算时间参数 (0-1)
        t = frame_idx / total_frames
        
        # 二维码 0: 水平移动
        x0 = int(200 + 300 * np.sin(2 * np.pi * t))
        y0 = 200
        frame[y0:y0+tag_size, x0:x0+tag_size] = tags[0]
        cv2.putText(frame, "ID: 0", (x0, y0-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        # 二维码 1: 垂直移动
        x1 = 600
        y1 = int(200 + 200 * np.cos(2 * np.pi * t))
        frame[y1:y1+tag_size, x1:x1+tag_size] = tags[1]
        cv2.putText(frame, "ID: 1", (x1, y1-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        # 二维码 2: 旋转效果（模拟距离变化）
        x2 = int(900 + 100 * np.sin(4 * np.pi * t))
        y2 = 400
        scale = 0.8 + 0.4 * np.sin(2 * np.pi * t)  # 0.8 - 1.2
        scaled_size = int(tag_size * scale)
        tag2_scaled = cv2.resize(tags[2], (scaled_size, scaled_size))
        frame[y2:y2+scaled_size, x2:x2+scaled_size] = tag2_scaled
        cv2.putText(frame, "ID: 2", (x2, y2-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        # 添加帧信息
        info_text = f"Frame: {frame_idx}/{total_frames}  Time: {t:.2f}s"
        cv2.putText(frame, info_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        out.write(frame)
        
        if frame_idx % 30 == 0:
            print(f"进度: {frame_idx}/{total_frames} ({100*frame_idx/total_frames:.1f}%)")
    
    out.release()
    print(f"视频已保存: {output_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='生成测试视频')
    parser.add_argument('-o', '--output', default='test_video.mp4',
                       help='输出文件名')
    parser.add_argument('-d', '--duration', type=int, default=10,
                       help='视频时长（秒）')
    parser.add_argument('-f', '--fps', type=int, default=30,
                       help='帧率')
    
    args = parser.parse_args()
    
    create_test_video(args.output, args.duration, args.fps)
