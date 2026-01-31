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
        self._exec_status: str = "LOOP" # 核心执行状态，作为 Pipeline 级的一等公民

    # --- Attributes Slot (身份特征) ---
    def attr(self, key: str, default: Any = None) -> Any:
        return self._attrs.get(key, default)

    def set_attr(self, key: str, value: Any) -> 'GraphElement':
        self._attrs[key] = value
        return self

    def update_attrs(self, data: Dict[str, Any]) -> 'GraphElement':
        self._attrs.update(data)
        return self

    # --- Metrics Slot (量化指标) ---
    def metric(self, key: str, default: float = 0.0) -> float:
        return self._metrics.get(key, default)

    def set_metric(self, key: str, value: float) -> 'GraphElement':
        self._metrics[key] = float(value)
        return self

    def update_metrics(self, data: Dict[str, float]) -> 'GraphElement':
        self._metrics.update(data)
        return self

    # --- State Slot (流程状态) ---
    def state(self, key: str, default: Any = None) -> Any:
        if key == "status": return self._exec_status
        return self._state.get(key, default)

    def set_state(self, key: str, value: Any) -> 'GraphElement':
        if key == "status":
            self._exec_status = value
        else:
            self._state[key] = value
        return self

    def update_state(self, data: Dict[str, Any]) -> 'GraphElement':
        # 保护性检查：不允许通过通用 update 篡改核心状态
        clean_data = {k: v for k, v in data.items() if k != "status"}
        self._state.update(clean_data)
        return self

    # --- Pipeline Status Control (核心执行流转) ---
    def get_status(self) -> str:
        """获取当前节点的执行状态"""
        return self._exec_status

    def status(self, value: str) -> 'GraphElement':
        """
        设置节点的执行状态（支持链式调用）
        这是 Pipeline 级别的最高指令。
        """
        self._exec_status = value
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

    @property
    def metadata(self): return self._metadata

    def _clone_base_to(self, target: 'GraphElement'):
        """辅助方法：深拷贝基础插槽数据"""
        import copy
        target._attrs = copy.deepcopy(self._attrs)
        target._metrics = copy.deepcopy(self._metrics)
        target._state = copy.deepcopy(self._state)
        target._metadata = copy.deepcopy(self._metadata)
        target._exec_status = self._exec_status
        return target


class Node(GraphElement):
    """图节点：仅暴露 ID 和 Subgraph 核心结构字段"""
    def __init__(self, node_id: Optional[str] = None, label: Optional[str] = None, **kwargs):
        """
        智能构造函数：
        1. Node(node_id="A", label="Apple") -> 精确指定
        2. Node(label="Apple") -> 自动 ID (UUID), Label="Apple"
        3. Node("Apple") -> ID="Apple", Label="Apple" (快捷模式)
        """
        super().__init__()
        
        # ID 优先级：显式 node_id > 自动生成短 UUID
        self.id = node_id or str(uuid.uuid4())[:10]
        
        # Label 优先级：显式 label > 显式 node_id > 降级为 id
        self.label = label or node_id or self.id
        
        self.subgraph: Optional['Graph'] = None
        
        # 核心状态初始化 (优先于批量处理)
        if "status" in kwargs:
            self.status(kwargs.pop("status"))

        # 批量处理其他初始化数据
        for k, v in kwargs.items():
            if k == "state": 
                # 处理 state 字典中可能存在的 status
                s = v.get("status")
                if s: self.status(s)
                self.update_state(v)
            elif k == "metrics": self._metrics.update(v)
            elif k == "metadata": self._metadata.update(v)
            else: self.set_attr(k, v)

    @property
    def label(self) -> str:
        return self.attr("label", "")

    @label.setter
    def label(self, value: str):
        self.set_attr("label", value)

    def clone(self) -> 'Node':
        """快速物理隔离克隆"""
        new_node = Node(self.id, self.label)
        self._clone_base_to(new_node)
        if self.subgraph:
            new_node.subgraph = self.subgraph.clone()
        return new_node

    def __hash__(self): return hash(self.id)
    def __eq__(self, other): return isinstance(other, Node) and self.id == other.id
    def __repr__(self): return f"Node(id={self.id}, label={self.label})"

    def to_dict(self):
        return {
            "id": self.id,
            "status": self._exec_status,  # 提升为顶层字段
            "attributes": self._attrs,
            "metrics": self._metrics,
            "state": self._state,
            "metadata": self._metadata,
            "has_subgraph": self.subgraph is not None
        }


class Edge(GraphElement):
    """图边：仅暴露 Source 和 Target 拓扑字段"""
    def __init__(self, source: str, target: str, relation: str, edge_id: Optional[str] = None, **kwargs):
        super().__init__()
        self.source = source
        self.target = target
        self.relation = relation
        self.id = edge_id or str(uuid.uuid4())[:8] # 短 ID 辅助识别
        
        for k, v in kwargs.items():
            if k == "weight": self.set_metric("weight", v)
            elif k == "metadata": self._metadata.update(v)
            else: self.set_attr(k, v)

    @property
    def relation(self) -> str:
        return self.attr("relation", "")

    @relation.setter
    def relation(self, value: str):
        self.set_attr("relation", value)

    def clone(self) -> 'Edge':
        """快速物理隔离克隆"""
        new_edge = Edge(self.source, self.target, self.relation, edge_id=self.id)
        self._clone_base_to(new_edge)
        return new_edge

    def __hash__(self): return hash((self.source, self.target, self.relation, self.id))
    def __eq__(self, other):
        return (isinstance(other, Edge) and 
                self.source == other.source and 
                self.target == other.target and 
                self.relation == other.relation and
                self.id == other.id)

    def to_dict(self):
        return {
            "id": self.id,
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

    def add_node(self, node: Node, overwrite: bool = True) -> Node:
        if node.id in self.nodes and not overwrite:
            raise KeyError(f"Node with ID '{node.id}' already exists in graph '{self.graph_id}'")
        self.nodes[node.id] = node
        return node
    
    def add_edge(self, edge: Edge) -> Edge:
        if edge.source not in self.nodes or edge.target not in self.nodes:
            # 宽容处理：但在生产环境建议报错。这里保持现有逻辑并打印警告。
            import logging
            logging.warning(f"Adding edge for missing nodes: {edge.source} -> {edge.target}")
        self.edges.append(edge)
        return edge

    def get_node(self, node_id: str) -> Optional[Node]:
        return self.nodes.get(node_id)

    def clone(self) -> 'Graph':
        """深拷贝整个图拓扑及所有元素，确保 Pipeline 中绝对的数据隔离"""
        new_graph = Graph(graph_id=self.graph_id)
        new_graph.depth = self.depth
        new_graph.source = self.source
        
        import copy
        new_graph._metadata = copy.deepcopy(self._metadata)
        
        # 克隆所有节点
        for node in self.nodes.values():
            new_graph.add_node(node.clone())
            
        # 克隆所有边
        for edge in self.edges:
            new_graph.add_edge(edge.clone())
            
        return new_graph

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
            edge_id = ed.get("id")
            edge = Edge(source=ed["source"], target=ed["target"], relation=relation, edge_id=edge_id)
            edge._attrs.update(ed.get("attributes", {}))
            edge._metrics.update(ed.get("metrics", {}))
            edge._metadata.update(ed.get("metadata", {}))
            g.add_edge(edge)

        return g

    def __len__(self): return len(self.nodes)
    def __repr__(self): return f"Graph(id={self.graph_id}, v={len(self.nodes)}, e={len(self.edges)})"

