"""
模块接口协议定义 (Component Protocols)
确保所有可插拔模块实现标准接口，支持生命周期管理、动态配置与元数据自述。
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, List, Type

META_REGISTRY = []


class IDescribable(ABC):
    """
    自述接口：使组件能够描述自己的能力和所需的配置项。
    用于前端动态生成 GUI 控件。
    """
    
    @classmethod
    @abstractmethod
    def get_component_spec(cls) -> Dict[str, Any]:
        """
        获取组件规范：描述名称、功能、版本以及可调参数。
        """
        pass
    
    @classmethod
    def __init_subclass__(cls, **kwargs):
        """
        自动注册机制预留
        """
        super().__init_subclass__(**kwargs)


class IConfigurable(ABC):
    """可配置接口：支持运行时热更新参数"""
    
    @abstractmethod
    def update_config(self, params: Dict[str, Any]):
        """
        更新运行时参数。
        """
        pass


class IPreloadable(ABC):
    """可预热接口：执行耗时的预加载操作（如模型权重加载）"""
    
    @abstractmethod
    def preload(self):
        """执行预加载逻辑"""
        pass



class IExtractor(IDescribable, ABC):
    """抽取器协议 (Bottom-Up)"""
    category = "extractors"
    
    @abstractmethod
    def extract(self, text: str) -> Any:
        """从文本抽取并构建图对象"""
        pass


class IExpander(IDescribable, ABC):
    """展开器协议 (Top-Down)"""
    category = "expanders"
    
    @abstractmethod
    def expand_goal(self, goal: str, **kwargs) -> Any:
        """从目标描述构建初始图"""
        pass

    @abstractmethod
    def expand_graph(self, graph: Any, **kwargs) -> Any:
        """基于当前图上下文进行智能扩展"""
        pass


class IFusion(IDescribable, ABC):
    """融合器协议"""
    category = "fusions"
    
    @abstractmethod
    def fuse(self, graph_b: Any, graph_t: Any) -> Any:
        """合并两个图对象"""
        pass


class IHalting(IDescribable, ABC):
    """判停策略协议"""
    category = "haltings"
    
    @abstractmethod
    def should_halt(self, graph: Any, goal: str, **kwargs) -> Any:
        """
        判断是否满足停止条件
        Returns: 建议的决策结果 (HaltingResponse)
        """
        pass


class IProcessor(IDescribable, ABC):
    """单体处理器协议 (例如去重、分片)"""
    category = "processors"
    
    @abstractmethod
    def process(self, graph: Any, **kwargs) -> Any:
        pass


class IOrchestrator(IDescribable, ABC):
    """
    编排器协议 (The Motherboard)
    核心任务是声明“插槽”，并协调组件运行。
    """
    category = "orchestrators"
    
    @classmethod
    @abstractmethod
    def get_required_slots(cls) -> Dict[str, str]:
        """
        声明所需组件的插槽及类型要求。
        """
        pass

    @abstractmethod
    def run(self, goal: str, text: str, **kwargs) -> Any:
        """运行编排逻辑"""
        pass


# 自动发现并注册所有组件协议接口
# 规则：继承自 IDescribable 且 定义了 'category' 属性的类
import inspect
import sys

current_module = sys.modules[__name__]
for name, obj in inspect.getmembers(current_module, inspect.isclass):
    if issubclass(obj, IDescribable) and obj is not IDescribable:
        if hasattr(obj, 'category') and obj.category:
            META_REGISTRY.append(obj)
