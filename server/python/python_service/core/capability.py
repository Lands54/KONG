from typing import Any, Dict, Type, Callable
from kgforge.protocols import IConfigurable, IPreloadable
from kgforge import get_logger

logger = get_logger(__name__)

class CapabilityViolationError(Exception):
    """当组件声称拥有某种能力但未履行契约时抛出"""
    pass

class CapabilityManager:
    """
    契约驱动的能力执行系统。
    管理 'Configurable', 'Preloadable' 等标准能力的生命周期。
    """
    
    _handlers: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register_capability(cls, name: str, protocol: Type, handler: Callable):
        cls._handlers[name] = {"protocol": protocol, "handler": handler}

    @classmethod
    def enforce(cls, instance: Any, capability_name: str, *args, **kwargs) -> Any:
        if capability_name not in cls._handlers:
            raise KeyError(f"Unknown Capability: {capability_name}")

        cap_def = cls._handlers[capability_name]
        protocol = cap_def["protocol"]
        handler = cap_def["handler"]

        if not isinstance(instance, protocol):
            raise CapabilityViolationError(
                f"Component '{type(instance).__name__}' claims '{capability_name}' "
                f"but does not implement '{protocol.__name__}'."
            )

        try:
            return handler(instance, *args, **kwargs)
        except Exception as e:
            logger.error(f"Capability execution failed [{capability_name}]: {e}")
            raise

    @staticmethod
    def _handle_config(instance: Any, params: Dict[str, Any]):
        instance.update_config(params)

    @staticmethod
    def _handle_preload(instance: Any):
        instance.preload()

# 自动注册标准能力
CapabilityManager.register_capability("Configurable", IConfigurable, CapabilityManager._handle_config)
CapabilityManager.register_capability("Preloadable", IPreloadable, CapabilityManager._handle_preload)
