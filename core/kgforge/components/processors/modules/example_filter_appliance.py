
from typing import Any, Dict
from kgforge.models import Graph
from kgforge.components.base import BaseProcessor

class ExampleFilterAppliance(BaseProcessor):
    """
    示例过滤器 (Processor)
    
    过滤掉属性 score 低于阈值的节点。
    """
    name = "example_filter"
    display_name = "Example 过滤器"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {})
        self.threshold = float(self.config.get("threshold", 0.5))

    @classmethod
    def get_component_spec(cls) -> Dict[str, Any]:
        return {
            "id": "example_filter",
            "name": "Example 过滤器",
            "type": "processor",
            "description": "过滤掉 Score 低于阈值的节点。",
            "params": {
                "threshold": {
                    "type": "number",
                    "default": 0.5,
                    "description": "过滤阈值 (0.0 - 1.0)"
                }
            }
        }

    def process(self, graph: Graph, **kwargs) -> Graph:
        filtered_graph = Graph(graph_id=f"{graph.graph_id}_filtered")
        
        # Keep nodes > threshold
        valid_ids = set()
        
        for nid, node in graph.nodes.items():
            score = node.attributes.get("score", 1.0) # Default keep if no score
            if score >= self.threshold:
                filtered_graph.add_node(node)
                valid_ids.add(nid)
                
        # Keep edges only connecting valid nodes
        for edge in graph.edges:
            if edge.source in valid_ids and edge.target in valid_ids:
                filtered_graph.add_edge(edge)
                
        return filtered_graph

