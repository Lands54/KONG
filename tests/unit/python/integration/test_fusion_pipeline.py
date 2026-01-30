"""
融合管道的集成测试
"""

import pytest
from dynhalting.processors.fusion import GraphFusion
from dynhalting.core.graph import Graph, Node, NodeType
from tests.python.fixtures.sample_graphs import create_simple_graph


@pytest.mark.integration
class TestFusionPipeline:
    """测试融合管道"""
    
    def test_fusion_pipeline(self):
        """测试完整的融合流程"""
        fusion = GraphFusion()
        
        # 创建 Bottom-Up 图
        graph_b = Graph(graph_id="bottom")
        node_b1 = Node(id="b1", label="Entity 1", node_type=NodeType.ENTITY)
        node_b2 = Node(id="b2", label="Entity 2", node_type=NodeType.ENTITY)
        graph_b.add_node(node_b1)
        graph_b.add_node(node_b2)
        
        # 创建 Top-Down 图
        graph_t = Graph(graph_id="top")
        node_t1 = Node(id="t1", label="Concept 1", node_type=NodeType.CONCEPT)
        graph_t.add_node(node_t1)
        
        # 执行融合
        result = fusion.fuse(graph_b, graph_t)
        assert isinstance(result, Graph)
        assert len(result.nodes) >= 1
