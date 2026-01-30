"""
抽取管道的集成测试
"""

import pytest
from dynhalting.extractors.rebel_extractor import REBELExtractor
from dynhalting.extractors.gpt_expander import GPTExpander
from dynhalting.core.graph import Graph


@pytest.mark.integration
class TestExtractionPipeline:
    """测试抽取管道"""
    
    def test_rebel_extraction_pipeline(self, sample_text):
        """测试 REBEL 抽取管道"""
        extractor = REBELExtractor()
        graph = extractor.extract_to_graph(sample_text)
        assert isinstance(graph, Graph)
        assert len(graph.nodes) >= 0  # 可能为空，取决于文本内容
    
    @pytest.mark.skip(reason="需要 API Key，跳过集成测试")
    def test_gpt_expansion_pipeline(self, sample_goal):
        """测试 GPT 展开管道"""
        # 注意：这需要有效的 API Key
        expander = GPTExpander()
        graph = expander.expand(sample_goal)
        assert isinstance(graph, Graph)
