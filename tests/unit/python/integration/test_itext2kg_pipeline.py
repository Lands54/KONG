"""
IText2KG 集成测试（真实调用）

要求：
- 环境变量 OPENROUTER_API_KEY 必须已设置（可在项目根目录 .env 文件中）
- 会发起真实 API 调用（极小输入，控制成本）
- 验证端到端流程：文本 -> itext2kg -> Graph
"""

import pytest
import os
from pathlib import Path


@pytest.fixture(scope="module", autouse=True)
def load_env_for_integration():
    """
    集成测试前加载项目根目录 .env
    
    职责分离：
    - 测试侧负责准备环境（加载 .env）
    - 抽取器/builder 只负责读取环境变量
    """
    try:
        from dotenv import load_dotenv  # type: ignore
        
        # 查找项目根目录 .env
        current = Path(__file__).resolve()
        for parent in current.parents:
            env_file = parent / ".env"
            if env_file.exists():
                load_dotenv(env_file)
                print(f"[Integration Test] 已加载 .env: {env_file}")
                break
    except ImportError:
        print("[Integration Test] 警告: python-dotenv 未安装，无法自动加载 .env")


@pytest.mark.integration
def test_itext2kg_extraction_pipeline_live():
    """
    真实调用 itext2kg/ATOM 的端到端测试
    
    需要：
    - OPENROUTER_API_KEY 环境变量已设置
    - 网络连接
    - 极小输入（控制成本）
    """
    from backend.python_service.core.factory import ExtractorFactory
    from dynhalting.core.graph import Graph
    
    # 前置检查：环境变量是否设置
    if not os.getenv("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY 未设置，跳过集成测试")
    
    # 通过 Factory 创建（会自动调用 builder）
    extractor = ExtractorFactory.create(
        "itext2kg",
        params={
            "chat_model": "google/gemini-2.5-flash-lite",
            "embeddings_model": "sentence-transformers/all-MiniLM-L6-v2",
            "llm_max_tokens": 256,
            "llm_timeout": 60,
            "llm_max_retries": 0,
            "max_atomic_facts": 1,
            "max_chars_per_fact": 200,
            "max_workers": 1,
        }
    )
    
    text = "Paris is the capital of France."
    graph = extractor.extract_to_graph(text)
    
    assert isinstance(graph, Graph)
    assert len(graph.edges) >= 1, "应至少抽取到 1 条关系"
    assert graph.metadata.get("extractor") == "itext2kg"
    
    print(f"✓ 成功抽取: {len(graph.nodes)} 节点, {len(graph.edges)} 边")
