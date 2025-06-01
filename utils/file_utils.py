import os
import json
from datetime import datetime

def ensure_dirs():
    """
    @brief 确保所需的目录存在。

    @details
    自动创建 'config' 和 'data' 目录，如果它们尚不存在。
    用于初始化程序运行所需的文件夹结构。
    """
    os.makedirs('config', exist_ok=True)
    os.makedirs('data', exist_ok=True)


def load_json(path, default=None):
    """
    @brief 从指定路径加载 JSON 文件。

    @param path 文件路径
    @param default 文件不存在时返回的默认值，默认为空字典 {}

    @return 成功读取返回解析后的 JSON 对象；若文件不存在或错误，则返回 default。
    """
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default if default is not None else {}


def save_json(path, data):
    """
    @brief 将数据保存为 JSON 文件。

    @param path 文件保存路径
    @param data 要保存的 Python 对象（通常为 dict 或 list）

    @details
    数据将以 UTF-8 编码保存，并使用 4 空格缩进和非 ASCII 字符直写。
    """
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def list_config_ids():
    """
    @brief 获取 config 目录下所有计划配置文件的 ID 列表。

    @return 所有以 `.json` 结尾的文件名（去除扩展名）组成的列表。
    """
    return [f.replace('.json', '') for f in os.listdir('config') if f.endswith('.json')]


def get_today():
    """
    @brief 获取今天的日期字符串。

    @return 当前日期，格式为 "YYYY-MM-DD"。
    """
    return datetime.now().strftime('%Y-%m-%d')
