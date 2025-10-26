import pandas as pd
import os
from google import genai
from google.genai.errors import APIError

# --- 配置 ---
# 确保你已经设置了 GEMINI_API_KEY 环境变量
# 如果你没有设置环境变量，可以取消注释下面一行，并替换 YOUR_API_KEY
os.environ["GEMINI_API_KEY"] = "AIzaSyDPrk6-2vNluGA5L9BSndjWQNhCY-lmMmo"

# 要处理的CSV文件名
CSV_FILE = 'working\same_name_tags.csv' 
# 模型名称
MODEL_NAME = 'gemini-2.5-flash'
# 批次大小 (每次API调用处理多少个tag)
BATCH_SIZE = 50 

# --- 初始化 Gemini 客户端 ---
try:
    client = genai.Client()
except Exception as e:
    print(f"初始化 Gemini 客户端失败。请确保设置了有效的 GEMINI_API_KEY。错误: {e}")
    exit()

# --- 辅助函数：调用 Gemini API 进行翻译 ---
def translate_tags_with_gemini(tags: list) -> list:
    """
    调用 Gemini API 翻译一组 Danbooru 标签。

    Args:
        tags: 待翻译的英文标签列表。

    Returns:
        翻译后的中文标签列表，如果API调用失败则返回空列表。
    """
    if not tags:
        return []

    # 构造请求的提示词 (Prompt)
    tags_str = "\n".join(f"- {tag}" for tag in tags)
    
    # 提示词要求：
    # 1. 明确角色：你是Danbooru标签翻译专家。
    # 2. 明确目的：意译，而非直译，要描述内容。
    # 3. 明确格式：使用相同的列表格式返回。
    prompt = f"""
    你是一位专业的图像推理标签翻译专家，专门负责将 Danbooru 风格的英文标签翻译成中文。
    请注意：这些标签是用来描述二次元或游戏图像内容的，**绝对不能直译**，你需要**意译**或**提供一个准确且自然的中文描述**来表达标签所代表的图像元素。

    请严格按照下面的列表格式进行翻译，**只返回翻译结果的列表**，每行对应一个标签的中文描述。

    待翻译标签列表（英文）：
    {tags_str}

    请返回翻译后的中文描述列表：
    """
    
    print(f"-> 正在请求翻译 {len(tags)} 个标签...")
    
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={"temperature": 0.3} # 降低温度以获得更稳定准确的翻译
        )
        
        # 解析返回结果
        # 模型返回的文本是一行一个中文标签，我们按行分割
        translated_texts = [line.strip() for line in response.text.split('\n') if line.strip()]
        
        # 简单检查数量是否一致
        if len(translated_texts) != len(tags):
            print(f"[警告] 标签数量不匹配。请求: {len(tags)}, 响应: {len(translated_texts)}。可能会出现错位。")
        
        return translated_texts
        
    except APIError as e:
        print(f"[错误] Gemini API 调用失败: {e}")
        return [f"[翻译失败: {e}]" for _ in tags] # 返回失败标记，防止数据错位
    except Exception as e:
        print(f"[错误] 翻译过程中发生未知错误: {e}")
        return [f"[翻译失败: {e}]" for _ in tags]

# --- 主处理逻辑 ---
def process_csv_and_translate():
    """读取CSV，批量翻译name，更新right_tag_cn列，并保存。"""
    
    # 1. 读取 CSV
    print(f"正在读取文件: {CSV_FILE}")
    try:
        df = pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        print(f"[错误] 文件未找到: {CSV_FILE}")
        return
    
    # 检查必要的列是否存在
    required_cols = ['name', 'right_tag_cn']
    for col in required_cols:
        if col not in df.columns:
            print(f"[错误] CSV文件缺少必要的列: {col}")
            return

    # 筛选出需要翻译的标签（name非空且right_tag_cn为空或包含[翻译失败]标记的行）
    # 使用 .str.contains 检查是否包含失败标记
    mask = (df['name'].notna()) & (
        (df['right_tag_cn'].isna()) | 
        (df['right_tag_cn'] == '') | 
        (df['right_tag_cn'].astype(str).str.contains(r'\[翻译失败'))
    )
    
    tags_to_translate_df = df[mask].copy()
    
    if tags_to_translate_df.empty:
        print("所有需要的标签都已经翻译完成或 'name' 列为空，无需操作。")
        return

    tags_list = tags_to_translate_df['name'].tolist()
    total_tags = len(tags_list)
    print(f"--- 找到 {total_tags} 个需要翻译的唯一标签。 ---")
    
    all_translated_tags = []
    
    # 2. 批量处理和翻译
    for i in range(0, total_tags, BATCH_SIZE):
        batch = tags_list[i:i + BATCH_SIZE]
        print(f"\n>>>> 正在处理批次 {i//BATCH_SIZE + 1} ({i+1} - {min(i + BATCH_SIZE, total_tags)}) / 总计 {total_tags} 个标签...")
        
        translated_batch = translate_tags_with_gemini(batch)
        all_translated_tags.extend(translated_batch)
        
        # 为了防止API限制，可以考虑在这里添加一个小小的延迟
        import time; time.sleep(1)

    # 3. 将翻译结果回填到 DataFrame
    if len(all_translated_tags) != total_tags:
        print(f"[严重警告] 翻译结果总数与待翻译标签总数不匹配 ({len(all_translated_tags)} vs {total_tags})。请检查API调用。本次操作终止。")
        return
        
    # 将翻译结果赋值回筛选出来的子DataFrame
    tags_to_translate_df['right_tag_cn'] = all_translated_tags
    
    # 将更新后的数据合并回原始 DataFrame (使用index匹配)
    df.loc[mask, 'right_tag_cn'] = tags_to_translate_df['right_tag_cn']

    # 4. 保存回 CSV 文件
    # 为了安全，建议先备份原始文件，或者保存为新的文件名
    # 在代码中临时添加，保存到当前目录
    df.to_csv('working\output.csv', index=False, encoding='utf-8')
    print(f"\n--- 任务完成 ---")
    print(f"成功更新 {total_tags} 行数据。文件已保存至: working\output.csv")

# --- 运行主函数 ---
if __name__ == '__main__':
    process_csv_and_translate()