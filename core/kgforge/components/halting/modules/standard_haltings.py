from typing import Any, Dict, Optional
from kgforge.components.base import BaseHalting
from kgforge.components.halting.utils.halting_strategies import (
    ASI_Strategy, SCD_Strategy, PSG_Strategy, UCB_Strategy, RuleBasedStrategy
)
from kgforge.models import Graph
from kgforge.models.enums import HaltingDecision, HaltingResponse

def _wrap_strategy_decision(decision_str: str, strategy_name: str) -> HaltingResponse:
    """将策略返回的字符串转换为 HaltingResponse"""
    mapping = {
        "HALT": HaltingDecision.HALT_ACCEPT,
        "CONTINUE": HaltingDecision.CONTINUE,
        "LOOP": HaltingDecision.LOOP,
        "DROP": HaltingDecision.HALT_DROP,
        "HITL": HaltingDecision.HITL
    }
    decision_enum = mapping.get(decision_str.upper(), HaltingDecision.CONTINUE)
    return HaltingResponse(decision=decision_enum, reason=f"strategy: {strategy_name}")

class ASIAppliance(BaseHalting):
    """ASI (Ablation-based Structural Importance) 判停策略器具"""
    name = "ASI"
    display_name = "ASI 判停策略"

    def __init__(self, config: Dict[str, Any] = None, **kwargs):
        super().__init__(config)
        self.strategy = ASI_Strategy(config=self.config, **kwargs)

    def evaluate_graph(self, graph: Graph, current_state: Dict[str, Any]) -> Graph:
        return self.strategy.evaluate_graph(graph, current_state)

    def should_halt(self, graph: Graph, goal: str, **kwargs) -> HaltingResponse:
        current_state = {"goal": goal, **kwargs}
        res_str = self.strategy.should_halt(graph, current_state)
        return _wrap_strategy_decision(res_str, "ASI")

class SCDAppliance(BaseHalting):
    """SCD (Semantic Consistency Degradation) 判停策略器具"""
    name = "SCD"
    display_name = "SCD 判停策略"

    def __init__(self, config: Dict[str, Any] = None, **kwargs):
        super().__init__(config)
        self.strategy = SCD_Strategy(config=self.config, **kwargs)

    def evaluate_graph(self, graph: Graph, current_state: Dict[str, Any]) -> Graph:
        return self.strategy.evaluate_graph(graph, current_state)

    def should_halt(self, graph: Graph, goal: str, **kwargs) -> HaltingResponse:
        current_state = {"goal": goal, **kwargs}
        res_str = self.strategy.should_halt(graph, current_state)
        return _wrap_strategy_decision(res_str, "SCD")

class PSGAppliance(BaseHalting):
    """PSG (Probabilistic Subgraph) 判停策略器具"""
    name = "PSG"
    display_name = "PSG 判停策略"

    def __init__(self, config: Dict[str, Any] = None, **kwargs):
        super().__init__(config)
        self.strategy = PSG_Strategy(config=self.config, **kwargs)

    def evaluate_graph(self, graph: Graph, current_state: Dict[str, Any]) -> Graph:
        return self.strategy.evaluate_graph(graph, current_state)

    def should_halt(self, graph: Graph, goal: str, **kwargs) -> HaltingResponse:
        current_state = {"goal": goal, **kwargs}
        res_str = self.strategy.should_halt(graph, current_state)
        return _wrap_strategy_decision(res_str, "PSG")

class UCBAppliance(BaseHalting):
    """UCB (Upper Confidence Bound) 判停策略器具"""
    name = "UCB"
    display_name = "UCB 判停策略"

    def __init__(self, config: Dict[str, Any] = None, **kwargs):
        super().__init__(config)
        self.strategy = UCB_Strategy(config=self.config, **kwargs)

    def evaluate_graph(self, graph: Graph, current_state: Dict[str, Any]) -> Graph:
        return self.strategy.evaluate_graph(graph, current_state)

    def should_halt(self, graph: Graph, goal: str, **kwargs) -> HaltingResponse:
        current_state = {"goal": goal, **kwargs}
        res_str = self.strategy.should_halt(graph, current_state)
        return _wrap_strategy_decision(res_str, "UCB")

class RuleBasedStrategyAppliance(BaseHalting):
    """通用规则判停策略器具"""
    name = "RULE_BASED"
    display_name = "规则基线判停"

    def __init__(self, config: Dict[str, Any] = None, **kwargs):
        super().__init__(config)
        self.strategy = RuleBasedStrategy(config=self.config, **kwargs)

    def evaluate_graph(self, graph: Graph, current_state: Dict[str, Any]) -> Graph:
        return self.strategy.evaluate_graph(graph, current_state)

    def should_halt(self, graph: Graph, goal: str, **kwargs) -> HaltingResponse:
        current_state = {"goal": goal, **kwargs}
        res_str = self.strategy.should_halt(graph, current_state)
        return _wrap_strategy_decision(res_str, "RuleBased")
