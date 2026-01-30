import requests
import json
import time

def run_fuzz_test(node_count=100, iterations=5):
    url = "http://localhost:8000/api/v1/infer"
    
    payload = {
        "goal": "Fuzz Test Goal",
        "text": "This is a dummy text for fuzz testing.",
        "orchestrator": "fuzz_test",  # 指定刚刚创建的 Fuzz 编排器
        "params": {
            "node_count": node_count,
            "iteration_count": iterations,
            "attribute_complexity": 20, # 高复杂度 JSON
            "edge_density": 0.2
        }
    }
    
    print(f"🚀 发送 Fuzz 请求: nodes={node_count}, iterations={iterations}")
    start_time = time.time()
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            # print(json.dumps(data, indent=2))
            
            graph = data.get("graph", {})
            nodes = graph.get("nodes", {})
            edges = graph.get("edges", [])
            
            print("\n✅ Fuzz 测试成功!")
            print(f"⏱️  耗时: {time.time() - start_time:.2f}s")
            print(f"📊 最终图规模: {len(nodes)} Nodes, {len(edges)} Edges")
            print(f"💾 中间状态图数量: {len(data.get('intermediate_graphs', {}))}")
            
            # 简单的验证
            if len(nodes) < node_count * 0.9: # 考虑到随机性，大致范围
                print("⚠️ 警告: 节点数量似乎少于预期")
            
        else:
            print(f"\n❌ Fuzz 测试失败: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")

if __name__ == "__main__":
    # 可以调整压力
    run_fuzz_test(node_count=200, iterations=3)
