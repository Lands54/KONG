"""
动态判停模块
实现 HaltingModule.evaluate_graph() 和 should_halt_global() 接口
支持三种占位模式：ALWAYS_LOOP, ALWAYS_HALT, RULE_BASED, STRATEGY
"""

from typing import Dict, Any, Optional, List
from kgforge.models.enums import HaltingDecision, HaltingMode, HaltingResponse
from kgforge.models import Graph
from .halting_strategies import AbstractHaltingStrategy, PlaceholderStrategy


class HaltingModule:
    """动态判停模块"""
    
    def __init__(
        self,
        mode: str = "RULE_BASED",
        max_depth: int = 3,
        max_nodes: int = 50,
        max_iterations: int = 10,
        strategy: Optional[AbstractHaltingStrategy] = None
    ):
        """
        初始化判停模块
        """
        # 自动关联策略类并重新设置 mode
        if mode.upper() in ["ASI", "PSG", "SCD", "UCB"]:
            from .halting_strategies import (
                ASI_Strategy, PSG_Strategy, SCD_Strategy, UCB_Strategy
            )
            strategies = {
                "ASI": ASI_Strategy(),
                "PSG": PSG_Strategy(),
                "SCD": SCD_Strategy(),
                "UCB": UCB_Strategy()
            }
            self.strategy = strategies.get(mode.upper())
            self.mode = HaltingMode.STRATEGY
        else:
            try:
                self.mode = HaltingMode(mode.lower())
            except ValueError:
                # 降级到 STRATEGY 或 RULE_BASED
                self.mode = HaltingMode.STRATEGY
            self.strategy = strategy or PlaceholderStrategy()
        self.max_depth = max_depth
        self.max_nodes = max_nodes
        self.max_iterations = max_iterations
        
        # 状态追踪
        self.decision_history: List[Dict[str, Any]] = []
    
    def evaluate_graph(self, graph: Graph, goal: str, depth: int = 0, iteration: int = 0, **kwargs) -> Graph:
        """
        评估图并为每个节点添加属性标签（新接口）
        
        Args:
            graph: 当前候选决策图 G_F（会被修改，添加节点属性）
            goal: 需求目标
            depth: 当前深度
            iteration: 当前迭代次数
            **kwargs: 其他状态信息
            
        Returns:
            带标签的图（节点已添加属性）
        """
        current_state = {
            "goal": goal,
            "depth": depth,
            "iteration": iteration,
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
            **kwargs
        }
        
        # 根据模式选择判停逻辑
        if self.mode == HaltingMode.ALWAYS_LOOP:
            for node in graph.nodes.values():
                node.set_state('status', 'LOOP')
                node.set_metric('ablation_value', self.strategy.evaluate_value(node, graph))
        
        elif self.mode == HaltingMode.ALWAYS_HALT:
            for node in graph.nodes.values():
                node.set_state('status', 'HALT-ACCEPT')
                node.set_metric('ablation_value', self.strategy.evaluate_value(node, graph))
        
        elif self.mode == HaltingMode.RULE_BASED:
            self._rule_based_evaluate(graph, current_state)
        
        elif self.mode == HaltingMode.STRATEGY:
            graph = self.strategy.evaluate_graph(graph, current_state)
        
        # 记录决策历史
        node_statuses = [node.state('status', 'UNKNOWN') for node in graph.nodes.values()]
        status_counts = {}
        for status in node_statuses:
            status_counts[status] = status_counts.get(status, 0) + 1
        
        self.decision_history.append({
            "iteration": iteration,
            "depth": depth,
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
            "node_statuses": status_counts,
            "goal": goal
        })
        
        return graph

    # ... (skipping ahead to rule_based_evaluate)

    def _rule_based_evaluate(self, graph: Graph, state: Dict[str, Any]) -> None:
        depth = state.get("depth", 0)
        node_count = state.get("node_count", 0)
        iteration = state.get("iteration", 0)
        
        global_halt = False
        global_halt_reason = None
        
        if depth >= self.max_depth:
            global_halt, global_halt_reason = True, "max_depth"
        elif node_count >= self.max_nodes:
            global_halt, global_halt_reason = True, "max_nodes"
        elif iteration >= self.max_iterations:
            global_halt, global_halt_reason = True, "max_iterations"
        
        # 为每个节点设置属性
        for node in graph.nodes.values():
            value = self.strategy.evaluate_value(node, graph)
            degree = graph.get_node_degree(node.id)
            
            node.set_metric('ablation_value', value)
            node.set_metric('structural_importance', float(degree))
            node.set_metric('uncertainty', 0.3)
            node.set_metric('confidence', min(1.0, value / 10.0))
            
            # 使用逻辑分支确定最终状态
            if global_halt:
                status = 'HALT-ACCEPT' if value > 2 else 'HALT-DROP'
                reason = global_halt_reason
            elif node_count < 3:
                status, reason = 'HALT-DROP', "insufficient_nodes"
            elif degree == 0:
                status, reason = 'HALT-DROP', "isolated_node"
            elif value > 5:
                status, reason = 'HALT-ACCEPT', "high_value"
            elif value < 1:
                status, reason = 'HALT-DROP', "low_value"
            elif not node.state("expandable", True):
                status, reason = 'HALT-ACCEPT', "not_expandable"
            else:
                status, reason = 'LOOP', "continue_expansion"
            
            node.set_state('status', status)
            node.set_state('halt_reason', reason)
    
    def should_halt_global(self, graph: Graph, goal: str, depth: int = 0, iteration: int = 0, **kwargs) -> HaltingResponse:
        """全局判停：基于硬性规则和节点状态统计"""
        state = {"depth": depth, "node_count": len(graph.nodes), "iteration": iteration, "goal": goal}
        depth, node_count, iteration = state.get("depth", 0), state.get("node_count", 0), state.get("iteration", 0)
        
        if depth >= self.max_depth:
            return HaltingResponse(decision=HaltingDecision.HALT_ACCEPT, reason=f"max_depth reached ({depth})")
        if node_count >= self.max_nodes:
            return HaltingResponse(decision=HaltingDecision.HALT_ACCEPT, reason=f"max_nodes reached ({node_count})")
        if iteration >= self.max_iterations:
            return HaltingResponse(decision=HaltingDecision.HALT_ACCEPT, reason=f"max_iterations reached ({iteration})")
        
        # 使用 Slot API 检查状态
        node_statuses = {}
        for node in graph.nodes.values():
            st = node.state('status', 'UNKNOWN')
            node_statuses[st] = node_statuses.get(st, 0) + 1
        
        if node_statuses.get('LOOP', 0) == 0:
            decision = HaltingDecision.HALT_ACCEPT if node_statuses.get('HALT-ACCEPT', 0) > 0 else HaltingDecision.HALT_DROP
            return HaltingResponse(decision=decision, reason="all_nodes_terminal")
            
        return HaltingResponse(decision=HaltingDecision.CONTINUE, reason="ongoing_expansion")
        
        # 默认继续
        return HaltingResponse(decision=HaltingDecision.CONTINUE, reason="ongoing_expansion")
    
    def get_decision_history(self) -> List[Dict[str, Any]]:
        """获取决策历史"""
        return self.decision_history.copy()
    
    def reset(self):
        """重置决策历史"""
        self.decision_history = []
