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
        self.last_progress = 0
        self.last_update_time = 0
        self.update_interval = 3  # 每3秒更新一次

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

    def _monitor_loop(self):
        last_processed = 0
        last_time = time.time()
        while self.is_running:
            try:
                current_time = time.time()
                # 控制更新频率
                if current_time - self.last_update_time >= self.update_interval:
                    progress = self.dispatcher.get_progress()
                    worker_status = self.pool_manager.monitor_workers()
                    summary = self.result_collector.get_summary()
                    
                    time_diff = current_time - last_time
                    processed_diff = summary['success_count'] - last_processed
                    current_speed = processed_diff / time_diff if time_diff > 0 else 0
                    remaining = progress['remaining']
                    
                    # 只在进度有显著变化或时间间隔到时更新显示
                    if (abs(progress['progress'] - self.last_progress) > 1 or 
                        current_time - self.last_update_time >= self.update_interval):
                        eta_str = self._format_time(remaining / current_speed) if current_speed > 0 else "计算中..."
                        self._display_progress(
                            progress['progress'], current_speed, eta_str, worker_status, summary
                        )
                        self.last_progress = progress['progress']
                        self.last_update_time = current_time
                        last_processed = summary['success_count']
                        last_time = current_time
                
                time.sleep(1)
            except Exception as e:
                # 静默处理监控错误，避免干扰主输出
                time.sleep(5)

    def _display_progress(self, progress: float, current_speed: float, 
                          eta: str, worker_status: Dict, summary: Dict):
        """显示进度信息"""
        bar_length = 40
        filled_length = int(bar_length * progress / 100)
        bar = '#' * filled_length + '-' * (bar_length - filled_length)
        
        # 使用回车符覆盖上一行，而不是换行
        print(f"\r进度: |{bar}| {progress:.1f}% | "
              f"速度: {current_speed:.1f}张/秒 | "
              f"剩余: {eta} | "
              f"进程: {worker_status['active_workers']}/{worker_status['total_workers']} | "
              f"成功: {summary['success_count']} | "
              f"失败: {summary['failure_count']}", end='', flush=True)

    def _format_time(self, seconds: float) -> str:
        """格式化时间显示"""
        if seconds <= 0:
            return "0秒"
        elif seconds < 60:
            return f"{seconds:.0f}秒"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}分{secs}秒"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}时{minutes}分"

    def final_report(self):
        """最终报告，只在主线程调用一次"""
        # 先换行，结束进度条的那一行
        print()
        
        summary = self.result_collector.get_summary()
        total_time = time.time() - self.start_time
        
        print("\n" + "=" * 50)
        print(f"图片总数:     {summary['total_images']:>8}")
        print(f"处理成功:     {summary['success_count']:>8}")
        print(f"处理失败:     {summary['failure_count']:>8}")
        print(f"成功率:       {summary['success_rate']:>7.2f}%")
        print(f"总耗时:       {total_time:>7.2f}秒")
        print(f"平均速度:     {summary['images_per_second']:>7.2f} 张/秒")
        print(f"生成标签总数: {summary['total_tags_generated']:>8}")
        print(f"平均每张标签数: {summary['avg_tags_per_image']:>6.2f}")
        
        failed = self.result_collector.get_failed_images()
        if failed:
            print(f"\n处理失败的图片 ({len(failed)}张):")
            print("-" * 40)
            for f in failed[:5]:
                print(f"  {f['image_path']}")
                print(f"    错误: {f['error']}")
            if len(failed) > 5:
                print(f"  ... 以及其他 {len(failed) - 5} 张")