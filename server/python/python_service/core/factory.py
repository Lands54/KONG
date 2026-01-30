"""
Unified Factory (Thread-Safe Version)
引入“影子实例”机制，解决预热单例在多任务并发时的状态污染问题。
"""

import copy
from typing import Dict, Any, Optional
from .engine import engine
from .capability import CapabilityManager
from kgforge import get_logger

logger = get_logger(__name__)

class UnifiedFactory:
    """
    统一工厂
    """
    
    @classmethod
    def create_component(cls, category: str, name: str, params: Optional[Dict[str, Any]] = None) -> Any:
        params = (params or {}).copy()
        
        # --- Stage 1: 预热缓存与影子化 ---
        from python_service.services.lifecycle import warmer
        base_instance = warmer.get_instance(category, name)
        
        if base_instance:
            if not params:
                # 如果没有新参数，直接复用单例（最快路径）
                return base_instance
            
            # 核心修复：如果存在新参数，坚决不修改单例原件
            # 通过浅拷贝创建一个影子实例 (Shadow Instance)
            # 这样：配置是私有的，但底层的重型资源（如权重、连接）是共享的
            logger.info(f"Creating shadow instance for preloaded {category}.{name} to avoid state pollution.")
            instance = copy.copy(base_instance)
            
            spec = instance.get_component_spec() if hasattr(instance, "get_component_spec") else {}
            if "Configurable" in spec.get("capabilities", []):
                try:
                    CapabilityManager.enforce(instance, "Configurable", params)
                except Exception as e:
                    logger.warning(f"Failed to apply local config to shadow {category}.{name}: {e}")
            return instance
            
        # --- Stage 2: 动态加载 ---
        comp_class = engine.get_class(category, name)
        if comp_class is None:
            raise ValueError(f"Unknown component: {category}/{name}")
            
        # --- Stage 3: 递归解决插槽 (保持原有逻辑) ---
        spec = comp_class.get_component_spec() if hasattr(comp_class, "get_component_spec") else {}
        slots = spec.get("slots", {})
        
        if slots:
            for slot_name, interface_name in slots.items():
                slot_value = params.get(slot_name)
                comp_id = slot_value if isinstance(slot_value, str) else None
                child_cat = engine.resolve_category(interface_name)
                
                if comp_id is None and child_cat:
                     available = engine.list_ids(child_cat)
                     if available:
                         comp_id = available[0]

                if comp_id and child_cat:
                    child_params = params.get(f"{slot_name}_params", {})
                    params[slot_name] = cls.create_component(child_cat, comp_id, params=child_params)
            
            # 清理递归注入参数
            for slot_name in slots: params.pop(f"{slot_name}_params", None)

        # --- Stage 4: 实例化 (新建实例天然安全) ---
        try:
            return comp_class(**params)
        except Exception as e:
            logger.error(f"Failed to instantiate {category}.{name}: {e}")
            raise RuntimeError(f"Instantiation error [{category}.{name}]: {e}") from e

    def __class_getitem__(cls, category: str):
        return type(f"{category.capitalize()}Factory", (), {
            "create": staticmethod(lambda name, params=None: cls.create_component(category, name, params))
        })
