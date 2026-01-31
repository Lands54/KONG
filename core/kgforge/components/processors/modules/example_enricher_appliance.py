
from typing import Any, Dict
import time
from kgforge.models import Graph
from kgforge.components.base import BaseProcessor

class ExampleEnricherAppliance(BaseProcessor):
    """
    示例增强器 (Processor)
    
    模拟耗时操作，给节点增加增强属性。
    """
    name = "example_enricher"
    display_name = "Example 增强器"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {})
        self.delay_ms = int(self.config.get("delay_ms", 100))

    @classmethod
    def get_component_spec(cls) -> Dict[str, Any]:
        return {
            "id": "example_enricher",
            "name": "Example 增强器",
            "type": "processor",
            "description": "模拟数据增强，给节点添加时间戳和标签。",
            "params": {
                "delay_ms": {
                    "type": "integer",
                    "default": 100,
                    "description": "模拟处理延迟(ms)"
                }
            }
        }

    def process(self, graph: Graph, **kwargs) -> Graph:
        # Clone inputs implicitly by modifying in place (since Graphs are mutable, but usually run returns new)
        # For safety in pipelines, let's create a new graph container pointing to same objects or clones?
        # Here we just modify in place and return the same object for efficiency, 
        # but in a real pipeline we might want immutability. 
        # For this example, let's modify in place.
        
        enrichStart = time.time()
        
        # Simulate delay
        time.sleep(self.delay_ms / 1000.0)
        
        for node in graph.nodes.values():
            # 1. 检查状态，避免重复增强 (幂等性)
            if node.state("enriched"):
                continue
                
            # 2. 标记状态
            node.set_state("enriched", True)
            node.set_attr("enrich_ts", enrichStart)
            
            # 3. 智能修改 Label
            if not node.label.startswith("[E] "):
                node.label = f"[E] {node.label}"
            
            # 4. 添加模拟评分 (并入 attributes 插槽)
            node.set_attr("score", 0.7)
            
        return graph

