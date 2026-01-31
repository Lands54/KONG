import importlib
import inspect
import pkgutil
import sys
from typing import Dict, List, Any, Type, Optional
from kgforge.protocols import IDescribable
from kgforge.protocols.interfaces import META_REGISTRY, IPreloadable

class ComponentEngine:
    """
    PRISM 组件引擎 (SSOT Engine)
    统一管理扫描、发现、ID解析与动态工厂生成。
    """
    
    def __init__(self):
        self._categories = {}
        self._class_cache: Dict[str, Type] = {}
        self._spec_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._category_map = {} # Interface Name -> Category
        
        self._initialize_protocols()

    def _initialize_protocols(self):
        """从核心协议定义初始化映射关系"""
        for p in META_REGISTRY:
            if hasattr(p, 'category'):
                self._categories[p.category] = p
                self._category_map[p.__name__] = p.category

    def scan_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """全量扫描物理组件包并导出 Spec 蓝图"""
        results = {cat: [] for cat in self._categories}
        
        import kgforge.components as components_pkg
        pkg_path = components_pkg.__path__
        
        # 递归扫描
        for _, module_name, _ in pkgutil.walk_packages(pkg_path, components_pkg.__name__ + "."):
            if any(part in module_name.split('.') for part in ['utils', 'base']):
                continue
                
            try:
                module = importlib.import_module(module_name)
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    # 必须是本项目定义的类，且是非抽象的 IDescribable
                    if obj.__module__ != module_name: continue
                    if issubclass(obj, IDescribable) and not inspect.isabstract(obj):
                        # 分类归属
                        for cat, interface in self._categories.items():
                            if issubclass(obj, interface):
                                spec = obj.get_component_spec()
                                spec["class_path"] = f"{module_name}.{obj.__name__}"
                                spec["can_preload"] = issubclass(obj, IPreloadable)
                                
                                # 针对编排器提取插槽信息
                                if cat == "orchestrators" and hasattr(obj, "get_required_slots"):
                                    spec["slots"] = obj.get_required_slots()
                                
                                if not any(existing["id"] == spec["id"] for existing in results[cat]):
                                    results[cat].append(spec)
                                break
            except Exception:
                continue
        
        self._spec_cache = results
        return results

    def get_class(self, category: str, component_id: str) -> Optional[Type]:
        """根据类别和 ID 加载类对象"""
        cache_key = f"{category}.{component_id}"
        if cache_key in self._class_cache:
            return self._class_cache[cache_key]
            
        if not self._spec_cache:
            self.scan_all()
            
        for spec in self._spec_cache.get(category, []):
            if spec["id"] == component_id:
                path_parts = spec["class_path"].split(".")
                module_name = ".".join(path_parts[:-1])
                class_name = path_parts[-1]
                module = importlib.import_module(module_name)
                cls = getattr(module, class_name)
                self._class_cache[cache_key] = cls
                return cls
        return None

    def resolve_category(self, interface_name: str) -> Optional[str]:
        """接口名到类别名的映射"""
        return self._category_map.get(interface_name)

    def list_ids(self, category: str) -> List[str]:
        """列出某个类别下所有可见的组件 ID"""
        if not self._spec_cache:
            self.scan_all()
        return [spec["id"] for spec in self._spec_cache.get(category, [])]

    def reload_module(self, module_name: str):
        """
        动态重载模块 (Hot-Reload)
        
        策略：
        1. 从 sys.modules 移除目标模块
        2. 清除相关类的缓存 (_class_cache)
        3. 重新扫描注册表 (触发重新 import 和自省)
        """
        # 1. Evict from sys.modules
        if module_name in sys.modules:
            del sys.modules[module_name]
        
        # 2. Clear internal caches
        # 我们需要清除使用了该 module 的所有缓存条目
        keys_to_remove = []
        for key, cls in self._class_cache.items():
            if cls.__module__ == module_name:
                keys_to_remove.append(key)
        
        for k in keys_to_remove:
            del self._class_cache[k]
            
        # 3. Force Re-scan to update Specs
        # TODO: 优化为增量扫描？目前为了安全起见全量扫描
        self.scan_all()
        return True

# 单例入口
engine = ComponentEngine()
