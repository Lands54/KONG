"""
验证后端纯度测试
确保 backend/python_service 不直接依赖算法实现，而是通过工厂/注册表加载
同时确保所有路径和命名对齐已完成
"""

import sys
import os
from pathlib import Path

# 获取项目根目录并添加到 sys.path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 添加 python_service 及其子目录到 sys.path
python_service_path = os.path.join(project_root, "backend", "python_service")
if python_service_path not in sys.path:
    sys.path.insert(0, python_service_path)

def test_registry_and_factories():
    print("--- 验证 Registry 和 Factories ---")
    try:
        from core.module_registry import get_registry
        registry = get_registry()
        
        # 验证 fusions 和 processors 和 haltings 命名
        fusions = registry.list_fusions()
        processors = registry.list_processors()
        haltings = registry.list_haltings()
        
        print(f"✓ 注册表融合器列表: {fusions}")
        print(f"✓ 注册表处理器列表: {processors}")
        print(f"✓ 注册表判停策略列表: {haltings}")
        
        assert "fusion" in fusions
        assert "dedup" in processors
        assert "ASI" in haltings
        
        # 验证 Factory
        from core.factory import HaltingFactory, FusionFactory, ProcessorFactory
        
        asi_class = registry.get_halting_class("ASI")
        print(f"✓ ASI 策略类路径: {asi_class.__module__}.{asi_class.__name__}")
        assert "dynhalting.components.halting.utils.halting_strategies" in asi_class.__module__
        
        processor_class = registry.get_processor_class("dedup")
        print(f"✓ Dedup 处理器路径: {processor_class.__module__}.{processor_class.__name__}")
        assert "dynhalting.components.processors.utils.semantic_deduplicator" in processor_class.__module__

        # 验证 Orchestrator
        orchestrators = registry.list_orchestrators()
        print(f"✓ 注册表编排器列表: {orchestrators}")
        assert "dynamic_halting" in orchestrators

        orchestrator_class = registry.get_orchestrator_class("dynamic_halting")
        print(f"✓ Dynamic Halting 编排器路径: {orchestrator_class.__module__}.{orchestrator_class.__name__}")
        assert "backend.python_service.components.orchestrators.dynamic_halting" in orchestrator_class.__module__
        
        print("✓ Registry 和 Factories 验证通过\n")
        return True
    except Exception as e:
        print(f"✗ Registry/Factories 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_purity_checks():
    print("--- 验证后端纯度 (无遗留算法目录) ---")
    halting_strategies_path = os.path.join(python_service_path, "halting", "strategies")
    halt_engine_path = os.path.join(python_service_path, "halting", "halt_engine.py")
    
    deleted_paths = [halting_strategies_path, halt_engine_path]
    all_clear = True
    
    for path in deleted_paths:
        if os.path.exists(path):
            print(f"✗ 错误: 发现遗留路径: {path}")
            all_clear = False
        else:
            print(f"✓ 已确认路径不存在: {path}")
            
    if all_clear:
        print("✓ 后端纯度验证通过\n")
    return all_clear

def test_imports_cleanliness():
    print("--- 验证导入清洁度 ---")
    try:
        # 尝试导入 backend 下可能存在的旧模块（应该失败）
        try:
            import backend.python_service.halting.strategies.asi_evaluator
            print("✗ 错误: backend.python_service.halting.strategies.asi_evaluator 仍然可以导入!")
            return False
        except ImportError:
            print("✓ 无法导入旧的 asi_evaluator (正确)")
            
        print("✓ 导入清洁度验证通过\n")
        return True
    except Exception as e:
        print(f"✗ 导入验证过程中出错: {e}")
        return False

if __name__ == "__main__":
    v1 = test_registry_and_factories()
    v2 = test_purity_checks()
    v3 = test_imports_cleanliness()
    
    if v1 and v2 and v3:
        print("All backend purity tests PASSED!")
        sys.exit(0)
    else:
        print("Some backend purity tests FAILED!")
        sys.exit(1)
