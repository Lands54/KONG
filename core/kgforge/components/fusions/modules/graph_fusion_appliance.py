from typing import Any, Dict, Optional
from kgforge.components.base import BaseFusion
from kgforge.components.fusions.utils.graph_fusion import GraphFusion
from kgforge.models import Graph
from kgforge.protocols import IConfigurable

class GraphFusionAppliance(BaseFusion, IConfigurable):
    """
    语义图融合器具
    """
    name = "fusion"
    display_name = "语义图融合器"

    def __init__(self, config: Dict[str, Any] = None, **kwargs):
        # 参数合并
        mapped_config = (config or {}).copy()
        mapped_config.update(kwargs)
        super().__init__(mapped_config)
        
        # 处理预加载的去重器
        deduplicator = kwargs.get("deduplicator")
        
        self.fusion = GraphFusion(
            similarity_threshold=self.config.get("similarity_threshold", 0.9),
            deduplicator=deduplicator
        )

    @classmethod
    def get_component_spec(cls) -> Dict[str, Any]:
        """获取组件规范"""
        return {
            "id": "fusion",
            "name": "语义图融合器",
            "description": "基于语义相似度的图融合器，合并 Bottom-Up 和 Top-Down 结果。",
            "params": {
                "similarity_threshold": {
                    "type": "number",
                    "default": 0.9,
                    "description": "语义相似度阈值"
                }
            },
            "capabilities": ["Configurable"]
        }

    def fuse(self, graph_b: Graph, graph_t: Graph) -> Graph:
        """实现 IFusion 接口"""
        graph_f, id_mapping = self.fusion.fuse(graph_b, graph_t)
        # 将映射表存入 metadata，以便下游组件使用
        graph_f.set_meta("node_id_mapping", id_mapping)
        return graph_f
    
    def update_config(self, params: Dict[str, Any]):
        """实现 IConfigurable 接口"""
        if self.fusion:
             self.fusion.update_config(params)
