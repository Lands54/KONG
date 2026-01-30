from typing import Any, Dict, Optional
from kgforge.components.base import BaseProcessor
from kgforge.components.processors.utils.semantic_deduplicator import SemanticDeduplicator
from kgforge.protocols import IPreloadable, IConfigurable
from kgforge.models import Graph

class SemanticDeduplicatorAppliance(BaseProcessor, IPreloadable, IConfigurable):
    """
    基于语义相似度的节点去重处理器器具
    """
    name = "dedup"
    display_name = "语义去重处理器"

    def __init__(self, config: Dict[str, Any] = None, **kwargs):
        # 合并配置
        mapped_config = (config or {}).copy()
        mapped_config.update(kwargs)
        super().__init__(mapped_config)
        
        self.processor = SemanticDeduplicator(
            model_name=self.config.get("model_name", "sentence-transformers/all-MiniLM-L6-v2"),
            similarity_threshold=self.config.get("similarity_threshold", 0.9),
            device=self.config.get("device")
        )

    @classmethod
    def get_component_spec(cls) -> Dict[str, Any]:
        """获取组件规范"""
        return {
            "id": "dedup",
            "name": "语义去重处理器",
            "description": "基于语义相似度的节点去重器，合并相似含义的节点。",
            "params": {
                "similarity_threshold": {
                    "type": "number",
                    "default": 0.9,
                    "description": "语义相似度阈值"
                },
                "model_name": {
                    "type": "string",
                    "default": "sentence-transformers/all-MiniLM-L6-v2",
                    "description": "Embedding模型名称"
                },
                "device": {
                    "type": "string",
                    "default": "cpu",
                    "description": "运行设备 (cpu/cuda)"
                }
            },
            "capabilities": ["Configurable", "Preloadable"]
        }

    def process(self, graph: Graph, **kwargs) -> Graph:
        """实现 IProcessor 接口"""
        return self.processor.deduplicate(graph)

    def deduplicate(self, graph: Graph) -> Graph:
        """别名兼容性支持"""
        return self.process(graph)

    def preload(self):
        """实现 IPreloadable 接口"""
        self.processor.load_model()

    def update_config(self, params: Dict[str, Any]):
        """实现 IConfigurable 接口"""
        if "similarity_threshold" in params:
            self.processor.threshold = float(params["similarity_threshold"])
