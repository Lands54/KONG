"""
Dynamic Halting Research Framework
算法引擎组件库 - 闭环本体语义抽取系统
"""

__version__ = "0.1.0"

# 1. 暴露基础数据结构 (Basic Data Structures)
from kgforge.models import Graph, Node, Edge, ExperimentResult, HaltingDecision, HaltingMode

# 2. 暴露生命周期与扩展协议 (Protocols)
from kgforge.protocols import (
    IExtractor, IExpander, IProcessor, IFusion, 
    IOrchestrator, IPreloadable, IConfigurable
)

# 3. 暴露日志工具
from kgforge.utils import get_logger

__all__ = [
    "Graph", "Node", "Edge", "ExperimentResult", "HaltingDecision", "HaltingMode",
    "IExtractor", "IExpander", "IProcessor", "IFusion", 
    "IOrchestrator", "IPreloadable", "IConfigurable",
    "get_logger"
]
