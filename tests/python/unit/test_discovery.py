import pytest
from python_service.core.engine import engine

def test_engine_scan():
    """测试引擎全量扫描功能"""
    catalog = engine.scan_all()
    assert isinstance(catalog, dict)
    assert "extractors" in catalog
    assert "orchestrators" in catalog
    
    # 验证关键组件是否存在
    orchestrator_ids = [s["id"] for s in catalog["orchestrators"]]
    assert "dynamic_halting" in orchestrator_ids
    assert "fuzz_test" in orchestrator_ids

def test_engine_get_class():
    """测试类加载逻辑"""
    cls = engine.get_class("orchestrators", "fuzz_test")
    assert cls is not None
    assert cls.__name__ == "FuzzTestOrchestratorAppliance"

def test_engine_resolve_category():
    """测试接口到类别的反向解析"""
    assert engine.resolve_category("IExtractor") == "extractors"
    assert engine.resolve_category("IOrchestrator") == "orchestrators"
