import os
import glob
import json
from pathlib import Path
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import threading
import shutil

def get_eagle_library_path():
    """
    获取并验证 Eagle 资源库的路径。

    验证结构：
    路径下必须包含以下子文件夹和文件：
    - \backup (文件夹)
    - \images (文件夹)
    - actions.json (文件)
    - metadata.json (文件)
    - mtime.json (文件)
    - saved-filters.json (文件)
    - tags.json (文件)

    如果路径结构不正确，会要求用户重新输入。
    """

    # 定义 Eagle 资源库应包含的文件夹和文件
    REQUIRED_DIRS = ['backup', 'images']
    REQUIRED_FILES = [
        'actions.json',
        'metadata.json',
        'mtime.json',
        'saved-filters.json',
        'tags.json'
    ]

    while True:
        # 1. 获取用户输入的路径
        input_path = input("请输入 Eagle 资源库的路径 (例如: D:\\默认资源库.Library): ")
        library_path = Path(input_path.strip())

        # 2. 检查路径是否存在且是一个目录
        if not library_path.is_dir():
            print(f"错误：路径 '{library_path}' 不存在或不是一个有效的目录。请重试。")
            continue

        # 3. 验证所需的子文件夹和文件
        is_valid = True
        missing_items = []

        # 检查必需的子文件夹
        for d in REQUIRED_DIRS:
            if not (library_path / d).is_dir():
                is_valid = False
                missing_items.append(f"缺少文件夹：{d}")

        # 检查必需的文件
        for f in REQUIRED_FILES:
            if not (library_path / f).is_file():
                is_valid = False
                missing_items.append(f"缺少文件：{f}")

        # 4. 根据验证结果决定是否跳出循环
        if is_valid:
            print(f"\nEagle 资源库路径：{library_path}")
            return str(library_path)  # 返回路径字符串
        else:
            print(f"\n错误：输入的路径 '{library_path}' 结构不符合 Eagle 资源库。")
            print("缺少以下必需的文件或文件夹：")
            for item in missing_items:
                print(f"- {item}")
            print("请重新输入。\n")

