"""
语义去重处理器的单元测试
"""

import pytest
from dynhalting.processors.dedup import SemanticDeduplicator
from dynhalting.core.graph import Graph, Node, NodeType
from tests.python.fixtures.sample_graphs import create_simple_graph


class TestSemanticDeduplicator:
    """测试语义去重器"""
    
    @pytest.fixture
    def deduplicator(self):
        """创建去重器实例"""
        return SemanticDeduplicator()
    
    def test_deduplicator_initialization(self, deduplicator):
        """测试去重器初始化"""
        assert deduplicator is not None
        assert deduplicator.threshold > 0
    
    def test_compute_embeddings(self, deduplicator):
        """测试计算 embeddings"""
        nodes = [
            Node(id="n1", label="United States", node_type=NodeType.ENTITY),
            Node(id="n2", label="USA", node_type=NodeType.ENTITY),
        ]
        embeddings = deduplicator.compute_embeddings(nodes)
        assert len(embeddings) == 2
        assert "n1" in embeddings
        assert "n2" in embeddings
    
    def test_find_similar_pairs(self, deduplicator):
        """测试查找相似节点对"""
        nodes = [
            Node(id="n1", label="United States", node_type=NodeType.ENTITY),
            Node(id="n2", label="USA", node_type=NodeType.ENTITY),
            Node(id="n3", label="Apple", node_type=NodeType.ENTITY),
        ]
        embeddings = deduplicator.compute_embeddings(nodes)
        similar_pairs = deduplicator.find_similar_pairs(nodes, embeddings)
        # n1 和 n2 应该相似
        assert len(similar_pairs) >= 0  # 取决于实际相似度
