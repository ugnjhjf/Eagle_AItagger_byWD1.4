import multiprocessing as mp
from typing import List, Dict, Any
import time
import queue
from manager import worker_process
from unified_config import UnifiedConfig

class ProcessPoolManager:
    """进程池管理器"""
    def __init__(self, config: UnifiedConfig):
        self.config = config
        self.num_processes = config.process.max_workers
        self.task_queue = mp.Queue()
        self.result_queue = mp.Queue()
        self.processes: List[mp.Process] = []
        self.worker_status: Dict[int, Dict] = {}

    def start_workers(self, config_dict: Dict[str, Any]):
        print(f"正在启动 {self.num_processes} 个工作进程...")
        for i in range(self.num_processes):
            process = mp.Process(
                target=worker_process,
                args=(config_dict, self.task_queue, self.result_queue, i),
                name=f"Worker-{i}"
            )
            process.daemon = True
            process.start()
            self.processes.append(process)
            self.worker_status[i] = {
                'status': 'running',
                'processed_tasks': 0,
                'last_activity': time.time(),
                'start_time': time.time()
            }
        print(f"所有 {self.num_processes} 个工作进程已启动")

    def submit_tasks(self, batches: List[Dict]):
        print(f"正在提交 {len(batches)} 个任务批次...")
        for batch in batches:
            task = (batch['batch_id'], batch['images'])
            self.task_queue.put(task)
        for _ in range(self.num_processes):
            self.task_queue.put(None)

    def get_results(self, timeout: float = 60) -> Dict:
        try:
            result = self.result_queue.get(timeout=timeout)
            worker_id = result.get('worker_id')
            if worker_id in self.worker_status:
                self.worker_status[worker_id]['processed_tasks'] += 1
                self.worker_status[worker_id]['last_activity'] = time.time()
            return result
        except queue.Empty:
            self.restart_failed_workers()
            return {'error': '获取结果超时'}

    def monitor_workers(self) -> Dict[str, Any]:
        active_workers = 0
        total_processed = 0
        for worker_id, status in self.worker_status.items():
            if self.processes[worker_id].is_alive():
                active_workers += 1
                total_processed += status['processed_tasks']
                if time.time() - status['last_activity'] > 300:
                    print(f"警告: 工作进程 {worker_id} 可能卡住，最后活动于 {time.time() - status['last_activity']:.0f} 秒前")
        return {
            'total_workers': len(self.processes),
            'active_workers': active_workers,
            'total_processed_tasks': total_processed,
            'worker_details': self.worker_status
        }

    def restart_failed_workers(self):
        for worker_id in range(self.num_processes):
            if not self.processes[worker_id].is_alive():
                print(f"正在重启失效的工作进程 {worker_id}...")
                self.restart_worker(worker_id)

    def restart_worker(self, worker_id: int):
        if worker_id < len(self.processes):
            old_process = self.processes[worker_id]
            if old_process.is_alive():
                old_process.terminate()
                old_process.join(timeout=5)
            new_process = mp.Process(
                target=worker_process,
                args=(self.config.to_dict(), self.task_queue, self.result_queue, worker_id),
                name=f"Worker-{worker_id}-restarted"
            )
            new_process.daemon = True
            new_process.start()
            self.processes[worker_id] = new_process
            self.worker_status[worker_id] = {
                'status': 'restarted',
                'processed_tasks': 0,
                'last_activity': time.time(),
                'start_time': time.time()
            }
            print(f"工作进程 {worker_id} 重启完成")

    def shutdown(self):
        print("正在关闭进程池...")
        for _ in range(self.num_processes):
            try:
                self.task_queue.put(None, timeout=1)
            except:
                pass
        for i, process in enumerate(self.processes):
            if process.is_alive():
                process.join(timeout=10)
                if process.is_alive():
                    print(f"正在强制终止工作进程 {i}")
                    process.terminate()
        print("进程池关闭完成")