import yaml
import os

def load_config(config_path):
    """
    加载配置文件
    :param config_path: 配置文件路径
    :return: 配置字典
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件未找到: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)