def process_json(json_file, tag_map):
    """
    处理单个 JSON 文件的函数，更新标签。
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        original_tags = data.get("tags", [])
        updated_tags = []
        tags_updated = False
        changed_tags = []  # 记录发生变化的标签
        unmatched_tags = []  # 记录未匹配的标签
        
        # 更新标签
        for tag in original_tags:
            if tag in tag_map:
                new_tag = tag_map[tag]
                if new_tag not in updated_tags:  # 避免重复标签
                    updated_tags.append(new_tag)
                tags_updated = True
                changed_tags.append(f"{tag} -> {new_tag}")  # 记录变化
            else:
                unmatched_tags.append(tag)  # 记录未匹配的标签
                if tag not in updated_tags:  # 避免重复标签
                    updated_tags.append(tag)
        
        # 调试信息：如果有标签但没匹配到映射
        if original_tags and not tags_updated:
            print(f"\n文件 {os.path.basename(json_file)} 有标签但未匹配:")
            print(f"  原标签: {original_tags}")
            print(f"  未匹配: {unmatched_tags}")

        # 如果有标签被更新，则保存文件
        if tags_updated:
            data["tags"] = updated_tags
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            
            # 构建结果消息，包含变化的标签
            change_info = f"标签转换: {', '.join(changed_tags)}" if changed_tags else "无具体变化"
            return True, json_file, f"标签已更新: {len(original_tags)} -> {len(updated_tags)} | {change_info}"
        else:
            return True, json_file, "无标签需要更新"
            
    except Exception as e:
        return False, json_file, f"处理出错: {e}"

def main():
    # 验证资源库结构
    eagle_library_path = get_eagle_library_path()

    # 使用os.walk()获取images路径下所有的json文件
    print("获取json文件列表中……等待……")
    images_dir = os.path.join(eagle_library_path, "images")
    json_files = []
    files_scanned_count = 0  # 文件扫描计数器
    progress_interval = 1000 # 打印进度的间隔

    print(f"开始扫描目录: {images_dir}")

    for root, dirs, files in os.walk(images_dir):
        for file in files:
            files_scanned_count += 1 # 每找到一个文件就计数

            # 检查是否到达打印进度的时机
            if files_scanned_count % progress_interval == 0:
                # 使用 \r 和 end="" 来实现单行刷新显示进度，不换行
                print(f"\r当前已扫描文件数: {files_scanned_count}", end="")

            if file.endswith(".json"):
                json_files.append(os.path.join(root, file))
    print(f"\r总共扫描了 {files_scanned_count} 个文件。")
    print(f"共找到 {len(json_files)} 个 JSON 文件。")

    # 读取csv建立映射表
    tag_map = {}
    csv_path = r"csv\Tags-cn_2024_ver-1.0.csv"
    
    try:
        df = pd.read_csv(csv_path)
        
        # 创建映射字典，处理可能的NaN值
        df['name'] = df['name'].str.replace('_', ' ')
        tag_map = df.set_index('name')['right_tag_cn'].to_dict()
        # 过滤掉NaN值
        tag_map = {k: v for k, v in tag_map.items() if pd.notna(k) and pd.notna(v)}
        
        print(f"成功加载 {len(tag_map)} 个标签映射")
        
        # 显示前几个映射示例
        print("标签映射示例:")
        for i, (old_tag, new_tag) in enumerate(list(tag_map.items())[:5]):
            print(f"  {old_tag} -> {new_tag}")
        if len(tag_map) > 5:
            print("  ...")
            
    except Exception as e:
        print(f"读取 CSV 文件失败: {e}")
        return

    # 在处理前添加统计
    all_tags_in_library = set()
    for json_file in json_files[:1000]:  # 抽样检查前1000个文件
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            all_tags_in_library.update(data.get("tags", []))
        except Exception as e:
            print(f"读取文件 {json_file} 时出错: {e}")
    print(f"资源库中的唯一标签数量: {len(all_tags_in_library)}")
    print(f"映射表覆盖率: {len(set(tag_map.keys()) & all_tags_in_library)}/{len(all_tags_in_library)}")

    # 确认是否继续
    confirm = input(f"\n即将检查 {len(json_files)} 个文件的标签，是否继续? (y/n): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        return

    # 根据cpu，新建多线程池
    max_workers = os.cpu_count() or 4
    print(f"使用 {max_workers} 个线程处理 JSON 文件。")
    
    # 用于统计的变量
    processed_count = 0
    success_count = 0
    lock = threading.Lock()
    
    def update_progress(result):
        nonlocal processed_count, success_count
        with lock:
            processed_count += 1
            if result[0]:  # 如果处理成功
                success_count += 1
            
            # 显示进度
            progress = processed_count / len(json_files) * 100
            print(f"\r处理进度: {processed_count}/{len(json_files)} ({progress:.1f}%) - 成功: {success_count}", end="")
            
            # 如果处理成功且有标签更新，显示转换信息
            if result[0] and "标签已更新" in result[2]:
                print(f"\n文件: {os.path.basename(result[1])}")
                print(f"  {result[2]}")
            # 如果处理失败，显示错误信息
            elif not result[0]:
                print(f"\n错误: {result[1]} - {result[2]}")
    
    print("开始处理 JSON 文件...")
    
    # 使用线程池处理文件
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        futures = [
            executor.submit(process_json, json_file, tag_map) 
            for json_file in json_files
        ]
        
        # 处理完成的任务
        for future in futures:
            try:
                result = future.result()
                update_progress(result)
            except Exception as e:
                with lock:
                    processed_count += 1
                    print(f"\n处理任务时发生异常: {e}")
    
    print(f"\n\n处理完成!")
    print(f"总文件数: {len(json_files)}")
    print(f"成功处理: {success_count}")
    print(f"失败: {len(json_files) - success_count}")
    
if __name__ == "__main__":
    main()