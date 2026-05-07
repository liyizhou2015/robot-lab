"""
主程序 - 二维码视觉定位
"""

import cv2
import numpy as np
import argparse
import yaml
from pathlib import Path

from camera import Camera, CalibratedCamera
from detector import AprilTagDetector


def load_config(config_path: str) -> dict:
    """加载配置文件"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description='二维码视觉定位')
    parser.add_argument('--config', '-c', type=str, default='config/camera.yaml',
                       help='配置文件路径')
    parser.add_argument('--camera', type=int, default=0,
                       help='相机ID')
    parser.add_argument('--marker-size', type=float, default=0.05,
                       help='二维码边长（米）')
    parser.add_argument('--no-gui', action='store_true',
                       help='无GUI模式，仅输出坐标')
    
    args = parser.parse_args()
    
    # 加载配置
    camera_matrix = None
    dist_coeffs = None
    if Path(args.config).exists():
        config = load_config(args.config)
        camera_matrix = np.array(config.get('camera_matrix'))
        dist_coeffs = np.array(config.get('dist_coeffs'))
        print("已加载相机标定参数")
    else:
        print("警告: 未找到相机标定文件，位姿估计可能不准确")
        print(f"请运行标定程序生成 {args.config}")
    
    # 初始化相机
    if camera_matrix is not None:
        camera = CalibratedCamera(
            camera_id=args.camera,
            camera_matrix=camera_matrix,
            dist_coeffs=dist_coeffs
        )
    else:
        camera = Camera(camera_id=args.camera)
    
    # 初始化检测器
    detector = AprilTagDetector(marker_size=args.marker_size)
    
    print("=" * 50)
    print("二维码视觉定位系统")
    print("=" * 50)
    print("按 'q' 退出")
    print("按 's' 保存截图")
    print("=" * 50)
    
    with camera:
        while True:
            # 读取帧
            if camera_matrix is not None:
                success, frame = camera.read_undistorted()
            else:
                success, frame = camera.read()
                
            if not success:
                print("无法读取图像")
                break
            
            # 检测二维码
            if camera_matrix is not None:
                detections = detector.detect_and_estimate(
                    frame, camera_matrix, dist_coeffs
                )
            else:
                detections = detector.detect(frame)
            
            # 输出信息（无GUI模式或控制台输出）
            if args.no_gui:
                for det in detections:
                    if det.pose:
                        rvec, tvec = det.pose
                        print(f"ID: {det.marker_id}, "
                              f"位置: [{tvec[0][0]:.3f}, {tvec[1][0]:.3f}, {tvec[2][0]:.3f}]")
            else:
                # 可视化
                display = detector.draw_detections(
                    frame, detections,
                    draw_axes=camera_matrix is not None,
                    camera_matrix=camera_matrix,
                    dist_coeffs=dist_coeffs
                )
                
                # 显示状态信息
                info_text = f"Detected: {len(detections)}"
                cv2.putText(display, info_text, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                cv2.imshow("Vision QR", display)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    filename = f"capture_{cv2.getTickCount()}.png"
                    cv2.imwrite(filename, display)
                    print(f"截图已保存: {filename}")
    
    if not args.no_gui:
        cv2.destroyAllWindows()
    
    print("程序已退出")


if __name__ == "__main__":
    main()
