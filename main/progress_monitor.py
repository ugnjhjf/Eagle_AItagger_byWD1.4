import time
from typing import Dict, Any
import threading

class ProgressMonitor:
    """进度监控器"""
    def __init__(self, dispatcher, pool_manager, result_collector):
        self.dispatcher = dispatcher
        self.pool_manager = pool_manager
        self.result_collector = result_collector
        self.start_time = time.time()
        self.is_running = False
        self.monitor_thread = None

    def start(self):
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print("进度监控已启动")

    def stop(self):
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("进度监控已停止")

    def _monitor_loop(self):
        last_processed = 0
        last_time = time.time()
        while self.is_running:
            try:
                progress = self.dispatcher.get_progress()
                worker_status = self.pool_manager.monitor_workers()
                summary = self.result_collector.get_summary()
                current_time = time.time()
                time_diff = current_time - last_time
                processed_diff = summary['success_count'] - last_processed
                current_speed = processed_diff / time_diff if time_diff > 0 else 0
                remaining = progress['remaining']
                eta_str = self._format_time(remaining / current_speed) if current_speed > 0 else "计算中..."
                self._display_progress(
                    progress['progress'], current_speed, eta_str, worker_status, summary
                )
                last_processed = summary['success_count']
                last_time = current_time
                time.sleep(2)
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(5)

    def _display_progress(self, progress: float, current_speed: float, 
                          eta: str, worker_status: Dict, summary: Dict):
        bar_length = 30
        filled_length = int(bar_length * progress / 100)
        bar = '█' * filled_length + '─' * (bar_length - filled_length)
        print(f"\r进度: |{bar}| {progress:.1f}% "
              f"速度: {current_speed:.1f} 张/秒 "
              f"预计剩余时间: {eta} "
              f"工作进程: {worker_status['active_workers']}/{worker_status['total_workers']} "
              f"成功率: {summary['success_rate']:.1f}%", end='', flush=True)

    def _format_time(self, seconds: float) -> str:
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds / 60:.0f}m"
        else:
            return f"{seconds / 3600:.1f}h"

    def final_report(self):
        summary = self.result_collector.get_summary()
        total_time = time.time() - self.start_time
        print("\n" + "=" * 60)
        print("处理完成！")
        print("=" * 60)
        print(f"图片总数: {summary['total_images']}")
        print(f"处理成功: {summary['success_count']}")
        print(f"处理失败: {summary['failure_count']}")
        print(f"成功率: {summary['success_rate']:.2f}%")
        print(f"总耗时: {total_time:.2f}秒")
        print(f"平均速度: {summary['images_per_second']:.2f} 张/秒")
        print(f"生成标签总数: {summary['total_tags_generated']}")
        print(f"平均每张标签数: {summary['avg_tags_per_image']:.2f}")
        failed = self.result_collector.get_failed_images()
        if failed:
            print(f"\n处理失败的图片 ({len(failed)}):")
            for f in failed[:5]:
                print(f"  - {f['image_path']}")
            if len(failed) > 5:
                print(f"  ... 以及其他 {len(failed) - 5} 张")