"""
3D位姿估计测试
支持相机标定和二维码3D定位
"""

import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from detector import AprilTagDetector, MarkerDetection
from pose_estimator import PoseEstimator, CameraCalibrator, load_calibration, save_calibration
import cv2
import numpy as np


def test_with_video(video_path: str, calibration_file: Optional[str] = None,
                   marker_size: float = 0.05):
    """
    测试视频中的3D位姿估计
    
    Args:
        video_path: 视频文件路径
        calibration_file: 相机标定文件路径（可选）
        marker_size: 二维码实际边长（米）
    """
    # 加载相机标定
    if calibration_file and Path(calibration_file).exists():
        calib = load_calibration(calibration_file)
        print(f"已加载相机标定: {calibration_file}")
    else:
        # 使用默认内参（近似值，仅用于测试）
        print("警告: 使用默认相机参数，3D定位可能不准确")
        print("建议先运行相机标定: python test_3d_pose.py --calibrate")
        
        # 假设 720p 相机，约 60度 FOV
        fx = fy = 800  # 焦距（像素）
        cx, cy = 640, 360  # 主点
        calib = type('obj', (object,), {
            'camera_matrix': np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]]),
            'dist_coeffs': np.zeros((4, 1)),
            'image_size': (1280, 720)
        })()
    
    # 初始化检测器和位姿估计器
    detector = AprilTagDetector(marker_size=marker_size)
    pose_estimator = PoseEstimator(marker_size=marker_size)
    
    # 打开视频
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"无法打开视频: {video_path}")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"\n视频信息: {int(cap.get(cv2.CAP_PROP_FRAME_COUNT))} 帧, {fps:.1f} FPS")
    print("=" * 60)
    print("3D位姿估计结果:")
    print("=" * 60)
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 检测二维码
        detections = detector.detect(frame)
        
        # 估计3D位姿
        for det in detections:
            pose = pose_estimator.estimate_pose(
                det.corners, calib.camera_matrix, calib.dist_coeffs
            )
            
            if pose:
                det.pose = (pose.rotation, pose.position)
                
                timestamp = frame_count / fps if fps > 0 else 0
                print(f"\nFrame {frame_count} ({timestamp:.2f}s) - ID {det.marker_id}:")
                print(f"  位置: [{pose.position[0]:.3f}, {pose.position[1]:.3f}, {pose.position[2]:.3f}] m")
                print(f"  欧拉角: [Roll={pose.euler_angles[0]:.1f}, Pitch={pose.euler_angles[1]:.1f}, Yaw={pose.euler_angles[2]:.1f}] deg")
                print(f"  距离: {np.linalg.norm(pose.position):.3f} m")
        
        # 限制输出帧数
        frame_count += 1
        if frame_count >= 30:  # 只显示前30帧
            print("\n... (仅显示前30帧)")
            break
    
    cap.release()
    
    print("\n" + "=" * 60)
    print("提示: 使用 --save-vis 保存带可视化的结果")


def calibrate_camera(image_dir: str, output_file: str = "camera_calibration.yaml"):
    """
    使用棋盘格图像标定相机
    
    Args:
        image_dir: 棋盘格图像目录
        output_file: 输出标定文件
    """
    image_path = Path(image_dir)
    if not image_path.exists():
        print(f"目录不存在: {image_dir}")
        print("请提供包含棋盘格图像的目录")
        return
    
    # 查找所有图像
    image_files = sorted(image_path.glob("*.jpg")) + sorted(image_path.glob("*.png"))
    
    if len(image_files) < 3:
        print(f"图像数量不足: {len(image_files)} (至少需要3张)")
        return
    
    print(f"找到 {len(image_files)} 张图像")
    
    # 执行标定
    calibrator = CameraCalibrator(checkerboard_size=(9, 6), square_size=0.025)
    calibration = calibrator.calibrate_from_images([str(f) for f in image_files])
    
    if calibration:
        save_calibration(calibration, output_file)
        print(f"\n标定完成! 参数已保存到: {output_file}")


