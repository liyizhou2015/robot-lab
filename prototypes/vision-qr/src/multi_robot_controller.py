"""
多机器人视觉控制系统 - 主程序

基于第三视角单相机的地面多机器人定位与控制
"""

import cv2
import numpy as np
import argparse
import yaml
from pathlib import Path

from camera import Camera, CalibratedCamera
from detector import AprilTagDetector
from multi_robot import RobotManager, WorldMapper, Commander, MockCommander
from multi_robot.robot_manager import DetectionInfo


def load_config(config_path: str) -> dict:
    """加载配置文件"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def create_detection_info(detection, aux_detection=None) -> DetectionInfo:
    """从检测结果创建 DetectionInfo"""
    return DetectionInfo(
        tag_id=detection.marker_id,
        center=tuple(detection.center),
        corners=detection.corners,
        aux_tag_id=aux_detection.marker_id if aux_detection else None,
        aux_center=tuple(aux_detection.center) if aux_detection else None
    )


def draw_robot_info(frame, robot, mapper):
    """在图像上绘制机器人信息"""
    # 转换为像素坐标
    pixel_pos = mapper.world_to_pixel((robot.current_pose.x, robot.current_pose.y, 0))
    
    # 绘制机器人位置
    color = {
        'IDLE': (0, 255, 0),      # 绿色
        'MOVING': (0, 255, 255),  # 黄色
        'ARRIVED': (0, 255, 0),   # 绿色
        'ERROR': (0, 0, 255),     # 红色
        'OFFLINE': (128, 128, 128)  # 灰色
    }.get(robot.state.name, (255, 255, 255))
    
    cv2.circle(frame, pixel_pos, 10, color, 2)
    cv2.circle(frame, pixel_pos, 3, color, -1)
    
    # 绘制朝向
    theta_rad = np.radians(robot.current_pose.theta)
    end_x = int(pixel_pos[0] + 20 * np.cos(theta_rad))
    end_y = int(pixel_pos[1] + 20 * np.sin(theta_rad))
    cv2.arrowedLine(frame, pixel_pos, (end_x, end_y), color, 2)
    
    # 绘制标签
    label = f"{robot.name} ({robot.robot_id})"
    cv2.putText(frame, label, (pixel_pos[0] + 15, pixel_pos[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    # 绘制位置信息
    pos_text = f"({robot.current_pose.x:.2f}, {robot.current_pose.y:.2f})m"
    cv2.putText(frame, pos_text, (pixel_pos[0] + 15, pixel_pos[1] + 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    
    # 如果有目标点，绘制目标
    if robot.target_pose:
        target_pixel = mapper.world_to_pixel(
            (robot.target_pose.x, robot.target_pose.y, 0)
        )
        cv2.circle(frame, target_pixel, 5, (255, 0, 0), -1)
        cv2.line(frame, pixel_pos, target_pixel, (255, 0, 0), 1)
    
    return frame


def main():
    parser = argparse.ArgumentParser(description='多机器人视觉控制系统')
    parser.add_argument('--config', '-c', type=str, default='config/camera.yaml',
                       help='相机配置文件路径')
    parser.add_argument('--robot-config', '-r', type=str, default='config/robots.json',
                       help='机器人配置文件路径')
    parser.add_argument('--camera', type=int, default=0,
                       help='相机ID')
    parser.add_argument('--marker-size', type=float, default=0.05,
                       help='二维码边长（米）')
    parser.add_argument('--camera-height', type=float, default=2.0,
                       help='相机离地面高度（米）')
    parser.add_argument('--mock', action='store_true',
                       help='模拟模式，不实际发送命令')
    
    args = parser.parse_args()
    
    # 加载相机配置
    camera_matrix = None
    dist_coeffs = None
    if Path(args.config).exists():
        config = load_config(args.config)
        camera_matrix = np.array(config.get('camera_matrix'))
        dist_coeffs = np.array(config.get('dist_coeffs'))
        print("✓ 已加载相机标定参数")
    else:
        print("⚠ 警告: 未找到相机标定文件")
        print(f"  请先运行: python tests/test_3d_pose.py --calibrate")
        return
    
    # 初始化相机
    camera = CalibratedCamera(
        camera_id=args.camera,
        camera_matrix=camera_matrix,
        dist_coeffs=dist_coeffs
    )
    
    # 初始化检测器
    detector = AprilTagDetector(marker_size=args.marker_size)
    
    # 初始化世界坐标映射器
    world_mapper = WorldMapper(
        camera_height=args.camera_height,
        camera_matrix=camera_matrix,
        dist_coeffs=dist_coeffs
    )
    
    # 初始化机器人管理器
    manager = RobotManager(world_mapper)
    
    # 加载或创建机器人配置
    if Path(args.robot_config).exists():
        manager.load_configuration(args.robot_config)
    else:
        print("\n创建默认机器人配置...")
        # 创建示例机器人
        manager.register_robot(
            robot_id=0,
            name="Robot-1",
            tag_id=0,
            aux_tag_id=100,
            ip_address="192.168.1.101",
            port=12345
        )
        manager.register_robot(
            robot_id=1,
            name="Robot-2",
            tag_id=1,
            aux_tag_id=101,
            ip_address="192.168.1.102",
            port=12345
        )
        # 保存配置
        manager.save_configuration(args.robot_config)
    
    # 初始化命令下发器
    if args.mock:
        commander = MockCommander()
        print("\n[模拟模式] 命令不会实际发送")
    else:
        commander = Commander(protocol="udp")
        commander.connect()
    
    print("\n" + "=" * 60)
    print("多机器人视觉控制系统")
    print("=" * 60)
    print("控制键:")
    print("  q - 退出")
    print("  s - 保存截图")
    print("  p - 打印状态报告")
    print("  1-9 - 发送目标点给对应机器人")
    print("  space - 紧急停止所有机器人")
    print("=" * 60)
    
    # 目标点预设（用于测试）
    test_goals = [
        (1.0, 0.0, 0.0),
        (1.0, 1.0, 90.0),
        (0.0, 1.0, 180.0),
        (-1.0, 1.0, -90.0),
        (-1.0, 0.0, 0.0),
        (-1.0, -1.0, 0.0),
        (0.0, -1.0, 0.0),
        (1.0, -1.0, 0.0),
        (0.0, 0.0, 0.0),
    ]
    
    with camera:
        while True:
            # 读取帧
            success, frame = camera.read_undistorted()
            if not success:
                print("无法读取图像")
                break
            
            # 检测二维码
            detections = detector.detect(frame)
            
            # 配对主标签和辅助标签
            detection_infos = []
            main_tags = {d.marker_id: d for d in detections if d.marker_id < 100}
            aux_tags = {d.marker_id - 100: d for d in detections if d.marker_id >= 100}
            
            for tag_id, det in main_tags.items():
                aux_det = aux_tags.get(tag_id)
                detection_infos.append(create_detection_info(det, aux_det))
            
            # 更新机器人位置
            manager.update_from_detections(detection_infos)
            
            # 发送控制命令
            for robot in manager.get_active_robots():
                commander.update_robot(robot)
            
            # 可视化
            display = frame.copy()
            
            # 绘制网格
            grid = world_mapper.create_ground_grid(
                frame.shape[:2],
                grid_size=0.5,
                grid_range=(3.0, 3.0)
            )
            display = cv2.addWeighted(display, 0.7, grid, 0.3, 0)
            
            # 绘制检测到的二维码
            display = detector.draw_detections(
                display, detections,
                draw_axes=True,
                camera_matrix=camera_matrix,
                dist_coeffs=dist_coeffs
            )
            
            # 绘制机器人信息
            for robot in manager.get_all_robots():
                display = draw_robot_info(display, robot, world_mapper)
            
            # 显示状态信息
            active_count = len(manager.get_active_robots())
            info_text = f"Robots: {active_count}/{len(manager.robots)} | Detections: {len(detections)}"
            cv2.putText(display, info_text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow("Multi-Robot Control", display)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                filename = f"capture_{cv2.getTickCount()}.png"
                cv2.imwrite(filename, display)
                print(f"截图已保存: {filename}")
            elif key == ord('p'):
                print(manager.get_status_report())
            elif key == ord(' '):
                manager.emergency_stop()
                print("紧急停止!")
            elif ord('1') <= key <= ord('9'):
                robot_id = key - ord('1')
                if robot_id < len(manager.robots):
                    goal = test_goals[robot_id % len(test_goals)]
                    manager.send_goal(robot_id, goal)
    
    cv2.destroyAllWindows()
    commander.disconnect()
    
    # 保存配置
    manager.save_configuration(args.robot_config)
    
    print("\n程序已退出")
    print(f"命令统计: {commander.get_stats()}")


if __name__ == "__main__":
    main()
