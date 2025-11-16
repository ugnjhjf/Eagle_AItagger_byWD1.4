from typing import List, Dict, Any
import math
from .unified_config import UnifiedConfig

class TaskDispatcher:
    """任务分发器"""
    def __init__(self, config: UnifiedConfig):
        self.config = config
        self.batch_size = config.process.batch_size
        self.total_images = 0
        self.processed_images = 0

    def create_batches(self, image_data: List[Dict]) -> List[Dict]:
        self.total_images = len(image_data)
        batches = []
        batch_count = math.ceil(self.total_images / self.batch_size)
        for i in range(batch_count):
            start_idx = i * self.batch_size
            end_idx = min((i + 1) * self.batch_size, self.total_images)
            batch = {
                'batch_id': i,
                'images': image_data[start_idx:end_idx],
                'total_batches': batch_count
            }
            batches.append(batch)
        print(f"已创建 {batch_count} 个批次，每个批次包含 {self.batch_size} 张图片")
        return batches

    def adjust_batch_size(self, success_rate: float, avg_processing_time: float):
        if success_rate > 0.9 and avg_processing_time < 30:
            new_batch_size = min(self.batch_size * 2, 50)
            if new_batch_size != self.batch_size:
                    print(f"批处理大小从 {self.batch_size} 调整为 {new_batch_size}")
                    self.batch_size = new_batch_size
        elif success_rate < 0.7 or avg_processing_time > 60:
            new_batch_size = max(self.batch_size // 2, 1)
            if new_batch_size != self.batch_size:
                    print(f"批处理大小从 {self.batch_size} 调整为 {new_batch_size}")
                    self.batch_size = new_batch_size

    def get_progress(self) -> Dict[str, Any]:
        progress = 0
        if self.total_images > 0:
            progress = (self.processed_images / self.total_images) * 100
        return {
            'processed': self.processed_images,
            'total': self.total_images,
            'progress': progress,
            'remaining': self.total_images - self.processed_images
        }

    def update_progress(self, batch_size: int):
        self.processed_images += batch_size