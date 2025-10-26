import multiprocessing as mp
from pathlib import Path
import time
from typing import List, Dict, Any
from PIL import Image
from tagger import TaggerService
from unified_config import UnifiedConfig, VersionConfig, ModelConfig, TagConfig, ProcessConfig, ReportConfig

class ModelWorker:
    """模型工作进程"""
    def __init__(self, config_dict: Dict[str, Any]):
        # 手动从嵌套字典重建 ProcessConfig, ReportConfig, TagConfig
        # ModelConfig 中的 Path 对象在 to_dict 中被转为 str，需要转回来
        model_config = ModelConfig(
            model_path=Path(config_dict['model']['model_path']),
            tags_path=Path(config_dict['model']['tags_path'])
        )
        # 其他配置 dataclass 可以直接用字典作为关键字参数创建
        tag_config = TagConfig(**config_dict['tag'])
        process_config = ProcessConfig(**config_dict['process'])
        report_config = ReportConfig(**config_dict['report'])
        version_config = VersionConfig(**config_dict['version']) # 假设 VersionConfig 也需要

        # 使用重建的 dataclass 实例初始化 UnifiedConfig
        self.config = UnifiedConfig(
            version=version_config,
            model=model_config,
            tag=tag_config,
            process=process_config,
            report=report_config
        )
        # --- 💥 重点修改部分结束 💥 ---
        
        self.tagger_service = None
        self._load_model()

    def _load_model(self):
        max_retries = self.config.process.max_retries
        retry_count = 0
        while retry_count < max_retries:
            try:
                print(f"工作进程 {mp.current_process().name} 正在加载模型（第 {retry_count + 1}/{max_retries} 次尝试）")
                self.tagger_service = TaggerService(self.config)
                print(f"工作进程 {mp.current_process().name} 模型加载完成")
                return
            except Exception as e:
                retry_count += 1
                print(f"工作进程 {mp.current_process().name} 加载失败: {e}")
                time.sleep(2)
        raise RuntimeError("模型加载失败，已重试多次")

    def process_batch(self, batch_data: List[Dict]) -> List[Dict]:
        """处理批次，只返回标签结果，不更新JSON"""
        results = []
        for item in batch_data:
            image_path = Path(item['image_path'])
            json_path = Path(item['json_path'])
            if not image_path.exists():
                results.append({
                    'image_path': str(image_path),
                    'json_path': str(json_path),
                    'tags': [],
                    'success': False,
                    'error': f'图片未找到: {image_path}'
                })
                continue
            try:
                tags_dict = self.tagger_service.process_single_image(image_path)
                tag_list = list(tags_dict.keys())
                results.append({
                    'image_path': str(image_path),
                    'json_path': str(json_path),
                    'tags': tag_list,
                    'success': True,
                    'error': None
                })
            except Exception as e:
                results.append({
                    'image_path': str(image_path),
                    'json_path': str(json_path),
                    'tags': [],
                    'success': False,
                    'error': f'处理失败: {str(e)}'
                })
        return results

    def unload(self):
        if self.tagger_service:
            self.tagger_service.unload()

def worker_process(config_dict: Dict[str, Any], task_queue: mp.Queue, 
                   result_queue: mp.Queue, worker_id: int):
    worker = None
    try:
        worker = ModelWorker(config_dict)
        print(f"工作进程 {worker_id} 已启动")
        while True:
            task = task_queue.get()
            if task is None:
                break
            batch_id, batch_data = task
            print(f"工作进程 {worker_id} 正在处理批次 {batch_id}")
            start_time = time.time()
            results = worker.process_batch(batch_data)
            processing_time = time.time() - start_time
            result_queue.put({
                'batch_id': batch_id,
                'worker_id': worker_id,
                'results': results,
                'processing_time': processing_time
            })
    except Exception as e:
        print(f"工作进程 {worker_id} 出错: {e}")
        result_queue.put({
            'batch_id': -1,
            'worker_id': worker_id,
            'error': str(e),
            'results': []
        })
    finally:
        if worker:
            worker.unload()
        print(f"工作进程 {worker_id} 已退出")