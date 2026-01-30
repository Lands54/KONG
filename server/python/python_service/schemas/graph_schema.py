"""
图序列化
将 Graph 对象转换为 JSON 格式
处理递归子图，避免循环引用
"""

from typing import Dict, Any, Set, Optional
import sys
import os


from kgforge.models import Graph, Node, Edge


def ensure_serializable(obj: Any) -> Any:
    """
    递归确保对象可以被 JSON 序列化。
    支持:
    1. 基础 JSON 类型 (str, int, float, bool, None)
    2. 实现了 to_dict() 接口的对象
    3. 列表、元组、集合、字典 (递归处理)
    4. 保底方案：调用 __str__ 魔法方法转换为字符串
    """
    # 1. 基础类型直通
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    
    # 2. 检查自定义序列化协议 (to_dict)
    if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
        try:
            return ensure_serializable(obj.to_dict())
        except:
            pass
            
    # 3. 容器类型递归
    if isinstance(obj, dict):
        return {str(k): ensure_serializable(v) for k, v in obj.items()}
    
    if isinstance(obj, (list, tuple, set)):
        return [ensure_serializable(v) for v in obj]
        
    # 4. 终极保底：利用 Python 魔法方法转化为字符串
    # 这能保证哪怕是一个复杂的类实例，也不会导致 API 崩溃
    try:
        return str(obj)
    except:
        return f"[Unserializable Object: {type(obj).__name__}]"


def node_to_dict(node: Node, visited_subgraphs: Optional[Set[str]] = None) -> Dict[str, Any]:
    """
    将 Node 转换为字典
    """
    if visited_subgraphs is None:
        visited_subgraphs = set()
    
    # 基础扁平化字段 (兼容 API 输出规范)
    node_dict = {
        "id": node.id,
        "label": node.attr("label"),
        "node_type": node.attr("node_type", "mixed"),
        "expandable": node.state("expandable", True),
    }
    
    # 抽取插槽数据并进行“安全序列化处理”
    attrs = ensure_serializable(node._attrs)
    metrics = ensure_serializable(node._metrics)
    state = ensure_serializable(node._state)
    metadata = ensure_serializable(node._metadata)

    # 自动分发逻辑保持：将元数据中的运行时信息移动到 state 插槽
    # 注意：这里的移动是在清理后的副本上操作的
    runtime_keys = ['depth', 'visited_count', 'status', 'state', 'flags', 'source', 'halt_reason']
    for key in runtime_keys:
        if key in metadata:
            state[key] = metadata.pop(key)
    
    node_dict["attributes"] = attrs
    node_dict["metrics"] = metrics
    node_dict["state"] = state
    node_dict["metadata"] = metadata
    if node.subgraph is not None:
        subgraph_id = node.subgraph.graph_id
        if subgraph_id not in visited_subgraphs:
            visited_subgraphs.add(subgraph_id)
            node_dict["subgraph"] = graph_to_dict(node.subgraph, visited_subgraphs)
        else:
            node_dict["subgraph"] = {"graph_id": subgraph_id, "_ref": True}
    
    # 其他辅助字段
    # canonical_id: 规范化 ID，用于语义去重后的实体追踪。
    # 所有的语义等价节点会共享同一个 canonical_id。
    canonical_id = node.attr("canonical_id")
    if canonical_id:
        node_dict["canonical_id"] = canonical_id
    
    return node_dict


def edge_to_dict(edge: Edge) -> Dict[str, Any]:
    """
    将 Edge 转换为字典
    """
    edge_dict = {
        "source": edge.source,
        "target": edge.target,
        "relation": edge.attr("relation"),
        "weight": edge.metric("weight"),
        # 插槽 (使用安全序列化)
        "attributes": ensure_serializable(edge.attributes),
        "metrics": ensure_serializable(edge.metrics),
        "metadata": ensure_serializable(edge._metadata)
    }
    
    return edge_dict


def graph_to_dict(graph: Graph, visited_subgraphs: Optional[Set[str]] = None) -> Dict[str, Any]:
    """
    将 Graph 转换为字典（支持递归子图）
    
    Args:
        graph: 图对象
        visited_subgraphs: 已访问的子图ID集合（避免循环引用）
        
    Returns:
        图字典
    """
    if visited_subgraphs is None:
        visited_subgraphs = set()
    
    graph_id = graph.graph_id
    if graph_id in visited_subgraphs:
        # 避免循环引用
        return {"graph_id": graph_id, "_ref": True}
    
    visited_subgraphs.add(graph_id)
    
    # 序列化节点
    nodes_dict = {}
    for node_id, node in graph.nodes.items():
        nodes_dict[node_id] = node_to_dict(node, visited_subgraphs)
    
    # 序列化边
    edges_list = [edge_to_dict(edge) for edge in graph.edges]
    
    # 构建图字典
    graph_dict = {
        "graph_id": graph_id,
        "nodes": nodes_dict,
        "edges": edges_list,
        "depth": graph.depth,
        "source": graph.source
    }
    
    if graph.metadata:
        graph_dict["metadata"] = graph.metadata.copy()
    
    return graph_dict
