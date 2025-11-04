## Eagle AI 图像标注工具

基于 WD14 模型的 Eagle 图像自动标注工具，支持多进程 GPU 加速推理和中文标签。

### 版本 4.0.0 更新说明

- ✅ 字典已完成全部汉化

- ✅ 支持多进程推理，自动管理推理任务

- ✅ 实时进度监控

#### 4.0.0 版本前生成的英文标签更新方式

如需将之前版本生成的英文标签更新为中文标签，请使用 `uptags.py` 工具（详见工具说明）。

注意：默认旧代码 `_` 被转义为了 ` `，如果旧代码是下划线版本，注释151行 `df['name'] = df['name'].str.replace('_', ' ')`

## 环境需求

- **GPU**: NVIDIA GPU (推荐 4GB+ 显存)

- **Python**: 3.8+

- **CUDA**: 12.9 ([下载地址](https://developer.download.nvidia.com/compute/cuda/12.9.0/local_installers/cuda_12.9.0_576.02_windows.exe))

- **cuDNN**: 9.10.1 ([下载地址](https://developer.download.nvidia.com/compute/cudnn/redist/cudnn/windows-x86_64/cudnn-windows-x86_64-9.10.1.4_cuda12-archive.zip))

- **VC_redist.x64**: ([下载地址](https://aka.ms/vs/17/release/vc_redist.x64.exe))

### GPU 推理配置

1. 安装 CUDA 12.9

2. 安装 cuDNN 9.10.1（将解压文件夹内容复制到 CUDA 安装目录，通常是 `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.9`）

3. 安装 VC_redist.x64

4. [安装教程视频](https://www.bilibili.com/video/BV116eBefETi/)

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 下载模型

从支持的模型列表中选择模型，下载到 `./model` 目录并重命名为对应的模型名称：
    
    - 示例：./model/swinv2-v3

**支持的模型列表：**

- **推荐模型**:
  
  - [swinv2-v3](https://huggingface.co/SmilingWolf/wd-swinv2-tagger-v3/tree/main) - 大多数情况推荐
  
  - [eva02-large-v3](https://huggingface.co/SmilingWolf/wd-eva02-large-tagger-v3/tree/main) - 精度更高，但资源消耗更大

- **其他模型**:
  
  - [convnext-v3](https://huggingface.co/SmilingWolf/wd-convnext-tagger-v3/tree/main)
  
  - [convnextv2-v2](https://huggingface.co/SmilingWolf/wd-v1-4-convnextv2-tagger-v2/tree/main)
 
  - [vit-large-v3](https://huggingface.co/SmilingWolf/wd-vit-large-tagger-v3/tree/main)
  
  - [更多模型...](#支持的模型列表)

**镜像站**: https://hf-mirror.com/SmilingWolf/

### 3. 准备图片列表

从 Eagle 选择需要标注的图片，右键选择 **复制文件路径** (快捷键 `Ctrl+Alt+C`)，将路径粘贴到 `image_list.txt`：

```
E:\动画与设计资源库.library\images\MAQGISQ1ELX97.info\124956717_p0.png
E:\动画与设计资源库.library\images\MAQGISQ1N6OHU.info\124719914_p0.png
E:\动画与设计资源库.library\images\MAQGISQ1Z8PST.info\124086849_p0.png
```

### 4. 配置参数

编辑 `config.ini` 文件：

```ini
[Model]
model_path = ./model/swinv2-v3.onnx  ; 模型文件路径
tags_path = ./csv/Tags-cn_2024_ver-1.0.csv  ; 标签字典路径

[Tag]
threshold = 0.5  ; 置信度阈值
use_chinese_name = True  ; 使用中文标签
```

### 5. 运行程序

运行 `run.ps1`

或运行 `main/main.py`

## 配置文件详解

### [Version] - 版本信息

**请勿修改此部分**

- `version`: 版本号

- `update_notes`: 版本更新说明

### [Model] - 模型配置

- `model_path`: 推理模型路径（相对路径）

- `tags_path`: 标签字典路径（相对路径）

### [Tag] - 标签处理

- `threshold`: **置信度阈值** (范围 0-1，默认 0.5)

- `replace_underscore`: 是否将下划线替换为空格（4.1版本计划删除）

- `underscore_excludes`: 不替换下划线的标签列表（4.1版本计划删除）

- `escape_tags`: 是否转义特殊字符（4.1版本计划删除）

- `use_chinese_name`: **是否使用中文标签名称**

- `additional_tags`: 强制添加的标签（逗号分隔）

- `exclude_tags`: 强制排除的标签（逗号分隔）

- `sort_alphabetically`: 是否按字母顺序排序（默认按置信度降序）

### [Json] - JSON 输出配置

- `is_creat_image_info_csv`: 是否创建 image_info.csv（4.1版本计划删除）

- `add_write_mode`: 标签写入模式 - `True`: 追加写入, `False`: 覆盖写入

### [Process] - 进程配置

- `max_workers`: **工作进程数**（根据 GPU 显存调整）

  - Eva02 模型 (1.5GB): 6G显存:2进程, 8G显存:3进程（推荐保留2G空闲显存）

- `batch_size`: 批处理大小（自动调整，无需手动设置）

- `max_retries`: 失败重试次数

- `checkpoint_interval`: 检查点间隔

## 支持的模型列表

**仅支持wd类的模型，db类的不支持**

[convnext-v3](https://huggingface.co/SmilingWolf/wd-convnext-tagger-v3/tree/main) | [convnextv2-v2](https://huggingface.co/SmilingWolf/wd-v1-4-convnextv2-tagger-v2/tree/main) | [convnext-v2](https://huggingface.co/SmilingWolf/wd-v1-4-convnext-tagger-v2/tree/main) | [convnext](https://huggingface.co/SmilingWolf/wd-v1-4-convnext-tagger/tree/main)

[swinv2-v2](https://huggingface.co/SmilingWolf/wd-v1-4-swinv2-tagger-v2/tree/main) | [swinv2-v3](https://huggingface.co/SmilingWolf/wd-swinv2-tagger-v3/tree/main)

[vit-large-v3](https://huggingface.co/SmilingWolf/wd-vit-large-tagger-v3/tree/main) | [vit-v3](https://huggingface.co/SmilingWolf/wd-vit-tagger-v3/tree/main) | [vit-v2](https://huggingface.co/SmilingWolf/wd-v1-4-vit-tagger-v2/tree/main) | [vit](https://huggingface.co/SmilingWolf/wd-v1-4-vit-tagger/tree/main)

[moat-v2](https://huggingface.co/SmilingWolf/wd-v1-4-moat-tagger-v2/tree/main)

[eva02-large-v3](https://huggingface.co/SmilingWolf/wd-eva02-large-tagger-v3/tree/main)

镜像站：https://hf-mirror.com/SmilingWolf/

## 故障排除

### 常见问题

**1. 模型加载失败**

- 检查模型文件路径是否正确

- 确认模型文件完整无损

- 验证 CUDA 和 cuDNN 安装

**2. GPU 内存不足**

- 减少 `max_workers` 数量

- 关闭其他占用 GPU 的程序

- 使用较小模型（如 swinv2-v3）

**3. 图片处理失败**

- 检查图片路径是否正确

- 确认图片文件没有损坏

- 验证图片格式支持

**4. 标签生成异常**

- 检查标签字典文件

- 调整置信度阈值

- 验证配置参数

## tag数据集

部分汉化：[NGA阿巧](https://ngabbs.com/read.php?tid=33869519)

    ./csv/人名tag.xlsx

    ./csv/中文化danbooru-tag对照表-词性对AI用优化版-Editor阿巧.xlsx

阿巧未汉化的5630条：在 4.0.0 已经全部汉化完成。

原始数据集：Danbooru2024

    ./csv/selected_tags.csv

## 引用

代码核心模块前身： [秋叶lora训练器](https://github.com/Akegarasu/lora-scripts)
