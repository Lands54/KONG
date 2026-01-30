"""
通用工具常量 (Utility Constants)
仅包含与算法逻辑无关的基础设施配置（如日志）。
算法相关的默认值应由各组件（Components）自行管理。
"""

# 基础日志配置
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
