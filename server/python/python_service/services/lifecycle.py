"""
Lifecycle Manager / Component Warmer
负责管理长生命周期组件（如 LLM, Embedding 模型）的预热与缓存。
"""

import threading
from typing import Dict, Any, Optional
from python_service.core.engine import engine
from python_service.core.capability import CapabilityManager
from kgforge import get_logger

logger = get_logger(__name__)

class LifecycleManager:
    """组件生命周期管理器 (原 ComponentWarmer)"""
    
    def __init__(self):
        self._instances: Dict[str, Any] = {}
        self._status: Dict[str, Dict[str, str]] = {}
        self._lock = threading.Lock()

    def get_instance(self, category: str, name: str) -> Optional[Any]:
        return self._instances.get(f"{category}.{name}")

    def warmup_all(self):
        """核心预热逻辑：自动预热所有在 Spec 中声明了 can_preload 的组件"""
        catalog = engine.scan_all()
        for category, components in catalog.items():
            for spec in components:
                if spec.get("can_preload"):
                    self._warm_individual(category, spec["id"])

    def _warm_individual(self, category: str, name: str):
        key = f"{category}.{name}"
        if key in self._instances: return

        try:
            logger.info(f"Warming up component: {key}...")
            self._set_status(category, name, "loading")
            
            # 使用工厂创建（它会自动跳过本缓存进入 Stage 2）
            from python_service.core.factory import UnifiedFactory
            instance = UnifiedFactory.create_component(category, name)
            
            # 执行预热动作 (契约)
            CapabilityManager.enforce(instance, "Preloadable")
            
            with self._lock:
                self._instances[key] = instance
            
            self._set_status(category, name, "ready")
            logger.info(f"✓ {key} is ready")
        except Exception as e:
            logger.error(f"Failed to warm up {key}: {e}")
            self._set_status(category, name, f"error: {str(e)}")

    def _set_status(self, category: str, name: str, status: str):
        if category not in self._status: self._status[category] = {}
        self._status[category][name] = status

    def get_status_report(self) -> Dict[str, Any]:
        return self._status

# 单例
warmer = LifecycleManager()

def preload_all():
    """API 启动热钩子"""
    warmer.warmup_all()
