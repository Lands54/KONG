from typing import Any, Dict
from kgforge.components.halting.utils.halting_module import HaltingModule
from kgforge.models import Graph
from kgforge.models.enums import HaltingDecision, HaltingResponse
from kgforge.components.base import BaseHalting

class RuleBasedHaltingAppliance(BaseHalting):
    """
    基于规则的判停器具
    """
    name = "rule_based"
    display_name = "规则判停器"

    def __init__(self, config: Dict[str, Any] = None, **kwargs):
        # 参数合并
        mapped_config = (config or {}).copy()
        mapped_config.update(kwargs)
        super().__init__(mapped_config)
        
        self.halting = HaltingModule(
            mode=self.config.get("mode", "RULE_BASED"),
            max_depth=self.config.get("max_depth", 3),
            max_nodes=self.config.get("max_nodes", 50),
            max_iterations=self.config.get("max_iterations", 10)
        )

    def should_halt(self, graph: Graph, goal: str, **kwargs) -> HaltingResponse:
        """实现 IHalting 接口"""
        depth = kwargs.get("depth", 0)
        iteration = kwargs.get("iteration", 0)
        
        # 1. 评估节点
        self.halting.evaluate_graph(graph, goal=goal, depth=depth, iteration=iteration)
        
        # 2. 全局判停
        return self.halting.should_halt_global(
            graph=graph,
            goal=goal,
            depth=depth,
            iteration=iteration
        )

    def evaluate_graph(self, graph: Graph, current_state: Dict[str, Any]) -> Graph:
        """实现 IHalting 接口的评估方法"""
        return self.halting.evaluate_graph(graph, current_state)

    @classmethod
    def get_component_spec(cls) -> Dict[str, Any]:
        """获取组件规范"""
        return {
            "id": "rule_based",
            "name": "规则判停器",
            "description": "基于深度、节点数等硬性规则的判停器。",
            "params": {
                "max_depth": {"type": "integer", "default": 3},
                "max_nodes": {"type": "integer", "default": 50},
                "max_iterations": {"type": "integer", "default": 10}
            }
        }
