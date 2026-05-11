"""
保存检测结果可视化（无需 GUI，使用 OpenCV 生成图片）
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from detector import AprilTagDetector
import cv2
import numpy as np


def save_detection_visualization(source: str, output_dir: str = "visualization", 
                                 max_frames: int = 20):
    """
    保存检测结果可视化图像
    
    Args:
        source: 视频文件路径
        output_dir: 输出目录
        max_frames: 最多保存多少帧
    """
    source_path = Path(source)
    if not source_path.is_absolute():
        source_path = Path.cwd() / source
    
    if not source_path.exists():
        print(f"文件不存在: {source_path}")
        return
    
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # 打开视频
    cap = cv2.VideoCapture(str(source_path))
    if not cap.isOpened():
        print(f"无法打开视频: {source_path}")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"视频: {source_path.name}")
    print(f"总帧数: {total_frames}, FPS: {fps:.1f}")
    print(f"将保存 {max_frames} 帧到: {output_path}")
    print("=" * 50)
    
    detector = AprilTagDetector()
    
    # 均匀采样帧
    frame_indices = [int(i * total_frames / max_frames) for i in range(max_frames)]
    
    saved_count = 0
    
    for idx, frame_idx in enumerate(frame_indices):
        # 跳转到指定帧
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        
        if not ret:
            continue
        
        # 检测
        detections = detector.detect(frame)
        
        # 创建对比图像（左右并排）
        h, w = frame.shape[:2]
        
        # 左侧：原始图像
        left = frame.copy()
        
        # 右侧：检测结果
        right = detector.draw_detections(frame, detections)
        
        # 合并
        combined = cv2.hconcat([left, right])
        
        # 添加标题栏
        title_height = 40
        title_bar = np.ones((title_height, combined.shape[1], 3), dtype=np.uint8) * 240
        
        timestamp = frame_idx / fps if fps > 0 else 0
        title_text = f"Frame {frame_idx} | Time: {timestamp:.2f}s | Detected: {len(detections)} tags"
        if detections:
            ids = [d.marker_id for d in detections]
            title_text += f" | IDs: {ids}"
        
        cv2.putText(title_bar, title_text, (10, 28),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        # 添加标签
        cv2.putText(left, "Original", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(right, "Detection", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # 重新合并（带标题）
        final = cv2.vconcat([title_bar, combined])
        
        # 保存
        output_file = output_path / f"frame_{frame_idx:04d}.jpg"
        cv2.imwrite(str(output_file), final)
        
        saved_count += 1
        print(f"[{idx+1}/{max_frames}] Frame {frame_idx}: {len(detections)} detections -> {output_file.name}")
    
    cap.release()
    
    print("=" * 50)
    print(f"完成! 保存了 {saved_count} 张可视化图像到: {output_path.absolute()}")
    print(f"\n在 Windows 中查看:")
    print(f"  打开文件资源管理器，输入路径查看")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='保存检测结果可视化')
    parser.add_argument('video', help='视频文件路径')
    parser.add_argument('-o', '--output', default='visualization',
                       help='输出目录 (默认: visualization)')
    parser.add_argument('-n', '--num-frames', type=int, default=20,
                       help='保存帧数 (默认: 20)')
    
    args = parser.parse_args()
    
    save_detection_visualization(args.video, args.output, args.num_frames)
