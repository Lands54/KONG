from typing import Any, Dict, Optional
from kgforge.components.base import BaseExtractor
from kgforge.components.extractors.utils.itext2kg_builder import build_itext2kg_extractor
from kgforge.models import Graph

class IText2KGExtractorAppliance(BaseExtractor):
    """
    基于 itext2kg/ATOM 的三元组抽取器具
    """
    name = "itext2kg"
    display_name = "IText2KG抽取器"

    def __init__(self, config: Dict[str, Any] = None, **kwargs):
        # 合并配置
        mapped_config = (config or {}).copy()
        mapped_config.update(kwargs)
        super().__init__(mapped_config)
        
        # 延迟构建
        self._extractor = None

    def _ensure_extractor(self):
        if self._extractor is None:
            self._extractor = build_itext2kg_extractor(self.config)

    @classmethod
    def get_component_spec(cls) -> Dict[str, Any]:
        """获取组件规范"""
        return {
            "id": "itext2kg",
            "name": "IText2KG抽取器",
            "description": "基于 itext2kg/ATOM 的本体抽取器，支持语义融合与实体对齐。",
            "params": {
                "chat_model": {"type": "string", "default": "google/gemini-2.0-flash-lite-preview-02-05"},
                "embeddings_model": {"type": "string", "default": "sentence-transformers/all-MiniLM-L6-v2"},
                "ent_threshold": {"type": "number", "default": 0.8},
                "rel_threshold": {"type": "number", "default": 0.7}
            }
        }

    def extract(self, text: str) -> Graph:
        """实现 IExtractor 接口"""
        self._ensure_extractor()
        # 原实现使用的是 extract_to_graph，这里做映射
        return self._extractor.extract_to_graph(text)

