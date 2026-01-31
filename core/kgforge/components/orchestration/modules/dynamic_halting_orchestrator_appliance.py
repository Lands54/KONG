from typing import Any, Dict
from kgforge.components.base import BaseOrchestrator
from kgforge.components.orchestration.utils.dynamic_halting_core import DynamicHaltingCore

class DynamicHaltingOrchestratorAppliance(BaseOrchestrator):
    """
    动态判停编排器具 (System Integration Wrapper)
    """
    name = "dynamic_halting"
    display_name = "动态判停闭环编排器"

    def __init__(self, config: Dict[str, Any] = None, **kwargs):
        mapped_config = (config or {}).copy()
        mapped_config.update(kwargs)
        super().__init__(mapped_config)
        
        # 保存注入的组件实例
        self.extractor = kwargs.get("extractor")
        self.expander = kwargs.get("expander")
        self.fusion = kwargs.get("fusion")
        self.halting = kwargs.get("halting")
        
        self.core = None

    @classmethod
    def get_required_slots(cls) -> Dict[str, str]:
        """声明所需组件的插槽及类型要求"""
        return {
            "extractor": "IExtractor",
            "expander": "IExpander",
            "fusion": "IFusion",
            "halting": "IHalting"
        }

    @classmethod
    def get_component_spec(cls) -> Dict[str, Any]:
        """获取组件规范"""
        return {
            "id": "dynamic_halting",
            "name": "动态判停闭环编排器",
            "slots": {
                "extractor": "IExtractor",
                "expander": "IExpander",
                "fusion": "IFusion",
                "halting": "IHalting"
            },
            "description": "结合Bottom-Up证据驱动与Top-Down目标驱动的动态判停编排器，支持递归图构建和智能判停决策",
            "params": {
                "max_depth": {
                    "type": "integer",
                    "default": 3,
                    "description": "最大递归深度"
                },
                "max_nodes": {
                    "type": "integer",
                    "default": 50,
                    "description": "最大节点数"
                },
                "max_iterations": {
                    "type": "integer",
                    "default": 10,
                    "description": "最大迭代次数"
                }
            }
        }

    def run(self, goal: str, text: str, verbose: bool = True, **kwargs) -> Any:
        """
        运行编排流程
        
        Args:
            goal: 目标/Query
            text: 输入文本
            verbose: 是否输出详细日志
        """
        # 懒初始化核心逻辑，确保组件已就绪
        if not self.core:
            # 优先使用 run 时传入的 kwargs 覆盖初始化参数（如果有）
            extractor = kwargs.get("extractor") or self.extractor
            expander = kwargs.get("expander") or self.expander
            fusion = kwargs.get("fusion") or self.fusion
            halting = kwargs.get("halting") or self.halting
            
            if not all([extractor, expander, fusion, halting]):
                raise ValueError("DynamicHalting 未完整配置所需组件 (extractor, expander, fusion, halting)")

            # 过滤掉已明确传递的组件参数，避免 **self.config 展开时造成重复参数错误
            core_config = self.config.copy()
            for key in ["extractor", "expander", "fusion", "halting"]:
                core_config.pop(key, None)

            self.core = DynamicHaltingCore(
                extractor=extractor,
                expander=expander,
                fusion=fusion,
                halting=halting,
                **core_config
            )

        return self.core.run(goal=goal, text=text, verbose=verbose, check_cancellation=self.check_cancellation, **kwargs)
