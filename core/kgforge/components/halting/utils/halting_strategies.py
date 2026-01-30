"""
动态判停策略接口
为研究预留的标准接口，支持后续实现 ASI、PSG、SCD、UCB 等策略

重构说明：
- 策略现在返回一个带标签的图，每个节点包含多个属性
- 节点属性包括：status, ablation_value, uncertainty, confidence 等
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from kgforge.models import Graph, Node


class AbstractHaltingStrategy(ABC):
    """抽象判停策略基类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        """
        初始化策略
        Args:
            config: 配置字典
            **kwargs: 其他透传参数
        """
        self.config = config or {}
        # 合并 kwargs 到 config
        self.config.update(kwargs)
    
    @abstractmethod
    def evaluate_graph(self, graph: Graph, current_state: Dict[str, Any]) -> Graph:
        """
        评估图并为每个节点添加属性标签
        
        这是核心方法，策略应该：
        1. 遍历图中的每个节点
        2. 计算节点的各种属性（价值、不确定性、置信度等）
        3. 为每个节点设置判停状态（HALT-ACCEPT, HALT-DROP, LOOP, HITL）
        4. 将所有属性写入节点的 metadata
        
        Args:
            graph: 待评估的图（会被修改，添加节点属性）
            current_state: 当前状态字典，包含：
                - goal: 目标需求
                - depth: 当前深度
                - iteration: 迭代次数
                - 其他自定义状态信息
                
        Returns:
            带标签的图（节点已添加属性）
            
        节点属性说明（存储在 node.metadata 中）：
            - status: 判停状态 ("HALT-ACCEPT", "HALT-DROP", "LOOP", "HITL")
            - ablation_value: 偏去式价值（浮点数）
            - uncertainty: 不确定性（浮点数，0-1）
            - confidence: 置信度（浮点数，0-1）
            - structural_importance: 结构重要性（浮点数）
            - semantic_consistency: 语义一致性（浮点数）
            - 其他自定义属性...
        """
        pass
    
    def evaluate_value(self, node: Node, graph: Graph) -> float:
        """
        计算节点在图中的偏去式价值 (Ablation Value)
        
        这是一个辅助方法，用于计算单个节点的价值。
        主要逻辑应该在 evaluate_graph 中实现。
        
        Args:
            node: 待评估的节点
            graph: 当前图结构
            
        Returns:
            节点的价值分数（通常为浮点数，值越大表示越重要）
        """
        # 默认实现：使用节点度数
        return float(graph.get_node_degree(node.id))
    
    def should_halt(self, graph: Graph, current_state: Dict[str, Any]) -> str:
        """全局判停接口：基于节点 Slot 状态统计"""
        node_statuses = {}
        for node in graph.nodes.values():
            # 从 state 插槽读取状态
            status = node.state('status', 'UNKNOWN')
            node_statuses[status] = node_statuses.get(status, 0) + 1
        
        # 如果还有任何节点处于 LOOP 状态，则继续探索
        if node_statuses.get('LOOP', 0) > 0:
            return "CONTINUE"
        return "HALT"
    
    def get_explanation(self, node: Node, current_state: Dict[str, Any]) -> str:
        status = node.state('status', 'UNKNOWN')
        value = node.metric('ablation_value', 0.0)
        return f"Node {node.id}: status={status}, value={value:.3f}"


class ASI_Strategy(AbstractHaltingStrategy):
    """ASI (Ablation-based Structural Importance) 策略"""
    def evaluate_graph(self, graph: Graph, current_state: Dict[str, Any]) -> Graph:
        for node in graph.nodes.values():
            value = self.evaluate_value(node, graph)
            # 使用标准的插槽方法写入
            node.set_metric('ablation_value', value)
            node.set_metric('structural_importance', float(graph.get_node_degree(node.id)))
            node.set_metric('uncertainty', 0.3)
            node.set_metric('confidence', min(1.0, value / 10.0))
            
            # 写入流程状态插槽
            status = 'HALT-ACCEPT' if value > 5 else ('HALT-DROP' if value < 1 else 'LOOP')
            node.set_state('status', status)
        return graph

class PSG_Strategy(AbstractHaltingStrategy):
    """PSG (Probabilistic Subgraph) 策略"""
    def evaluate_graph(self, graph: Graph, current_state: Dict[str, Any]) -> Graph:
        for node in graph.nodes.values():
            value = self.evaluate_value(node, graph)
            node.set_metric('ablation_value', value)
            node.set_metric('probabilistic_score', value)
            node.set_metric('uncertainty', 0.5)
            node.set_metric('confidence', value)
            
            status = 'HALT-ACCEPT' if value > 0.8 else ('HALT-DROP' if value < 0.2 else 'LOOP')
            node.set_state('status', status)
        return graph
    def evaluate_value(self, node: Node, graph: Graph) -> float:
        return 1.0

class SCD_Strategy(AbstractHaltingStrategy):
    """SCD (Semantic Consistency Degradation) 策略"""
    def evaluate_graph(self, graph: Graph, current_state: Dict[str, Any]) -> Graph:
        for node in graph.nodes.values():
            value = self.evaluate_value(node, graph)
            node.set_metric('ablation_value', value)
            node.set_metric('semantic_consistency', value / 10.0)
            node.set_metric('uncertainty', 0.4)
            node.set_metric('confidence', min(1.0, value / 20.0))
            
            status = 'HALT-ACCEPT' if value > 15 else ('HALT-DROP' if value < 3 else 'LOOP')
            node.set_state('status', status)
        return graph
    def evaluate_value(self, node: Node, graph: Graph) -> float:
        return float(len(node.attr("label")))

class UCB_Strategy(AbstractHaltingStrategy):
    """UCB (Upper Confidence Bound) 策略"""
    def evaluate_graph(self, graph: Graph, current_state: Dict[str, Any]) -> Graph:
        for node in graph.nodes.values():
            value = self.evaluate_value(node, graph)
            node.set_metric('ablation_value', value)
            node.set_metric('ucb_score', value)
            node.set_metric('uncertainty', 0.6)
            node.set_metric('confidence', value)
            
            status = 'HALT-ACCEPT' if value > 0.7 else ('HALT-DROP' if value < 0.3 else 'LOOP')
            node.set_state('status', status)
        return graph
    def evaluate_value(self, node: Node, graph: Graph) -> float:
        return 0.5

class RuleBasedStrategy(AbstractHaltingStrategy):
    """RuleBased 策略（用于测试和基线）"""
    def evaluate_graph(self, graph: Graph, current_state: Dict[str, Any]) -> Graph:
        for node in graph.nodes.values():
            value = self.evaluate_value(node, graph)
            node.set_metric('ablation_value', value)
            node.set_metric('structural_importance', float(graph.get_node_degree(node.id)))
            node.set_metric('uncertainty', 0.5)
            node.set_metric('confidence', 0.5)
            
            status = 'HALT-ACCEPT' if value > 5 else ('HALT-DROP' if value < 1 else 'LOOP')
            node.set_state('status', status)
        return graph

class PlaceholderStrategy(AbstractHaltingStrategy):
    def evaluate_graph(self, graph: Graph, current_state: Dict[str, Any]) -> Graph:
        return graph
