from typing import Any, Dict
from kgforge.components.base import BaseFusion
from kgforge.components.fusions.utils.graph_fusion import GraphFusion
from kgforge.models import Graph

class SemanticFusionAppliance(BaseFusion):
    """
    语义图融合器具
    """
    name = "semantic_fusion"
    display_name = "语义融合器"

    def __init__(self, config: Dict[str, Any] = None, **kwargs):
        # 参数合并
        mapped_config = (config or {}).copy()
        mapped_config.update(kwargs)
        super().__init__(mapped_config)
        
        self.fusion = GraphFusion(
            similarity_threshold=self.config.get("similarity_threshold", 0.9)
        )

    @classmethod
    def get_component_spec(cls) -> Dict[str, Any]:
        """获取组件规范"""
        return {
            "id": "semantic_fusion",
            "name": "语义融合器",
            "description": "基于语义相似度的图融合器，合并 Bottom-Up 和 Top-Down 结果。",
            "params": {
                "similarity_threshold": {
                    "type": "number",
                    "default": 0.9,
                    "description": "语义相似度阈值"
                }
            }
        }

    def fuse(self, graph_b: Graph, graph_t: Graph) -> Graph:
        """实现 IFusion 接口"""
        return self.fusion.fuse(graph_b, graph_t)
