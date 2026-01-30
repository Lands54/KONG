"""
测试用的示例图数据
"""

from dynhalting.core.graph import Graph, Node, Edge, NodeType


def create_simple_graph() -> Graph:
    """创建一个简单的测试图"""
    graph = Graph(graph_id="simple_test")
    node1 = Node(id="n1", label="Node 1", node_type=NodeType.ENTITY)
    node2 = Node(id="n2", label="Node 2", node_type=NodeType.ENTITY)
    edge = Edge(source="n1", target="n2", relation="related_to")
    
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_edge(edge)
    
    return graph


def create_nested_graph() -> Graph:
    """创建一个包含子图的嵌套图"""
    graph = Graph(graph_id="nested_test")
    
    # 主节点
    main_node = Node(id="main", label="Main Node", node_type=NodeType.SYSTEM)
    
    # 子图
    subgraph = Graph(graph_id="subgraph")
    sub_node1 = Node(id="sub1", label="Sub Node 1", node_type=NodeType.ENTITY)
    sub_node2 = Node(id="sub2", label="Sub Node 2", node_type=NodeType.ENTITY)
    sub_edge = Edge(source="sub1", target="sub2", relation="connects")
    
    subgraph.add_node(sub_node1)
    subgraph.add_node(sub_node2)
    subgraph.add_edge(sub_edge)
    
    main_node.subgraph = subgraph
    graph.add_node(main_node)
    
    return graph
