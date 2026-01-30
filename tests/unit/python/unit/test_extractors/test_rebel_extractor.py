"""
REBEL 抽取器的单元测试
"""

import pytest
from dynhalting.extractors.rebel_extractor import REBELExtractor
from dynhalting.core.graph import Graph


class TestREBELExtractor:
    """测试 REBEL 抽取器"""
    
    @pytest.fixture
    def extractor(self):
        """创建抽取器实例"""
        return REBELExtractor()
    
    def test_extractor_initialization(self, extractor):
        """测试抽取器初始化"""
        assert extractor is not None
        assert extractor.model_name is not None
    
    def test_extract_empty_text(self, extractor):
        """测试空文本抽取"""
        triples = extractor.extract("")
        assert triples == []
    
    def test_extract_to_graph(self, extractor, sample_text):
        """测试抽取到图结构"""
        # 注意：这需要模型加载，可能较慢
        # 在实际测试中可能需要 mock 或跳过
        graph = extractor.extract_to_graph(sample_text)
        assert isinstance(graph, Graph)
        # 验证图结构
        assert graph.graph_id is not None