def save_3d_visualization(video_path: str, output_dir: str = "3d_visualization",
                         calibration_file: Optional[str] = None,
                         marker_size: float = 0.05, num_frames: int = 10):
    """
    保存3D位姿估计可视化结果
    
    Args:
        video_path: 视频文件路径
        output_dir: 输出目录
        calibration_file: 相机标定文件
        marker_size: 二维码边长
        num_frames: 保存帧数
    """
    # 加载相机标定
    if calibration_file and Path(calibration_file).exists():
        calib = load_calibration(calibration_file)
    else:
        # 默认参数
        fx = fy = 800
        cx, cy = 640, 360
        calib = type('obj', (object,), {
            'camera_matrix': np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]]),
            'dist_coeffs': np.zeros((4, 1)),
            'image_size': (1280, 720)
        })()
    
    detector = AprilTagDetector(marker_size=marker_size)
    pose_estimator = PoseEstimator(marker_size=marker_size)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"无法打开视频: {video_path}")
        return
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print(f"保存 {num_frames} 帧3D可视化结果到: {output_path}")
    
    # 均匀采样
    frame_indices = [int(i * total_frames / num_frames) for i in range(num_frames)]
    
    for idx, frame_idx in enumerate(frame_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            continue
        
        # 检测和估计位姿
        detections = detector.detect(frame)
        for det in detections:
            pose = pose_estimator.estimate_pose(
                det.corners, calib.camera_matrix, calib.dist_coeffs
            )
            if pose:
                det.pose = (pose.rotation, pose.position)
        
        # 绘制（带3D坐标轴）
        vis = detector.draw_detections(
            frame, detections,
            draw_axes=True,
            camera_matrix=calib.camera_matrix,
            dist_coeffs=calib.dist_coeffs
        )
        
        # 添加3D信息
        timestamp = frame_idx / fps if fps > 0 else 0
        info = f"Frame {frame_idx} Time: {timestamp:.2f}s"
        cv2.putText(vis, info, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        y_offset = 60
        for det in detections:
            if det.pose:
                rvec, tvec = det.pose
                pos_text = f"ID{det.marker_id}: Pos=[{tvec[0]:.2f}, {tvec[1]:.2f}, {tvec[2]:.2f}]m"
                cv2.putText(vis, pos_text, (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                y_offset += 25
        
        # 保存
        output_file = output_path / f"pose_{frame_idx:04d}.jpg"
        cv2.imwrite(str(output_file), vis)
        print(f"[{idx+1}/{num_frames}] Frame {frame_idx}: {len(detections)} detections")
    
    cap.release()
    print(f"完成! 结果保存在: {output_path.absolute()}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='3D位姿估计测试')
    parser.add_argument('video', nargs='?', help='视频文件路径')
    parser.add_argument('--calibrate', metavar='IMAGE_DIR',
                       help='使用棋盘格图像标定相机')
    parser.add_argument('--calibration', '-c', default='camera_calibration.yaml',
                       help='相机标定文件')
    parser.add_argument('--marker-size', '-s', type=float, default=0.05,
                       help='二维码边长（米），默认0.05')
    parser.add_argument('--save-vis', action='store_true',
                       help='保存可视化结果')
    parser.add_argument('--output', '-o', default='3d_visualization',
                       help='可视化输出目录')
    parser.add_argument('-n', '--num-frames', type=int, default=10,
                       help='保存帧数')
    
    args = parser.parse_args()
    
    if args.calibrate:
        calibrate_camera(args.calibrate, args.calibration)
    elif args.video:
        if args.save_vis:
            save_3d_visualization(args.video, args.output, args.calibration, 
                                 args.marker_size, args.num_frames)
        else:
            test_with_video(args.video, args.calibration, args.marker_size)
    else:
        parser.print_help()
