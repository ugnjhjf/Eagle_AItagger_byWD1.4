import argparse
from pathlib import Path
import traceback
from unified_config import UnifiedConfig
from task_dispatcher import TaskDispatcher
from process_pool_manager import ProcessPoolManager
from result_collector import ResultCollector
from progress_monitor import ProgressMonitor
from check_update import VersionChecker

def get_image_list_info(img_list_path: Path) -> list:
    with img_list_path.open('r', encoding='utf-8') as f:
        img_paths = [Path(line.strip()).resolve() for line in f if line.strip()]
    return [
        {'image_path': str(img_path), 'json_path': str(img_path.parent / 'metadata.json')}
        for img_path in img_paths
    ]

def main(config_path: Path, img_list_path: Path):
    config = UnifiedConfig.from_ini_file(config_path)
    if not config.validate():
        print("配置验证失败")
        return

    print(f"模型路径: {config.model.model_path}")
    print(f"标签路径: {config.model.tags_path}")
    print(f"工作进程数: {config.process.max_workers}")
    print(f"批处理大小: {config.process.batch_size}")
    print(f"阈值: {config.tag.threshold}")

    checker = VersionChecker(config)
    checker.check_for_update()

    image_data = get_image_list_info(img_list_path)
    print(f"找到图片数量: {len(image_data)}")
    if not image_data:
        print("没有需要处理的图片")
        return

    dispatcher = TaskDispatcher(config)
    pool_manager = ProcessPoolManager(config)
    result_collector = ResultCollector(config)

    batches = dispatcher.create_batches(image_data)

    worker_config = config.to_dict()
    pool_manager.start_workers(worker_config)

    progress_monitor = ProgressMonitor(dispatcher, pool_manager, result_collector)
    progress_monitor.start()

    try:
        pool_manager.submit_tasks(batches)
        completed_batches = 0
        total_batches = len(batches)
        while completed_batches < total_batches:
            result = pool_manager.get_results(timeout=120)
            if 'error' in result:
                print(f"获取结果出错: {result['error']}")
                continue
            result_collector.add_result(result)
            completed_batches += 1
            batch_size = len(result.get('results', []))
            dispatcher.update_progress(batch_size)
            if completed_batches % 5 == 0:
                summary = result_collector.get_summary()
                dispatcher.adjust_batch_size(summary['success_rate'] / 100, summary['total_processing_time'] / completed_batches if completed_batches > 0 else 0)

        # 结果合并后统一更新JSON
        result_collector.update_json_files()

        print("\n正在生成报告...")
        result_collector.generate_report()
        progress_monitor.final_report()

        print("\n=== 完成 ===")
        summary = result_collector.get_summary()
        print(f"处理速度: {summary['images_per_second']:.2f} 图片/秒")

    except KeyboardInterrupt:
        print("\n程序被中断")
    except Exception as e:
        print(f"错误: {e}")
        traceback.print_exc()
    finally:
        progress_monitor.stop()
        pool_manager.shutdown()
        print("结束")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Image Tagger")
    parser.add_argument('--config', type=Path, default=Path('config.ini'), help='Config path')
    parser.add_argument('--image_list', type=Path, default=Path('image_list.txt'), help='Image list path')
    args = parser.parse_args()
    main(args.config, args.image_list)