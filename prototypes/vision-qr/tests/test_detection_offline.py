"""
离线测试 AprilTag 检测（支持图像序列和视频文件）
"""

import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from detector import AprilTagDetector
import cv2


def test_detection(source: str, save_visualization: bool = False, output_dir: str = "output"):
    """
    离线测试检测
    
    Args:
        source: 图像目录或视频文件路径
        save_visualization: 是否保存可视化结果图像
        output_dir: 可视化结果保存目录
    """
    # 支持相对路径和绝对路径
    source_path = Path(source)
    if not source_path.is_absolute():
        # 如果是相对路径，基于当前工作目录解析
        source_path = Path.cwd() / source
    
    # 如果路径不存在，尝试基于脚本位置
    if not source_path.exists():
        script_dir = Path(__file__).parent
        # 先检查是否是视频文件
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
        for ext in video_extensions:
            video_path = script_dir / f"{source}{ext}"
            if video_path.exists():
                source_path = video_path
                break
        else:
            # 否则尝试 test_data 目录
            source_path = script_dir.parent / 'test_data'
    
    # 判断是视频文件还是图像目录
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    is_video = source_path.suffix.lower() in video_extensions
    
    # 创建输出目录
    if save_visualization:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        print(f"可视化结果将保存到: {output_path}")
    
    detector = AprilTagDetector()
    total_detections = 0
    frame_count = 0
    
    if is_video:
        # 处理视频文件
        print(f"测试视频文件: {source_path}")
        print("=" * 50)
        
        cap = cv2.VideoCapture(str(source_path))
        if not cap.isOpened():
            print(f"无法打开视频文件: {source_path}")
            return
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"视频信息: {total_frames} 帧, {fps:.1f} FPS")
        print("=" * 50)
        
        # 每N帧处理一次（避免输出过多）
        process_every_n_frames = max(1, int(fps / 5))  # 每秒约5帧
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 跳帧处理
            if frame_count % process_every_n_frames != 0:
                frame_count += 1
                continue
            
            detections = detector.detect(frame)
            
            # 保存可视化结果
            if save_visualization and len(detections) > 0:
                vis_frame = detector.draw_detections(frame, detections)
                # 添加信息
                timestamp = frame_count / fps if fps > 0 else 0
                info_text = f"Frame: {frame_count} Time: {timestamp:.2f}s Detected: {len(detections)}"
                cv2.putText(vis_frame, info_text, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                # 保存
                output_file = output_path / f"frame_{frame_count:04d}.jpg"
                cv2.imwrite(str(output_file), vis_frame)
            
            timestamp = frame_count / fps if fps > 0 else 0
            print(f"\nFrame {frame_count} ({timestamp:.2f}s):")
            print(f"  检测到 {len(detections)} 个二维码:")
            
            for det in detections:
                print(f"    ID {det.marker_id}: center=({det.center[0]:.1f}, {det.center[1]:.1f})")
            
            total_detections += len(detections)
            frame_count += 1
            
            # 限制最大处理帧数
            if frame_count >= 1000:
                print("\n(已达到最大处理帧数限制)")
                break
        
        cap.release()
        
    else:
        # 处理图像序列
        image_files = sorted(source_path.glob("frame_*.png"))
        
        if not image_files:
            # 尝试其他图像格式
            image_files = sorted(source_path.glob("*.jpg")) + sorted(source_path.glob("*.png"))
        
        if not image_files:
            print(f"未找到图像文件: {source_path}")
            print(f"请确保已运行 create_test_frames.py 生成测试数据")
            return
        
        print(f"测试 {len(image_files)} 帧图像...")
        print("=" * 50)
        
        for img_path in image_files[:100]:  # 最多处理100帧
            frame = cv2.imread(str(img_path))
            if frame is None:
                continue
            
            detections = detector.detect(frame)
            
            print(f"\n{frame_count}: {img_path.name}")
            print(f"  检测到 {len(detections)} 个二维码:")
            
            for det in detections:
                print(f"    ID {det.marker_id}: center=({det.center[0]:.1f}, {det.center[1]:.1f})")
            
            total_detections += len(detections)
            frame_count += 1
    
    print("\n" + "=" * 50)
    if frame_count > 0:
        print(f"测试完成: {frame_count} 帧, 共 {total_detections} 次检测")
        print(f"平均每帧: {total_detections/frame_count:.2f} 个二维码")
    else:
        print("未处理任何帧")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='离线测试 AprilTag 检测（支持图像和视频）')
    parser.add_argument('source', nargs='?', default='../test_data',
                       help='图像目录或视频文件路径（默认: ../test_data）')
    parser.add_argument('--save-vis', '-s', action='store_true',
                       help='保存可视化结果图像')
    parser.add_argument('--output', '-o', default='output',
                       help='可视化结果输出目录')
    
    args = parser.parse_args()
    
    test_detection(args.source, args.save_vis, args.output)
