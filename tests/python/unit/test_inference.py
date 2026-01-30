import pytest
from python_service.services.inference import InferenceEngine

@pytest.fixture
def engine():
    return InferenceEngine()

def test_inference_engine_run_fuzz(engine, sample_text, sample_goal):
    """测试新版推理引擎"""
    result = engine.run_dynamic(
        goal=sample_goal,
        text=sample_text,
        orchestrator="fuzz_test",
        params={"node_count": 5}
    )
    
    assert result["status"] == "success"
    assert "graph" in result
    assert result["metadata"]["orchestrator_id"] == "fuzz_test"
    assert len(result["graph"]["nodes"]) >= 5

def test_inference_engine_error(engine):
    """测试错误处理"""
    with pytest.raises(RuntimeError):
        engine.run_dynamic(goal="", text="", orchestrator="non_existent")
