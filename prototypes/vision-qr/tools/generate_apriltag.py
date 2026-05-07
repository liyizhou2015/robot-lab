"""
生成 AprilTag 36h11 二维码图像
用于打印或显示
"""

import cv2
import numpy as np
import argparse
from pathlib import Path


def generate_apriltag(marker_id: int, size: int = 200) -> np.ndarray:
    """
    生成单个 AprilTag 图像
    
    Args:
        marker_id: 二维码ID (0-586)
        size: 图像尺寸（像素）
        
    Returns:
        二维码图像
    """
    # OpenCV 4.10+
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
    
    # 生成二维码
    marker_img = cv2.aruco.generateImageMarker(dictionary, marker_id, size)
    
    # 添加白色边框（便于检测）
    border = int(size * 0.1)
    marker_with_border = cv2.copyMakeBorder(
        marker_img, border, border, border, border,
        cv2.BORDER_CONSTANT, value=255
    )
    
    return marker_with_border


def generate_tag_sheet(marker_ids: list, tag_size: int = 200, 
                       cols: int = 3, margin: int = 50) -> np.ndarray:
    """
    生成包含多个二维码的打印页
    
    Args:
        marker_ids: 二维码ID列表
        tag_size: 单个二维码尺寸
        cols: 每行个数
        margin: 边距
        
    Returns:
        打印页图像
    """
    rows = (len(marker_ids) + cols - 1) // cols
    
    # 计算页面尺寸
    page_width = cols * tag_size + (cols + 1) * margin
    page_height = rows * tag_size + (rows + 1) * margin
    
    # 创建白色背景
    page = np.ones((page_height, page_width), dtype=np.uint8) * 255
    
    # 放置二维码
    for idx, marker_id in enumerate(marker_ids):
        row = idx // cols
        col = idx % cols
        
        x = margin + col * (tag_size + margin)
        y = margin + row * (tag_size + margin)
        
        tag = generate_apriltag(marker_id, tag_size)
        h, w = tag.shape
        page[y:y+h, x:x+w] = tag
        
        # 添加ID标签
        label = f"ID: {marker_id}"
        # 在二维码下方添加标签
        cv2.putText(page, label, (x, y + h + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, 0, 2)
    
    return page


def main():
    parser = argparse.ArgumentParser(description='生成 AprilTag 二维码')
    parser.add_argument('--id', '-i', type=int, default=0,
                       help='二维码ID (0-586)')
    parser.add_argument('--size', '-s', type=int, default=200,
                       help='二维码尺寸（像素）')
    parser.add_argument('--output', '-o', type=str, default='tag.png',
                       help='输出文件名')
    parser.add_argument('--sheet', action='store_true',
                       help='生成打印页（多个二维码）')
    parser.add_argument('--range', '-r', type=str, default='0-5',
                       help='ID范围，如 "0-5" 或 "0,2,4,6"')
    
    args = parser.parse_args()
    
    # 创建输出目录
    output_dir = Path('generated_tags')
    output_dir.mkdir(exist_ok=True)
    
    if args.sheet:
        # 解析ID范围
        if '-' in args.range:
            start, end = map(int, args.range.split('-'))
            marker_ids = list(range(start, end + 1))
        else:
            marker_ids = [int(x) for x in args.range.split(',')]
        
        # 生成打印页
        sheet = generate_tag_sheet(marker_ids, args.size)
        output_path = output_dir / f"apriltag_sheet_{args.range}.png"
        cv2.imwrite(str(output_path), sheet)
        print(f"打印页已生成: {output_path}")
        print(f"包含 {len(marker_ids)} 个二维码")
        
    else:
        # 生成单个二维码
        if args.id < 0 or args.id > 586:
            print("错误: ID 必须在 0-586 范围内")
            return
            
        tag = generate_apriltag(args.id, args.size)
        output_path = output_dir / args.output
        cv2.imwrite(str(output_path), tag)
        print(f"二维码已生成: {output_path}")
        print(f"ID: {args.id}, 尺寸: {args.size}x{args.size}")
    
    print(f"\n提示: 打印时保持实际尺寸为设定的物理尺寸")
    print(f"例如: 若设定 marker_size=0.05m，则打印尺寸应对应 5cm")


if __name__ == "__main__":
    main()
