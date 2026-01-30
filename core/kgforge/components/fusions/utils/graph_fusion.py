"""
图融合模块 (Core Implementation)
将 Bottom-Up 图 G_B 与 Top-Down 图 G_T 融合为候选决策图 G_F
纯粹的业务逻辑类，不依赖系统协议
"""

from typing import Dict, List, Optional, Any, Tuple
from kgforge.models import Graph, Node, Edge
from kgforge.components.processors.utils.semantic_deduplicator import SemanticDeduplicator

from kgforge.protocols import IConfigurable

class GraphFusion(IConfigurable):
    """图融合器核心逻辑"""
    
    def __init__(self, similarity_threshold: float = 0.9, deduplicator: Optional['SemanticDeduplicator'] = None, **kwargs):
        """
        初始化图融合器
        
        Args:
            similarity_threshold: 语义相似度阈值（用于节点对齐）
            deduplicator: 预加载的语义去重器（可选，如果提供则使用，否则创建新的）
        """
        if deduplicator is not None:
            self.deduplicator = deduplicator
        else:
            self.deduplicator = SemanticDeduplicator(similarity_threshold=similarity_threshold)
    
    def fuse(self, graph_b: Graph, graph_t: Graph) -> Tuple[Graph, Dict[str, str]]:
        """
        融合两个图
        
        Args:
            graph_b: Bottom-Up 图 G_B
            graph_t: Top-Down 图 G_T
            
        Returns:
            融合后的候选决策图 G_F
        """
        # 创建融合图
        graph_f = Graph(graph_id="G_F")
        graph_f.source = "fused"
        graph_f.depth = max(graph_b.depth, graph_t.depth)
        
        # 合并所有节点（先简单合并，后续去重）
        node_id_mapping = {}  # 原节点 ID -> 新节点 ID
        
        # 添加 G_B 的节点
        for node in graph_b.nodes.values():
            new_id = f"fused_B_{node.id}"
            new_node = Node(node_id=new_id, label=node.attr("label"))
            new_node._attrs.update(node._attrs)
            new_node._metrics.update(node._metrics)
            new_node._state.update(node._state)
            new_node._metadata.update(node._metadata)
            new_node.set_meta("source", "bottom_up")
            new_node.subgraph = node.subgraph
            
            graph_f.add_node(new_node)
            node_id_mapping[f"B_{node.id}"] = new_id
        
        # 添加 G_T 的节点
        for node in graph_t.nodes.values():
            new_id = f"fused_T_{node.id}"
            new_node = Node(node_id=new_id, label=node.attr("label"))
            new_node._attrs.update(node._attrs)
            new_node._metrics.update(node._metrics)
            new_node._state.update(node._state)
            new_node._metadata.update(node._metadata)
            new_node.set_meta("source", "top_down")
            new_node.subgraph = node.subgraph
            
            graph_f.add_node(new_node)
            node_id_mapping[f"T_{node.id}"] = new_id
        
        # 添加 G_B 的边
        for edge in graph_b.edges:
            source_id = node_id_mapping.get(f"B_{edge.source}")
            target_id = node_id_mapping.get(f"B_{edge.target}")
            if source_id and target_id:
                new_edge = Edge(
                    source=source_id,
                    target=target_id,
                    relation=edge.attr("relation")
                )
                new_edge._attrs.update(edge._attrs)
                new_edge._metrics.update(edge._metrics)
                new_edge._metadata.update(edge._metadata)
                new_edge.set_meta("source", "bottom_up")
                graph_f.add_edge(new_edge)
        
        # 添加 G_T 的边
        for edge in graph_t.edges:
            source_id = node_id_mapping.get(f"T_{edge.source}")
            target_id = node_id_mapping.get(f"T_{edge.target}")
            if source_id and target_id:
                new_edge = Edge(
                    source=source_id,
                    target=target_id,
                    relation=edge.attr("relation")
                )
                new_edge._attrs.update(edge._attrs)
                new_edge._metrics.update(edge._metrics)
                new_edge._metadata.update(edge._metadata)
                new_edge.set_meta("source", "top_down")
                graph_f.add_edge(new_edge)
        
        # 语义去重（合并相似节点）
        graph_f, id_mapping = self.deduplicator.deduplicate(graph_f)
        
        # 更新元数据
        graph_f._metadata.update({
            "source_graphs": {
                "G_B": graph_b.graph_id,
                "G_T": graph_t.graph_id
            },
            "fusion_method": "semantic_dedup"
        })
        
        return graph_f, id_mapping
    
    def align_and_merge(
        self,
        graph_b: Graph,
        graph_t: Graph,
        mapping: Optional[Dict[str, str]] = None
    ) -> Graph:
        """
        对齐并合并两个图（使用显式映射）
        """
        # 如果没有显式映射，使用语义相似度自动对齐
        if mapping is None:
            return self.fuse(graph_b, graph_t)
        
        # 使用显式映射进行融合（简化实现）
        graph_f = Graph(graph_id="G_F")
        graph_f.source = "fused"
        
        # TODO: 实现基于显式映射的融合逻辑
        
        return graph_f
    
    def update_config(self, params: Dict[str, Any]):
        """
        更新配置
        实现 IConfigurable 接口
        """
        if self.deduplicator:
             # Case 1: Deduplicator acts as Appliance (IConfigurable)
             if isinstance(self.deduplicator, IConfigurable) or hasattr(self.deduplicator, 'update_config'):
                  self.deduplicator.update_config(params)
             # Case 2: Deduplicator is raw instance (SemanticDeduplicator)
             elif hasattr(self.deduplicator, 'threshold') and 'similarity_threshold' in params:
                  self.deduplicator.threshold = float(params['similarity_threshold'])
