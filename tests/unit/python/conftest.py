"""
pytest 配置文件
提供测试 fixtures 和配置
"""

import pytest
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量（如果存在 .env 文件）
env_file = project_root / '.env'
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)

@pytest.fixture
def sample_text():
    """示例文本用于测试"""
    return """
    The United States is a country in North America. 
    Washington D.C. is the capital of the United States.
    Joe Biden is the President of the United States.
    """

@pytest.fixture
def sample_goal():
    """示例目标用于测试"""
    return "了解美国的政治体系"

@pytest.fixture
def sample_graph():
    """示例图结构用于测试"""
    from dynhalting.core.graph import Graph, Node, Edge, NodeType
    
    graph = Graph(graph_id="test_graph")
    node1 = Node(id="node1", label="United States", node_type=NodeType.ENTITY)
    node2 = Node(id="node2", label="Washington D.C.", node_type=NodeType.ENTITY)
    edge1 = Edge(source="node1", target="node2", relation="capital_of")
    
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_edge(edge1)
    
    return graph
