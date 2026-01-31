
import time
import uuid
import random
from typing import Any, Dict, List, Optional
from kgforge.components.base import BaseOrchestrator, TaskCancelledError
from kgforge.models import Graph, Node, Edge
from kgforge.models.experiment_result import ExperimentResult
from kgforge.utils import get_logger

logger = get_logger(__name__)

class FuzzTestOrchestratorAppliance(BaseOrchestrator):
    """
    模糊测试编排器 (FuzzTestOrchestrator)
    
    不依赖真实 LLM，而是模拟一个完整的编排流程：
    1. 模拟网络延迟和思考时间
    2. 生成随机结构的图数据
    3. 全流程发送 Telemetry 事件
    4. 响应取消信号
    
    用于：前端 UI 调试、系统稳定性测试、链路连通性验证。
    """
    name = "fuzz_test"
    display_name = "Mock模糊测试编排器"

    def __init__(self, config: Dict[str, Any] = None, **kwargs):
        super().__init__(config or {})
        self.delay_ms = int(kwargs.get("delay_ms", 1000))
        self.max_nodes = int(kwargs.get("max_nodes", 20))
        self.max_loops = int(kwargs.get("max_loops", 5))
    
    @classmethod
    def get_required_slots(cls) -> Dict[str, str]:
        return {} # 自包含 Mock 逻辑，不需要外部组件

    @classmethod
    def get_component_spec(cls) -> Dict[str, Any]:
        return {
            "id": "fuzz_test",
            "name": "Mock模糊测试编排器",
            "slots": {},
            "description": "用于系统压力测试和UI调试的虚拟编排器，不产生LLM消耗，支持模拟延迟和动态图生成。",
            "params": {
                "delay_ms": {
                    "type": "integer",
                    "default": 1000,
                    "description": "每步模拟延迟(ms)"
                },
                "max_loops": {
                    "type": "integer",
                    "default": 5,
                    "description": "模拟循环次数"
                }
            }
        }

    def _sleep(self, ms: int):
        """可中断的睡眠"""
        chunks = ms // 100
        for _ in range(chunks):
            self.check_cancellation()
            time.sleep(0.1)

    def _create_mock_graph(self, prefix: str, node_count: int) -> Graph:
        g = Graph(graph_id=f"mock_{prefix}_{uuid.uuid4().hex[:4]}")
        
        # Central Node
        center_id = f"{prefix}_ROOT"
        g.add_node(Node(node_id=center_id, label=f"{prefix} 核心", attributes={"type": "root", "score": 0.99}))
        
        for i in range(node_count):
            nid = f"{prefix}_NODE_{i}"
            g.add_node(Node(node_id=nid, label=f"{prefix} 概念 {i}", attributes={"type": "concept", "score": random.random()}))
            
            # Link to root or random previous
            target = center_id if i == 0 or random.random() > 0.7 else f"{prefix}_NODE_{random.randint(0, i-1)}"
            g.add_edge(Edge(source=nid, target=target, relation="related_to"))
            
        return g

    def run(self, goal: str, text: str, verbose: bool = True, **kwargs) -> ExperimentResult:
        logger.info(f"--- [FuzzTest] 开始模拟任务: {goal} ---")
        
        start_time = time.time()
        result = ExperimentResult(graph=Graph(graph_id="fuzz_final"))
        result.set_metadata("goal", goal)
        result.set_metadata("engine", "FuzzTestOrchestrator")
        
        current_graph = Graph(graph_id="main")

        try:
            # 1. Mock G_B (Bottom-Up)
            logger.info("Step 1: 模拟 Bottom-Up 抽取 (G_B)...")
            self._sleep(self.delay_ms)
            graph_b = self._create_mock_graph("B", 5)
            result.log_graph("G_B", graph_b)
            logger.telemetry({"intermediate_stats": {"G_B": {"node_count": len(graph_b.nodes), "edge_count": len(graph_b.edges), "source": "mock_extractor"}}})
            
            # Merge to main
            for n in graph_b.nodes.values(): current_graph.add_node(n)
            for e in graph_b.edges: current_graph.add_edge(e)

            # 2. Mock G_T (Top-Down)
            logger.info("Step 2: 模拟 Top-Down 展开 (G_T)...")
            self._sleep(self.delay_ms)
            graph_t = self._create_mock_graph("T", 3)
            result.log_graph("G_T", graph_t)
            logger.telemetry({"intermediate_stats": {"G_T": {"node_count": len(graph_t.nodes), "edge_count": len(graph_t.edges), "source": "mock_expander"}}})

            # Merge to main
            for n in graph_t.nodes.values(): current_graph.add_node(n)
            for e in graph_t.edges: current_graph.add_edge(e)
            
            # 3. Fuse
            logger.info("Step 3: 模拟融合 (G_F)...")
            self._sleep(self.delay_ms // 2)
            result.log_graph("G_F", current_graph) # Snapshot
            logger.telemetry({"intermediate_stats": {"G_F": {"node_count": len(current_graph.nodes), "edge_count": len(current_graph.edges), "source": "mock_fusion"}}})

            # 4. Loops
            for i in range(1, self.max_loops + 1):
                logger.info(f"Step 4.{i}: 模拟推理循环...")
                self._sleep(self.delay_ms)
                
                # Increment
                inc_graph = self._create_mock_graph(f"L{i}", random.randint(2, 5))
                
                # Merge
                for n in inc_graph.nodes.values(): current_graph.add_node(n)
                # Link new nodes to existing random nodes
                if len(current_graph.nodes) > 0:
                    existing_ids = list(current_graph.nodes.keys())
                    for n in inc_graph.nodes.values():
                        target = random.choice(existing_ids)
                        current_graph.add_edge(Edge(source=n.id, target=target, relation="inferred_link"))

                result.log_step(f"loop_{i}", {"nodes_added": len(inc_graph.nodes)})
                logger.telemetry({"intermediate_stats": {f"LOOP_{i}": {"node_count": len(current_graph.nodes), "edge_count": len(current_graph.edges), "depth": i, "source": "mock_loop"}}})
            
            # Finish
            result.graph = current_graph
            result.finish(final_decision="HALT", success=True)
            logger.info("--- [FuzzTest] 模拟完成 ---")
            
            return result

        except TaskCancelledError:
            logger.warning("[FuzzTest] 任务被用户取消!")
            result.finish(final_decision="CANCELLED", success=False)
            return result
        except Exception as e:
            logger.error(f"[FuzzTest] 模拟异常: {e}")
            raise e
