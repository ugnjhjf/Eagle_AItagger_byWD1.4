from PIL import Image
import numpy as np
import cv2

class ImageUtils:
    """图像预处理工具"""
    @staticmethod
    def fill_transparent(image: Image.Image, color='WHITE'):
        image = image.convert('RGBA')
        new_image = Image.new('RGBA', image.size, color)
        new_image.paste(image, mask=image)
        return new_image.convert('RGB')

    @staticmethod
    def resize(pic: Image.Image, size: int, keep_ratio=True) -> Image.Image:
        if not keep_ratio:
            target_size = (size, size)
        else:
            min_edge = min(pic.size)
            target_size = (
                int(pic.size[0] / min_edge * size),
                int(pic.size[1] / min_edge * size),
            )
        target_size = (target_size[0] & ~3, target_size[1] & ~3)
        return pic.resize(target_size, resample=Image.Resampling.LANCZOS)

    @staticmethod
    def smart_imread(img_path, flag=cv2.IMREAD_UNCHANGED):
        if img_path.suffix == ".gif":
            img = Image.open(img_path)
            img = img.convert("RGB")
            img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        else:
            img = cv2.imread(str(img_path), flag)
        return img

    @staticmethod
    def smart_24bit(img):
        if img.dtype == np.uint16:
            img = (img / 257).astype(np.uint8)
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif img.shape[2] == 4:
            trans_mask = img[:, :, 3] == 0
            img[trans_mask] = [255, 255, 255, 255]
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img

    @staticmethod
    def make_square(img, target_size):
        old_size = img.shape[:2]
        desired_size = max(old_size)
        desired_size = max(desired_size, target_size)
        delta_w = desired_size - old_size[1]
        delta_h = desired_size - old_size[0]
        top, bottom = delta_h // 2, delta_h - (delta_h // 2)
        left, right = delta_w // 2, delta_w - (delta_w // 2)
        color = [255, 255, 255]
        return cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)

    @staticmethod
    def smart_resize(img, size):
        if img.shape[0] > size:
            img = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)
        elif img.shape[0] < size:
            img = cv2.resize(img, (size, size), interpolation=cv2.INTER_CUBIC)
        return img

    @staticmethod
    def preprocess_image(image: Image.Image, target_size: int) -> np.ndarray:
        """标准化预处理"""
        image = ImageUtils.fill_transparent(image)
        arr = np.array(image)[:, :, ::-1]  # RGB to BGR
        arr = ImageUtils.make_square(arr, target_size)
        arr = ImageUtils.smart_resize(arr, target_size)
        return np.expand_dims(arr.astype(np.float32), 0)