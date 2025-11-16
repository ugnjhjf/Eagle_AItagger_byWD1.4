from pathlib import Path
import argparse
from main.mainp import main


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="图像标注工具")
	parser.add_argument('--config', type=Path, default=Path('config.ini'), help='配置文件路径')
	parser.add_argument('--image_list', type=Path, default=Path('image_list.txt'), help='图片列表文件路径')
	args = parser.parse_args()
	main(args.config, args.image_list)