import os
import sys
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from python_service.core.engine import engine
from kgforge import get_logger

logger = get_logger(__name__)

class ComponentReloader(FileSystemEventHandler):
    """
    监控组件目录变动并触发热重载
    """
    def __init__(self, watch_path: str):
        self.watch_path = os.path.abspath(watch_path)
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        filename = event.src_path
        if not filename.endswith(".py"):
            return
            
        # 忽略缓存和临时文件
        if "__pycache__" in filename or filename.startswith("."):
            return
            
        try:
            # 将文件路径转换为 Python 模块路径
            # e.g., /app/core/kgforge/components/extractors/foo.py -> kgforge.components.extractors.foo
            
            # 1. 找到相对于项目根目录的路径
            # 我们假设 watch_path 是 core/kgforge/components，但我们需要完整的包名
            # 最可靠的方法是查找 sys.path 中的哪个路径包含此文件
            
            module_name = self._resolve_module_name(filename)
            if not module_name:
                return

            logger.info(f"[HotReload] Detected change in {module_name}, reloading...")
            engine.reload_module(module_name)
            logger.info(f"[HotReload] ✓ Module {module_name} reloaded successfully.")
            
        except Exception as e:
            logger.error(f"[HotReload] Failed to reload {filename}: {e}")

    def _resolve_module_name(self, filepath: str) -> str:
        """
        根据文件路径反推模块名
        """
        # 简单策略：遍历 sys.path 尝试匹配
        filepath = os.path.abspath(filepath)
        best_match_path = ""
        best_match_module = ""
        
        for p in sys.path:
            abs_p = os.path.abspath(p)
            if filepath.startswith(abs_p):
                # 找到匹配的前缀
                if len(abs_p) > len(best_match_path):
                    best_match_path = abs_p
                    rel_path = os.path.relpath(filepath, abs_p)
                    # remove .py
                    rel_path = rel_path[:-3]
                    best_match_module = rel_path.replace(os.path.sep, ".")
        
        return best_match_module

def start_hot_reload_service(path_to_watch: str):
    """
    启动热重载监控服务 (后台线程)
    """
    if not os.path.exists(path_to_watch):
        logger.warning(f"[HotReload] Watch path does not exist: {path_to_watch}")
        return

    logger.info(f"[HotReload] Starting filesystem watcher on: {path_to_watch}")
    
    event_handler = ComponentReloader(path_to_watch)
    observer = Observer()
    observer.schedule(event_handler, path_to_watch, recursive=True)
    
    # 守护线程运行
    observer_thread = threading.Thread(target=observer.start, daemon=True)
    observer_thread.start()
