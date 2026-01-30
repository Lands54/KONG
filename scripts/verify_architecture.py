from dynhalting.core.engine import ComponentManager
import os
import sys

def test_new_architecture():
    print("开始验证脚本...", flush=True)
    # 初始化管理器，指向组件根目录
    project_root = "/Users/qiuboyu/CodeLearning/KONG"
    components_root = os.path.join(project_root, "dynhalting/components")
    
    print(f"组件目录: {components_root}", flush=True)
    manager = ComponentManager(components_root)
    
    # 1. 扫描并加载所有模块
    print("--- 正在扫描模块 ---", flush=True)
    try:
        manager.reload_all()
    except Exception as e:
        print(f"扫描模块失败: {e}", file=sys.stderr, flush=True)
        return
        
    # 2. 查看加载状态
    status = manager.get_status()
    for cat, info in status.items():
        print(f"类别: {cat}", flush=True)
        print(f"  可用模块: {info['available']}", flush=True)
    
    # 3. 热切换尝试 (不运行实际逻辑以免卡死)
    print("\n--- 测试热切换 (Extractor: rebel) ---", flush=True)
    try:
        rebel = manager.extractors.switch("rebel", config={"device": "cpu"})
        print(f"成功切换到器具: {rebel.name}", flush=True)
    except Exception as e:
        print(f"切换失败: {e}", flush=True)

if __name__ == "__main__":
    test_new_architecture()
    print("验证结束。", flush=True)
