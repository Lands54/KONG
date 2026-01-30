"""
图处理工具库
提供图统计、可视化及其他辅助功能
"""

def print_graph_summary(graph, title: str = "图统计"):
    """
    打印图统计信息
    
    Args:
        graph: Graph 对象
        title: 标题
    """
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"节点数: {len(graph.nodes)}")
    print(f"边数: {len(graph.edges)}")
    print(f"来源: {graph.source}")
    print(f"深度: {graph.depth}")
    
    if len(graph.nodes) > 0:
        print(f"\n节点示例 (前5个):")
        for i, node in enumerate(list(graph.nodes.values())[:5]):
            node_type = node.attr("node_type", "mixed")
            print(f"  {i+1}. {node.attr('label')} (类型: {node_type}, ID: {node.id})")
    else:
        print("\n节点: (无)")
