"""
路径工具
实现“内省原则”：库只关心自己的安装路径，而不强行推算外部项目的根目录。
"""

import os
from typing import Optional

def get_library_root() -> str:
    """
    获取 dynhalting 库的根目录
    """
    # 当前文件在 dynhalting/core/utils/path_utils.py
    # 返回 dynhalting/
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))

def get_resource_path(relative_path: str) -> str:
    """
    获取库内部资源的绝对路径
    """
    return os.path.join(get_library_root(), relative_path)
