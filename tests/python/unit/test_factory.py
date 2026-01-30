import pytest
from python_service.core.factory import UnifiedFactory
from python_service.core.engine import engine

def test_unified_factory_creation():
    """测试通用工厂创建组件（及递归插槽解决）"""
    orchestrator = UnifiedFactory.create_component("orchestrators", "fuzz_test")
    assert orchestrator is not None
    assert hasattr(orchestrator, "run")

def test_unified_factory_getitem_magic():
    """测试 [category] 元编程工厂语法"""
    factory = UnifiedFactory["orchestrators"]
    orchestrator = factory.create("fuzz_test")
    assert orchestrator is not None
    assert orchestrator.get_component_spec()["id"] == "fuzz_test"
    
def test_recursive_slot_resolution():
    """测试递归插槽物化逻辑"""
    # dynamic_halting 會自動尋找並實例化其引用的 extractor
    orchestrator = UnifiedFactory.create_component("orchestrators", "dynamic_halting")
    assert hasattr(orchestrator, "extractor")
    assert not isinstance(orchestrator.extractor, str) # 应该是个对象
