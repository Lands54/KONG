import pytest
from python_service.services.lifecycle import warmer
from python_service.core.capability import CapabilityManager
from kgforge.protocols.interfaces import IConfigurable, IDescribable

def test_warmer_status_initial():
    """测试 LifecycleManager 状态"""
    status = warmer.get_status_report()
    assert isinstance(status, dict)

def test_capabilities():
    """测试能力契约执行"""
    class MockComp(IConfigurable, IDescribable):
        def __init__(self): self.val = 0
        def update_config(self, p): self.val = p.get("v", 0)
        @classmethod
        def get_component_spec(cls): return {"capabilities": ["Configurable"]}

    obj = MockComp()
    CapabilityManager.enforce(obj, "Configurable", {"v": 100})
    assert obj.val == 100
