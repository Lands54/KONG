"""
图数据结构的单元测试
"""

import pytest
from dynhalting.core.graph import Graph, Node, Edge, NodeType


class TestNode:
    """测试 Node 类"""
    
    def test_node_creation(self):
        """测试节点创建"""
        node = Node(id="test1", label="Test Node", node_type=NodeType.ENTITY)
        assert node.id == "test1"
        assert node.label == "Test Node"
        assert node.node_type == NodeType.ENTITY
    
    def test_node_with_subgraph(self):
        """测试带子图的节点"""
        subgraph = Graph(graph_id="sub")
        node = Node(id="test1", label="Test", subgraph=subgraph)
        assert node.subgraph is not None
        assert node.subgraph.graph_id == "sub"


class TestEdge:
    """测试 Edge 类"""
    
    def test_edge_creation(self):
        """测试边创建"""
        edge = Edge(source="n1", target="n2", relation="related_to")
        assert edge.source == "n1"
        assert edge.target == "n2"
        assert edge.relation == "related_to"


class TestGraph:
    """测试 Graph 类"""
    
    def test_graph_creation(self):
        """测试图创建"""
        graph = Graph(graph_id="test_graph")
        assert graph.graph_id == "test_graph"
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0
    
    def test_add_node(self):
        """测试添加节点"""
        graph = Graph(graph_id="test")
        node = Node(id="n1", label="Node 1")
        graph.add_node(node)
        assert "n1" in graph.nodes
        assert graph.nodes["n1"] == node
    
    def test_add_edge(self):
        """测试添加边"""
        graph = Graph(graph_id="test")
        node1 = Node(id="n1", label="Node 1")
        node2 = Node(id="n2", label="Node 2")
        graph.add_node(node1)
        graph.add_node(node2)
        
        edge = Edge(source="n1", target="n2", relation="connects")
        graph.add_edge(edge)
        assert len(graph.edges) == 1
        assert graph.edges[0] == edge
    
    def test_get_node(self):
        """测试获取节点"""
        graph = Graph(graph_id="test")
        node = Node(id="n1", label="Node 1")
        graph.add_node(node)
        assert graph.get_node("n1") == node
        assert graph.get_node("nonexistent") is None
