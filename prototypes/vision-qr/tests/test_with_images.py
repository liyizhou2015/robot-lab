"""
使用图像序列测试 AprilTag 检测
模拟视频输入
"""

import cv2
import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from detector import AprilTagDetector


def test_with_image_sequence(image_dir: str, delay: int = 100):
    """
    使用图像序列测试检测
    
    Args:
        image_dir: 图像目录
        delay: 帧间延迟（毫秒）
    """
    # 支持相对路径和绝对路径
    image_path = Path(image_dir)
    if not image_path.is_absolute():
        # 如果是相对路径，基于当前工作目录解析
        image_path = Path.cwd() / image_dir
    
    # 如果路径不存在，尝试基于脚本位置
    if not image_path.exists():
        script_dir = Path(__file__).parent
        image_path = script_dir.parent / 'test_data'
    
    # 获取所有图像文件
    image_files = sorted(image_path.glob("frame_*.png"))
    
    if not image_files:
        print(f"未找到图像文件: {image_path}")
        print(f"请确保已运行 create_test_frames.py 生成测试数据")
        return
    
    print(f"找到 {len(image_files)} 帧图像")
    
    # 初始化检测器
    detector = AprilTagDetector()
    
    print("按 'q' 退出，按空格键暂停")
    
    for img_path in image_files:
        # 读取图像
        frame = cv2.imread(str(img_path))
        if frame is None:
            continue
        
        # 检测二维码
        detections = detector.detect(frame)
        
        # 绘制结果
        result = detector.draw_detections(frame, detections)
        
        # 显示信息
        info = f"Frame: {img_path.name} | Detected: {len(detections)}"
        cv2.putText(result, info, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # 显示检测结果
        for i, det in enumerate(detections):
            text = f"ID {det.marker_id}: ({det.center[0]:.1f}, {det.center[1]:.1f})"
            cv2.putText(result, text, (10, 60 + i * 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        
        cv2.imshow("AprilTag Detection", result)
        
        key = cv2.waitKey(delay) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):
            cv2.waitKey(0)  # 暂停直到按键
    
    cv2.destroyAllWindows()
    print("测试完成")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='测试 AprilTag 检测')
    parser.add_argument('--dir', '-d', default='../test_data',
                       help='图像目录')
    parser.add_argument('--delay', type=int, default=100,
                       help='帧间延迟（毫秒）')
    
    args = parser.parse_args()
    
    test_with_image_sequence(args.dir, args.delay)
