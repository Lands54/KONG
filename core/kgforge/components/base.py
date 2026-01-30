from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from kgforge.protocols.interfaces import (
    IDescribable, IExtractor, IExpander, IFusion, IOrchestrator, IProcessor, IHalting
)

class BaseAppliance(IDescribable, ABC):
    """
    组件器具基类
    实现 IDescribable 接口，并提供默认参数存储。
    """
    name: str = "base_appliance"
    display_name: str = "基础组件"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @classmethod
    def get_component_spec(cls) -> Dict[str, Any]:
        """默认返回空规范，子类应覆盖"""
        return {
            "id": cls.name,
            "name": cls.display_name,
            "description": "Base appliance class",
            "params": {}
        }


class BaseExtractor(BaseAppliance, IExtractor):
    """抽取器辅助基类"""
    pass


class BaseExpander(BaseAppliance, IExpander):
    """展开器辅助基类"""
    pass


class BaseFusion(BaseAppliance, IFusion):
    """融合器辅助基类"""
    pass


class BaseHalting(BaseAppliance, IHalting):
    """判停策略辅助基类"""
    pass


class BaseProcessor(BaseAppliance, IProcessor):
    """处理器辅助基类"""
    pass


class BaseOrchestrator(BaseAppliance, IOrchestrator):
    """编排器辅助基类 (Motherboard)"""
    pass
