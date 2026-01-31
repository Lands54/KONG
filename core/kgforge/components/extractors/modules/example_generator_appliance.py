
from typing import Any, Dict, List
from kgforge.models import Graph, Node, Edge
from kgforge.components.base import BaseExtractor

class ExampleGeneratorAppliance(BaseExtractor):
    """
    示例生成器 (Extractor)
    
    用于演示 Component 编写规范。
    不调用 LLM，仅生成确定性的测试数据。
    """
    name = "example_generator"
    display_name = "Example 数据生成器"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {})
        self.node_count = self.config.get("node_count", 10)

    @classmethod
    def get_component_spec(cls) -> Dict[str, Any]:
        return {
            "id": "example_generator",
            "name": "Example 数据生成器",
            "type": "extractor",
            "description": "生成固定模式的测试图数据，用于演示编排流程。",
            "params": {
                "node_count": {
                    "type": "integer",
                    "default": 10,
                    "description": "生成节点数量"
                }
            }
        }

    def extract(self, text: str) -> Graph:
        graph = Graph(graph_id="gen_graph")
        
        # 模拟根据输入文本生成
        root = Node(node_id="ROOT", label="Seed", attributes={"source": text[:10]})
        graph.add_node(root)
        
        for i in range(self.node_count):
            node = Node(
                node_id=f"NODE_{i}", 
                label=f"Item {i}", 
                attributes={"score": (i % 10) / 10.0} # 0.0 to 0.9
            )
            graph.add_node(node)
            graph.add_edge(Edge(source="ROOT", target=f"NODE_{i}", relation="generated"))
            
        return graph

