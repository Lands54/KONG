"""
IText2KG 抽取器单元测试

原则：
- 完全 mock 外部依赖（LLM/embeddings/itext2kg）
- 不依赖真实 API key
- 只测试抽取器本身的逻辑
"""

import pytest
from unittest.mock import Mock, MagicMock


class TestIText2KGExtractor:
    """IText2KGExtractor 单元测试"""
    
    def test_extractor_can_be_instantiated(self):
        """测试抽取器可以被实例化（接受 mock 的依赖）"""
        from dynhalting.extractors.itext2kg_extractor import IText2KGExtractor
        
        mock_llm = Mock()
        mock_embeddings = Mock()
        
        extractor = IText2KGExtractor(
            llm_model=mock_llm,
            embeddings_model=mock_embeddings,
        )
        
        assert extractor is not None
        assert extractor.llm_model is mock_llm
        assert extractor.embeddings_model is mock_embeddings
    
    def test_extract_to_graph_with_mock_atom(self, monkeypatch):
        """测试 extract_to_graph 能正确调用 ATOM 并转换结果"""
        from dynhalting.extractors.itext2kg_extractor import IText2KGExtractor
        from dynhalting.core.graph import Graph
        
        mock_llm = Mock()
        mock_embeddings = Mock()
        
        # Mock itext2kg.Atom
        mock_atom = MagicMock()
        
        # Mock build_graph 返回的 KnowledgeGraph（带 relationships）
        # 使用 spec 限制 Mock 只有特定属性
        mock_subj = Mock()
        mock_subj.name = "Paris"
        mock_obj = Mock()
        mock_obj.name = "France"
        
        mock_rel = Mock()
        mock_rel.startEntity = mock_subj
        mock_rel.endEntity = mock_obj
        mock_rel.name = "capital_of"
        
        # 用 spec 确保 hasattr 行为正确
        mock_kg = Mock(spec=['relationships'])
        mock_kg.relationships = [mock_rel]
        
        mock_atom.build_graph.return_value = mock_kg
        
        # Mock Atom 类
        mock_atom_class = Mock(return_value=mock_atom)
        monkeypatch.setattr("itext2kg.atom.Atom", mock_atom_class)
        
        extractor = IText2KGExtractor(
            llm_model=mock_llm,
            embeddings_model=mock_embeddings,
            max_atomic_facts=10,
        )
        
        graph = extractor.extract_to_graph("Paris is the capital of France.")
        
        assert isinstance(graph, Graph)
        assert len(graph.edges) >= 1
        assert graph.metadata.get("extractor") == "itext2kg"
        
        # 验证 Atom 被正确调用
        mock_atom_class.assert_called_once_with(
            llm_model=mock_llm,
            embeddings_model=mock_embeddings
        )
        mock_atom.build_graph.assert_called_once()
    
    def test_extract_empty_text_returns_empty_graph(self):
        """测试空文本返回空图"""
        from dynhalting.extractors.itext2kg_extractor import IText2KGExtractor
        
        mock_llm = Mock()
        mock_embeddings = Mock()
        
        extractor = IText2KGExtractor(
            llm_model=mock_llm,
            embeddings_model=mock_embeddings,
        )
        
        # 不需要 mock Atom，因为空文本会提前返回
        graph = extractor.extract_to_graph("")
        
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0
        assert graph.metadata.get("reason") == "empty_input"
    
    def test_factory_creates_itext2kg_extractor(self, monkeypatch):
        """测试 Factory 可以通过 builder 创建 itext2kg 抽取器"""
        from backend.python_service.core.factory import ExtractorFactory
        
        # Mock 环境变量
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-12345")
        
        # Mock LangChain imports
        mock_chat_openai = Mock()
        mock_openai_embeddings_class = Mock()
        mock_sentence_transformer = Mock()
        
        monkeypatch.setattr("langchain_openai.ChatOpenAI", mock_chat_openai)
        monkeypatch.setattr("sentence_transformers.SentenceTransformer", mock_sentence_transformer)
        
        # Mock itext2kg
        mock_atom_class = Mock()
        monkeypatch.setattr("itext2kg.atom.Atom", mock_atom_class)
        
        params = {
            "chat_model": "google/gemini-2.5-flash-lite",
            "embeddings_model": "sentence-transformers/all-MiniLM-L6-v2",
        }
        
        extractor = ExtractorFactory.create("itext2kg", params)
        
        assert extractor is not None
        # 验证 LLM 被构建
        mock_chat_openai.assert_called_once()
