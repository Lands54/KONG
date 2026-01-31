"""
统一日志系统
替换所有 print() 为标准的 logging，并提供数据持久化调试服务
"""

import logging
import sys
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict
from .constants import DEFAULT_LOG_LEVEL, DEFAULT_LOG_FORMAT

# 确保默认日志目录存在
DEFAULT_LOG_DIR = Path("logs")
DEFAULT_LOG_DIR.mkdir(exist_ok=True)

class DataProfiler:
    """
    数据调试服务 (Data Profiler Service)
    用于将运行时产生的复杂数据（JSON, Graph, Prompt等）即时写入文件，便于排查问题。
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, output_dir: str = "logs/debug_snapshots"):
        """
        初始化数据记录器
        Args:
            output_dir: 数据存储目录，默认为 logs/debug_snapshots
        """
        if not hasattr(self, 'initialized'):
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.initialized = True

    def record(self, name: str, data: Any, sub_dir: str = "", extension: str = "json") -> str:
        """
        记录数据到文件
        Args:
            name: 文件名标识（不用带后缀）
            data: 要记录的数据
            sub_dir: 可选的子目录（例如 'orchestrator/Trace'）
            extension: 文件后缀，默认 json

        Returns:
            保存的文件绝对路径
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19] # up to ms
            
            # 处理子目录
            target_dir = self.output_dir
            if sub_dir:
                target_dir = target_dir / sub_dir
                target_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{timestamp}__{name}.{extension}"
            file_path = target_dir / filename

            with open(file_path, "w", encoding="utf-8") as f:
                if extension.lower() == "json":
                    if isinstance(data, str):
                         # Try to parse if it is a stringified json to format it nicily
                        try:
                            parsed = json.loads(data)
                            json.dump(parsed, f, ensure_ascii=False, indent=2, default=str)
                        except:
                            f.write(data)
                    else:
                        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
                else:
                    f.write(str(data))
            
            return str(file_path.absolute())
        except Exception as e:
            # 降级处理：仅打印错误，不中断主流程
            sys.stderr.write(f"[DataProfiler] Failed to save {name}: {e}\n")
            return ""

# 单例实例
profiler = DataProfiler()

# 全局 Handlers (如 Telemetry)，会自动附加到所有通过 setup_logger 创建的 logger
_GLOBAL_HANDLERS = []

def register_global_handler(handler: logging.Handler):
    """
    注册一个全局 Handler，它会被添加到：
    1. 所有未来通过 setup_logger 创建的 logger
    2. 所有已经存在的、且名字以 'kgforge' 开头的 logger
    """
    if handler not in _GLOBAL_HANDLERS:
        _GLOBAL_HANDLERS.append(handler)
        
        # 追溯既往：给所有已存在的 logger 补票
        for name, logger in logging.Logger.manager.loggerDict.items():
            if isinstance(logger, logging.Logger) and name.startswith("kgforge"):
                # 避免重复添加
                if handler not in logger.handlers:
                    logger.addHandler(handler)

def setup_logger(
    name: str,
    level: Optional[str] = None,
    format_string: Optional[str] = None,
    log_to_file: bool = False,
    log_filename: str = "system.log"
) -> logging.Logger:
    """
    设置并返回配置好的 logger
    
    Args:
        name: logger 名称（通常是 __name__）
        level: 日志级别（默认从环境变量或常量读取）
        format_string: 日志格式字符串
        log_to_file: 是否输出到文件
        log_filename: 文件名（如果启用会有 logs/ 前缀）
        
    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 设置日志级别
    log_level = level or DEFAULT_LOG_LEVEL
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # 设置格式
    formatter = logging.Formatter(
        format_string or DEFAULT_LOG_FORMAT,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 1. 创建控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logger.level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 2. (可选) 创建文件 handler
    if log_to_file:
        try:
            file_path = DEFAULT_LOG_DIR / log_filename
            file_handler = logging.FileHandler(file_path, encoding='utf-8')
            file_handler.setLevel(logger.level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            sys.stderr.write(f"Failed to setup file logging for {name}: {e}\n")

    # 3. 添加全局 Handlers (如 Telemetry)
    for h in _GLOBAL_HANDLERS:
        if h not in logger.handlers:
            logger.addHandler(h)

    # 防止日志传播到根 logger
    logger.propagate = False
    
    return logger

class TelemetryAdapter(logging.LoggerAdapter):
    """
    支持遥测数据的 Logger Adapter
    增加 telemetry() 方法，将结构化数据通过 extra 字段传递给 Handler
    """
    def process(self, msg, kwargs):
        # 修复: 默认的 process 会简单覆盖 extra，导致 telemetry 参数丢失
        # 我们必须手动合并 self.extra 和 kwargs['extra']
        extra = self.extra.copy()
        if 'extra' in kwargs:
            extra.update(kwargs['extra'])
        kwargs['extra'] = extra
        return msg, kwargs

    def telemetry(self, data: Dict[str, Any], level: int = logging.INFO):
        """
        发送遥测事件
        Args:
           data: 结构化数据 (如 {"node_count": 100, "stage": "G_B"})
           level: 日志级别 (默认 INFO)
        """
        # 1. 发送日志事件 (用于 WebSocket 广播)
        self.log(level, "TELEMETRY_EVENT", extra={"telemetry": data})
        
        # 2. 尝试更新上下文中的持久化 Stats (用于保存到 DB)
        try:
            from python_service.core.context import update_current_stats
            if "intermediate_stats" in data:
                update_current_stats(data["intermediate_stats"])
        except ImportError:
            pass # 如果不在 server 坏境运行 (例如本地脚本)，忽略 context 更新

def get_logger(name: str) -> TelemetryAdapter:
    """
    获取 logger（如果已存在则返回，否则创建默认）
    返回 TelemetryAdapter 增强版实例
    
    Args:
        name: logger 名称
        
    Returns:
        TelemetryAdapter 实例
    """
    logger = setup_logger(name, log_to_file=True) # 默认开启文件日志以便调试
    return TelemetryAdapter(logger, {})
