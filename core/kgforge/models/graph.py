"""
Slot-based Graph Models (Clean Interface Version)
核心设计模式：Element-Slot 容器模式。
放弃属性兼容层，采用显式接口进行 Slot 访问。
"""

from typing import Dict, List, Optional, Set, Any
import uuid
import json


class GraphElement:
    """所有图元素的祖先，提供四类标准插槽访问接口"""
    def __init__(self):
        self._attrs: Dict[str, Any] = {}
        self._metrics: Dict[str, float] = {}
        self._state: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}

    # --- Attributes Slot (身份特征) ---
    def attr(self, key: str, default: Any = None) -> Any:
        return self._attrs.get(key, default)

    def set_attr(self, key: str, value: Any) -> 'GraphElement':
        self._attrs[key] = value
        return self

    # --- Metrics Slot (量化指标) ---
    def metric(self, key: str, default: float = 0.0) -> float:
        return self._metrics.get(key, default)

    def set_metric(self, key: str, value: float) -> 'GraphElement':
        self._metrics[key] = float(value)
        return self

    # --- State Slot (流程状态) ---
    def state(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set_state(self, key: str, value: Any) -> 'GraphElement':
        self._state[key] = value
        return self

    # --- Meta Slot (溯源元数据) ---
    def meta(self, key: str, default: Any = None) -> Any:
        return self._metadata.get(key, default)

    def set_meta(self, key: str, value: Any) -> 'GraphElement':
        self._metadata[key] = value
        return self

    @property
    def attributes(self): return self._attrs
    
    @property
    def metrics(self): return self._metrics
    
    @property
    def flow_state(self): return self._state


class Node(GraphElement):
    """图节点：仅暴露 ID 和 Subgraph 核心结构字段"""
    def __init__(self, node_id: str, label: str, **kwargs):
        super().__init__()
        self.id = node_id
        self.subgraph: Optional['Graph'] = None
        
        # 初始化核心属性
        self.set_attr("label", label)
        
        # 批量处理其他初始化数据
        for k, v in kwargs.items():
            if k == "state": self._state.update(v)
            elif k == "metrics": self._metrics.update(v)
            elif k == "metadata": self._metadata.update(v)
            else: self.set_attr(k, v)

    def __hash__(self): return hash(self.id)
    def __eq__(self, other): return isinstance(other, Node) and self.id == other.id
    def __repr__(self): return f"Node(id={self.id}, label={self.attr('label')})"

    def to_dict(self):
        return {
            "id": self.id,
            "attributes": self._attrs,
            "metrics": self._metrics,
            "state": self._state,
            "metadata": self._metadata,
            "has_subgraph": self.subgraph is not None
        }


class Edge(GraphElement):
    """图边：仅暴露 Source 和 Target 拓扑字段"""
    def __init__(self, source: str, target: str, relation: str, **kwargs):
        super().__init__()
        self.source = source
        self.target = target
        self.set_attr("relation", relation)
        
        for k, v in kwargs.items():
            if k == "weight": self.set_metric("weight", v)
            elif k == "metadata": self._metadata.update(v)
            else: self.set_attr(k, v)

    def __hash__(self): return hash((self.source, self.target, self.attr("relation")))
    def __eq__(self, other):
        return (isinstance(other, Edge) and 
                self.source == other.source and 
                self.target == other.target and 
                self.attr("relation") == other.attr("relation"))

    def to_dict(self):
        return {
            "source": self.source,
            "target": self.target,
            "attributes": self._attrs,
            "metrics": self._metrics,
            "metadata": self._metadata
        }


class Graph:
    """递归系统图：拓扑管理器"""
    def __init__(self, graph_id: Optional[str] = None):
        self.graph_id = graph_id or str(uuid.uuid4())
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self._metadata: Dict[str, Any] = {}
        self.depth: int = 0
        self.source: str = "unknown"

    def meta(self, key: str, default: Any = None) -> Any:
        return self._metadata.get(key, default)

    def set_meta(self, key: str, value: Any) -> 'Graph':
        self._metadata[key] = value
        return self
        
    @property
    def metadata(self): return self._metadata

    def add_node(self, node: Node) -> Node:
        self.nodes[node.id] = node
        return node
    
    def add_edge(self, edge: Edge) -> Edge:
        if edge.source not in self.nodes or edge.target not in self.nodes:
            raise ValueError(f"Edge links missing nodes: {edge.source} -> {edge.target}")
        self.edges.append(edge)
        return edge

    def get_node(self, node_id: str) -> Optional[Node]:
        return self.nodes.get(node_id)

    def merge_node(self, source_id: str, target_id: str):
        """
        将 source_id 节点合并到 target_id 节点
        1. 重新映射所有关联的边
        2. 删除 source 节点
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            return

        # 重新映射边
        for edge in self.edges:
            if edge.source == source_id:
                edge.source = target_id
            if edge.target == source_id:
                edge.target = target_id

        # 删除 source 节点
        del self.nodes[source_id]

    def get_node_degree(self, node_id: str) -> int:
        """获取节点的度（入度+出度）"""
        count = 0
        for edge in self.edges:
            if edge.source == node_id or edge.target == node_id:
                count += 1
        return count

    def get_neighbors(self, node_id: str) -> List[str]:
        """获取节点的邻居节点（不分方向）"""
        neighbors = set()
        for edge in self.edges:
            if edge.source == node_id:
                neighbors.add(edge.target)
            elif edge.target == node_id:
                neighbors.add(edge.source)
        return list(neighbors)

    def get_successors(self, node_id: str) -> List[str]:
        """获取后继节点（出边指向的节点）"""
        return [edge.target for edge in self.edges if edge.source == node_id]

    def get_predecessors(self, node_id: str) -> List[str]:
        """获取前驱节点（入边指向的节点）"""
        return [edge.source for edge in self.edges if edge.target == node_id]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "depth": self.depth,
            "source": self.source,
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Graph':
        g = cls(graph_id=data.get("graph_id"))
        g.depth = data.get("depth", 0)
        g.source = data.get("source", "unknown")
        g._metadata.update(data.get("metadata", {}))

        for nd in data.get("nodes", []):
            # 获取 label，优先从 attributes 读，兼容顶层
            label = nd.get("attributes", {}).get("label") or nd.get("label", "Unknown")
            node = Node(node_id=nd["id"], label=label)
            node._attrs.update(nd.get("attributes", {}))
            node._metrics.update(nd.get("metrics", {}))
            node._state.update(nd.get("state", {}))
            node._metadata.update(nd.get("metadata", {}))
            g.add_node(node)

        for ed in data.get("edges", []):
            relation = ed.get("attributes", {}).get("relation") or ed.get("relation", "related_to")
            edge = Edge(source=ed["source"], target=ed["target"], relation=relation)
            edge._attrs.update(ed.get("attributes", {}))
            edge._metrics.update(ed.get("metrics", {}))
            edge._metadata.update(ed.get("metadata", {}))
            g.add_edge(edge)

        return g

    def __len__(self): return len(self.nodes)
    def __repr__(self): return f"Graph(id={self.graph_id}, v={len(self.nodes)}, e={len(self.edges)})"
