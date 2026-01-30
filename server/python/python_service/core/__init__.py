"""
Engine Core
后端核心管理层：包含组件引擎、通用工厂与能力框架。
"""

from .engine import engine
from .factory import UnifiedFactory
from .capability import CapabilityManager

__all__ = [
    "engine",
    "UnifiedFactory",
    "CapabilityManager"
]
