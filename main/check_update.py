import requests
from packaging import version
from typing import Optional
from pathlib import Path
from unified_config import UnifiedConfig

class VersionChecker:
    """版本检查器"""
    def __init__(self, config: UnifiedConfig):
        self.config = config
        self.github_url = 'https://github.com/Ir-Phen/Eagle_AItagger_byWD1.4'

    def get_local_version(self) -> str:
        return self.config.version.version

    def get_remote_version(self) -> tuple[Optional[str], Optional[str]]:
        raw_url = "https://raw.githubusercontent.com/Ir-Phen/Eagle_AItagger_byWD1.4/main/config.ini"
        try:
            response = requests.get(raw_url, timeout=10)
            response.raise_for_status()
            
            # 1. 创建一个临时的配置解析器
            import configparser
            parser = configparser.ConfigParser()
            
            # 2. 从下载的文本内容中读取配置
            # 注意：如果远程配置中的编码不是默认的，可能会有问题，但通常INI文件是UTF-8。
            parser.read_string(response.text) 

            # 稳妥的修复方案：
            temp_config_path = Path('temp_remote_config.ini')
            # 将下载的内容写入临时文件
            with open(temp_config_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
                
            # 然后使用现有的 from_ini_file 方法解析
            remote_config = UnifiedConfig.from_ini_file(temp_config_path)
            
            # 4. 删除临时文件 (可选，推荐)
            temp_config_path.unlink()
            
            return remote_config.version.version, remote_config.version.update_notes
        except Exception as e:
            # 错误信息现在会包含更准确的错误，比如 'No section: 'Model''，
            # 如果远程文件格式正确，则不会报错。
            print(f'获取远程版本失败: {e}')
            return None, None

    def check_for_update(self) -> bool:
        local_version = self.get_local_version()
        remote_version, update_notes = self.get_remote_version()
        if remote_version is None:
            print(f"无法检查更新: {self.github_url}")
            return True
        try:
            if version.parse(remote_version) > version.parse(local_version):
                print(f"\n发现新版本: {remote_version} (当前版本: {local_version})")
                print(f"更新内容: {update_notes}")
                print(f"仓库地址: {self.github_url}")
                choice = input("\n是否继续使用当前版本? (y/n): ").strip().lower()
                if choice == 'y':
                    print("继续运行...\n")
                    return True
                else:
                    print("退出程序，请更新。")
                    exit()
            else:
                print("当前已是最新版本。\n")
                return True
        except version.InvalidVersion as e:
            print(f"无效的版本号: {e}")
            return True