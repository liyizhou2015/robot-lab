"""
可视化测试 AprilTag 检测（支持图像序列和视频文件）
"""

import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from detector import AprilTagDetector
import cv2


def test_detection_visual(source: str, delay: int = 100):
    """
    可视化测试检测
    
    Args:
        source: 图像目录或视频文件路径
        delay: 帧间延迟（毫秒），按空格键暂停，'q' 退出，'s' 保存截图
    """
    # 支持相对路径和绝对路径
    source_path = Path(source)
    if not source_path.is_absolute():
        source_path = Path.cwd() / source
    
    # 如果路径不存在，尝试基于脚本位置
    if not source_path.exists():
        script_dir = Path(__file__).parent
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
        for ext in video_extensions:
            video_path = script_dir / f"{source}{ext}"
            if video_path.exists():
                source_path = video_path
                break
        else:
            source_path = script_dir.parent / 'test_data'
    
    # 判断是视频文件还是图像目录
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    is_video = source_path.suffix.lower() in video_extensions
    
    detector = AprilTagDetector()
    
    # 设置窗口
    window_name = "AprilTag Detection"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1280, 720)
    
    paused = False
    frame_count = 0
    total_detections = 0
    
    if is_video:
        # 处理视频文件
        print(f"测试视频文件: {source_path}")
        cap = cv2.VideoCapture(str(source_path))
        if not cap.isOpened():
            print(f"无法打开视频文件: {source_path}")
            return
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"视频信息: {total_frames} 帧, {fps:.1f} FPS")
        print("控制: 空格=暂停, s=截图, q=退出")
        
        while True:
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    break
                frame_count += 1
            
            # 检测
            detections = detector.detect(frame)
            total_detections += len(detections)
            
            # 绘制结果
            display = detector.draw_detections(frame, detections)
            
            # 添加信息
            timestamp = frame_count / fps if fps > 0 else 0
            info_text = f"Frame: {frame_count}/{total_frames} | Time: {timestamp:.2f}s | Detected: {len(detections)}"
            cv2.putText(display, info_text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # 显示检测详情
            for i, det in enumerate(detections):
                text = f"ID {det.marker_id}: ({det.center[0]:.0f}, {det.center[1]:.0f})"
                cv2.putText(display, text, (10, 60 + i * 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            
            # 显示暂停状态
            if paused:
                cv2.putText(display, "PAUSED", (display.shape[1] - 150, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
            cv2.imshow(window_name, display)
            
            # 键盘控制
            key = cv2.waitKey(delay if not paused else 0) & 0xFF
            if key == ord('q'):
                break
            elif key == ord(' '):
                paused = not paused
            elif key == ord('s'):
                screenshot_path = f"screenshot_{frame_count:04d}.png"
                cv2.imwrite(screenshot_path, display)
                print(f"截图已保存: {screenshot_path}")
            elif key == ord('f'):  # 快进
                delay = max(1, delay - 20)
                print(f"延迟: {delay}ms")
            elif key == ord('r'):  # 减速
                delay += 20
                print(f"延迟: {delay}ms")
        
        cap.release()
        
    else:
        # 处理图像序列
        image_files = sorted(source_path.glob("frame_*.png"))
        if not image_files:
            image_files = sorted(source_path.glob("*.jpg")) + sorted(source_path.glob("*.png"))
        
        if not image_files:
            print(f"未找到图像文件: {source_path}")
            return
        
        print(f"测试 {len(image_files)} 帧图像...")
        print("控制: 空格=暂停, 左右箭头=上一帧/下一帧, s=截图, q=退出")
        
        current_idx = 0
        
        while True:
            img_path = image_files[current_idx]
            frame = cv2.imread(str(img_path))
            if frame is None:
                current_idx = (current_idx + 1) % len(image_files)
                continue
            
            frame_count = current_idx + 1
            
            # 检测
            detections = detector.detect(frame)
            total_detections += len(detections)
            
            # 绘制结果
            display = detector.draw_detections(frame, detections)
            
            # 添加信息
            info_text = f"Frame: {frame_count}/{len(image_files)} | File: {img_path.name} | Detected: {len(detections)}"
            cv2.putText(display, info_text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # 显示检测详情
            for i, det in enumerate(detections):
                text = f"ID {det.marker_id}: ({det.center[0]:.0f}, {det.center[1]:.0f})"
                cv2.putText(display, text, (10, 60 + i * 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            
            # 显示暂停状态
            if paused:
                cv2.putText(display, "PAUSED", (display.shape[1] - 150, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
            cv2.imshow(window_name, display)
            
            # 键盘控制
            wait_time = 0 if paused else delay
            key = cv2.waitKey(wait_time) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord(' '):
                paused = not paused
            elif key == ord('s'):
                screenshot_path = f"screenshot_{img_path.stem}.png"
                cv2.imwrite(screenshot_path, display)
                print(f"截图已保存: {screenshot_path}")
            elif key == 81 or key == 2:  # 左箭头
                current_idx = max(0, current_idx - 1)
                paused = True
            elif key == 83 or key == 3:  # 右箭头
                current_idx = min(len(image_files) - 1, current_idx + 1)
                paused = True
            elif key == ord('f'):  # 快进
                delay = max(1, delay - 20)
            elif key == ord('r'):  # 减速
                delay += 20
            else:
                if not paused:
                    current_idx = (current_idx + 1) % len(image_files)
    
    cv2.destroyAllWindows()
    
    print("\n" + "=" * 50)
    print(f"测试完成: {frame_count} 帧, 共 {total_detections} 次检测")
    if frame_count > 0:
        print(f"平均每帧: {total_detections/frame_count:.2f} 个二维码")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='可视化测试 AprilTag 检测')
    parser.add_argument('source', nargs='?', default='../test_data',
                       help='图像目录或视频文件路径（默认: ../test_data）')
    parser.add_argument('--delay', '-d', type=int, default=100,
                       help='帧间延迟（毫秒），默认 100ms')
    
    args = parser.parse_args()
    
    test_detection_visual(args.source, args.delay)
