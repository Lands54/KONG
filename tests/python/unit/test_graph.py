import pytest
from kgforge.models.graph import Graph, Node, Edge

class TestNode:
    def test_node_creation(self):
        node = Node(node_id="test1", label="Test Node")
        assert node.id == "test1"
        assert node.attr("label") == "Test Node"
    
    def test_node_attrs(self):
        node = Node(node_id="test1", label="Test")
        node.set_attr("key", "value")
        assert node.attr("key") == "value"

class TestEdge:
    def test_edge_creation(self):
        edge = Edge(source="n1", target="n2", relation="related_to")
        assert edge.source == "n1"
        assert edge.target == "n2"
        assert edge.attr("relation") == "related_to"

class TestGraph:
    def test_graph_creation(self):
        graph = Graph(graph_id="test_graph")
        assert graph.graph_id == "test_graph"
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0
    
    def test_add_node(self):
        graph = Graph(graph_id="test")
        node = Node(node_id="n1", label="Node 1")
        graph.add_node(node)
        assert "n1" in graph.nodes
        assert graph.nodes["n1"] == node
    
    def test_add_edge(self):
        graph = Graph(graph_id="test")
        node1 = Node(node_id="n1", label="Node 1")
        node2 = Node(node_id="n2", label="Node 2")
        graph.add_node(node1)
        graph.add_node(node2)
        
        edge = Edge(source="n1", target="n2", relation="connects")
        graph.add_edge(edge)
        assert len(graph.edges) == 1
        assert graph.edges[0] == edge
