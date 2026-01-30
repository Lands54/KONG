"""
配置加载器
负责加载服务器的基础运行配置，如环境、日志等级等。
不再包含任何关于具体算法组件的逻辑。
"""

import yaml
import os
from typing import Dict, Any, Optional

def load_config_file(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载指定的 YAML 配置文件
    """
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), 'modules.yaml')
    
    if not os.path.exists(config_path):
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config or {}
    except Exception:
        return {}

# 全局配置缓存
_config_cache: Optional[Dict[str, Any]] = None
_config_mtime: Optional[float] = None
_config_path: str = os.path.join(os.path.dirname(__file__), 'modules.yaml')

def get_config() -> Dict[str, Any]:
    """获取缓存的全局配置"""
    global _config_cache, _config_mtime
    current_mtime = os.path.getmtime(_config_path) if os.path.exists(_config_path) else None
    
    if _config_cache is None or _config_mtime != current_mtime:
        _config_cache = load_config_file(_config_path)
        _config_mtime = current_mtime
    
    return _config_cache

def reload_config() -> Dict[str, Any]:
    """强制重新加载配置"""
    global _config_cache, _config_mtime
    _config_cache = load_config_file(_config_path)
    _config_mtime = os.path.getmtime(_config_path) if os.path.exists(_config_path) else None
    return _config_cache
