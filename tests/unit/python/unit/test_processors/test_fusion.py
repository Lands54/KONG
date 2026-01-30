"""
图融合处理器的单元测试
"""

import pytest
from dynhalting.processors.fusion import GraphFusion
from dynhalting.core.graph import Graph, Node, Edge, NodeType
from tests.python.fixtures.sample_graphs import create_simple_graph


class TestGraphFusion:
    """测试图融合器"""
    
    @pytest.fixture
    def fusion(self):
        """创建融合器实例"""
        return GraphFusion()
    
    def test_fusion_initialization(self, fusion):
        """测试融合器初始化"""
        assert fusion is not None
        assert fusion.deduplicator is not None
    
    def test_fuse_empty_graphs(self, fusion):
        """测试融合空图"""
        graph_b = Graph(graph_id="empty_b")
        graph_t = Graph(graph_id="empty_t")
        result = fusion.fuse(graph_b, graph_t)
        assert isinstance(result, Graph)
        assert len(result.nodes) == 0
    
    def test_fuse_simple_graphs(self, fusion):
        """测试融合简单图"""
        graph_b = Graph(graph_id="b")
        node_b = Node(id="b1", label="Bottom Node", node_type=NodeType.ENTITY)
        graph_b.add_node(node_b)
        
        graph_t = Graph(graph_id="t")
        node_t = Node(id="t1", label="Top Node", node_type=NodeType.CONCEPT)
        graph_t.add_node(node_t)
        
        result = fusion.fuse(graph_b, graph_t)
        assert isinstance(result, Graph)
        assert len(result.nodes) >= 1
