import random
import uuid
import time
from typing import Any, Dict, List

from kgforge.components.base import BaseOrchestrator
from kgforge.models import Graph, Node, Edge, ExperimentResult
from kgforge.utils import get_logger

logger = get_logger(__name__)

class WeirdObjectWithToDict:
    """实现了 to_dict 协议的怪异对象"""
    def __init__(self, name: str):
        self.name = name
        self.secret = 42
    def to_dict(self):
        return {"type": "CustomObject", "name": self.name, "value": self.secret, "timestamp": time.time()}

class WeirdObjectStandard:
    """仅有标准魔法方法的怪异对象"""
    def __str__(self):
        return f"<MagicObject_at_{id(self)}>"
    def __repr__(self):
        return self.__str__()

class FuzzTestOrchestratorAppliance(BaseOrchestrator):
    """
    Fuzz 测试编排器
    
    用于对后端存储（JSON Slot, Variable Graph Storage）进行压力测试和边界条件测试。
    不依赖真实模型，而是生成随机的大规模/畸形数据。
    """
    name = "fuzz_test"
    display_name = "Fuzz 测试编排器"

    def __init__(self, config: Dict[str, Any] = None, **kwargs):
        super().__init__(config or {})
        # Fuzz 配置
        self.node_count = self.config.get("node_count", 100)
        self.edge_density = self.config.get("edge_density", 0.1)
        self.iteration_count = self.config.get("iteration_count", 5)
        self.attribute_complexity = self.config.get("attribute_complexity", 10) # 属性字段数量

    @classmethod
    def get_required_slots(cls) -> Dict[str, str]:
        return {}

    @classmethod
    def get_component_spec(cls) -> Dict[str, Any]:
        return {
            "id": "fuzz_test",
            "name": "Fuzz 测试编排器",
            "description": "生成随机大规模图数据和元数据，用于测试存储系统的健壮性",
            "params": {
                "node_count": {"type": "integer", "default": 100, "description": "生成的节点数量"},
                "edge_density": {"type": "number", "default": 0.1, "description": "边密度 (0-1)"},
                "iteration_count": {"type": "integer", "default": 5, "description": "模拟迭代次数"},
                "attribute_complexity": {"type": "integer", "default": 10, "description": "每个节点的随机属性数量"}
            }
        }

    def _generate_random_json(self, complexity: int) -> Dict[str, Any]:
        """生成深层嵌套、类型多样的随机 JSON"""
        data = {}
        types = ["string", "int", "float", "bool", "list", "dict", "null", "weird_obj", "magic_obj", "complex", "set"]
        
        for i in range(complexity):
            key = f"attr_{uuid.uuid4().hex[:6]}"
            t = random.choice(types)
            if t == "string":
                data[key] = "x" * random.randint(10, 100) # 长字符串
            elif t == "int":
                data[key] = random.randint(-10000, 10000)
            elif t == "float":
                data[key] = random.random() * 1000
            elif t == "bool":
                data[key] = random.choice([True, False])
            elif t == "list":
                data[key] = [random.randint(0, 100) for _ in range(3)]
            elif t == "dict":
                data[key] = {"nested_key": "nested_value", "data": [1, 2, 3]}
            elif t == "null":
                data[key] = None
            elif t == "weird_obj":
                data[key] = WeirdObjectWithToDict(f"ChaosNode_{i}")
            elif t == "magic_obj":
                data[key] = WeirdObjectStandard()
            elif t == "complex":
                data[key] = complex(random.random(), random.random())
            elif t == "set":
                data[key] = {random.randint(1, 5) for _ in range(3)}
        return data

    def _generate_random_metrics(self) -> Dict[str, float]:
        """生成随机数值指标"""
        metrics = {}
        for i in range(random.randint(2, 5)):
            metrics[f"metric_{i}"] = random.random() * 100
        # 保留标准指标
        metrics["score"] = random.random()
        metrics["confidence"] = random.uniform(0.5, 1.0)
        metrics["ablation_value"] = random.uniform(0.1, 0.9)
        return metrics

    def _generate_random_state(self) -> Dict[str, Any]:
        """生成随机状态信息"""
        states = ["active", "halted", "pending", "error"]
        return {
            "state": random.choice(states),
            "depth": random.randint(0, 5),
            "visited_count": random.randint(0, 100),
            "flags": [random.choice(["flag_a", "flag_b"]) for _ in range(random.randint(0, 3))]
        }

    def run(self, goal: str, text: str, verbose: bool = True, **kwargs) -> Any:
        logger.info(f"开启极度混乱模式 (Hyper-Chaos) Fuzz 测试: Nodes={self.node_count}")
        
        # 1. 初始化结果
        result = ExperimentResult(graph=Graph(graph_id="hyper_fuzz_graph"))
        result.set_metadata("test_mode", "chaotic_fuzz")
        result.set_metadata("engine_version", "v2.0-chaos")
        
        # 注入大量随机全局指标测试 UI 自适应
        global_metric_pool = ["system_load", "memory_fragmentation", "knowledge_density", "recursive_depth_avg", "logic_consistency_score", "api_token_consumption", "inference_cost_usd"]
        for m_name in global_metric_pool:
            result.record_metric(m_name, random.uniform(0.1, 500.0))
        
        # 注入决策统计
        decisions = ["HALT-CONFIDENCE", "HALT-TIMEOUT", "LOOP-CONTINUE", "LOOP-EXPAND", "RETRY-BACKOFF"]
        for d in decisions:
            for _ in range(random.randint(5, 20)):
                result.log_step("fuzz_decision", {"decision": d})

        current_graph = Graph(graph_id="root")

        # 2. 模拟迭代过程
        for i in range(self.iteration_count):
            logger.info(f"Fuzz Iteration {i+1}/{self.iteration_count}")
            
            step_nodes = []
            count_for_step = self.node_count // self.iteration_count
            
            for _ in range(count_for_step):
                node_id = f"node_{uuid.uuid4().hex[:8]}"
                label = f"ENTITY_NODE" # Simplifying for robustness
                node = Node(node_id, label, type="fuzz")
                
                # 随机填充插槽 (使用新接口)
                for k, v in self._generate_random_json(random.randint(5, 15)).items():
                    node.set_attr(k, v)
                
                for k, v in self._generate_random_metrics().items():
                    node.set_metric(k, v)
                
                # 注入运行时状态 (State Slot)
                runtime_state = self._generate_random_state()
                if random.random() > 0.7:
                    runtime_state["halt_reason"] = random.choice(["ENTROPY_THRESHOLD", "MAX_DEPTH_REACHED", "USER_SIGINT"])
                
                for k, v in runtime_state.items():
                    node.set_state(k, v)
                
                step_nodes.append(node)
                current_graph.add_node(node)

            # 生成随机边
            existing_ids = list(current_graph.nodes.keys())
            if len(existing_ids) > 1:
                target_edge_count = random.randint(1, len(step_nodes) * 2)
                for _ in range(target_edge_count):
                    src = random.choice(existing_ids)
                    tgt = random.choice(existing_ids)
                    if src != tgt:
                        edge = Edge(
                            source=src, target=tgt,
                            relation=random.choice(["CAUSES", "INHIBITS", "MAPS_TO", "UUID_LINK"])
                        )
                        for k, v in self._generate_random_json(3).items():
                            edge.set_meta(k, v)
                        current_graph.add_edge(edge)

            result.log_graph(f"iteration_{i}_graph", current_graph)
            
            # 每一个 step 记录一些混乱的日志项
            result.log_step(f"LOG_{uuid.uuid4().hex[:4]}", {
                "entropy_delta": random.random(),
                "active_threads": random.randint(1, 16),
                "subsystem_check": "OK" if random.random() > 0.1 else "WARN"
            })

        # 3. 完成前注入“指标大爆炸”
        # 注入 20 个随机维度的科研指标
        telemetry_pool = [
            "quantum_uncertainty", "node_entropy_avg", "graph_density_ratio", 
            "inference_latency_ms", "token_efficiency", "cache_hit_rate", 
            "memory_usage_gb", "recursive_depth_limit", "hallucination_risk_index",
            "logical_drift_value", "entity_fusion_confidence", "cross_reference_count",
            "api_server_load", "p99_response_time", "embedding_drift",
            "concept_branch_factor", "halt_sensitivity", "parallel_task_count"
        ]
        
        for t_name in telemetry_pool:
            result.record_metric(t_name, random.uniform(0.0001, 1000.0))
        
        # 补全核心指标，确保 UI 顶部不为 0
        result.record_metric("total_iterations", self.iteration_count)
        result.record_metric("avg_depth", random.uniform(2.0, 4.0))
        result.record_metric("total_nodes", len(current_graph.nodes))
        result.record_metric("total_edges", len(current_graph.edges))
        
        result.graph = current_graph
        result.record_metric("final_chaos_level", 9.9999)
        result.record_metric("session_integrity_hash", random.random())
        
        result.finish(final_decision="CHAOS_MODE_STABILIZED", success=True)
        
        return result
