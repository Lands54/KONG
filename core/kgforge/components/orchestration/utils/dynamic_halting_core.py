"""
动态判停编排器核心逻辑 (Core Implementation)
纯粹的算法流程实现，不依赖系统协议
"""

from typing import Optional, Dict, Any, List
from kgforge.protocols import IExtractor, IExpander, IFusion, IHalting
from kgforge.models.graph import Graph
from kgforge.models.experiment_result import ExperimentResult
from kgforge.utils import get_logger

logger = get_logger(__name__)

class DynamicHaltingCore:
    """
    动态判停算法核心逻辑
    接收零件实例，实现主板功能
    """
    
    def __init__(
        self,
        extractor: IExtractor,
        expander: IExpander,
        fusion: IFusion,
        halting: IHalting,
        max_iterations: int = 5,
        max_depth: int = 3,
        **kwargs
    ):
        self.extractor = extractor
        self.expander = expander
        self.fusion = fusion
        self.halting = halting
        self.max_iterations = max_iterations
        self.max_depth = max_depth
        self.kwargs = kwargs

    def run(self, goal: str, text: str, verbose: bool = True, **kwargs) -> ExperimentResult:
        """运行动态判停算法全链路"""
        if verbose:
            logger.info(f"--- [Orchestrator: DynamicHalting] 开始任务 ---")
            logger.info(f"目标: {goal}")

        # 1. 初始化结果容器
        result = ExperimentResult(graph=Graph(graph_id="dynamic_result"))
        result.set_metadata("goal", goal)
        result.set_metadata("engine", "DynamicHaltingOrchestrator")
        result.set_metadata("configs", {
            "max_iterations": self.max_iterations,
            "max_depth": self.max_depth
        })
        
        current_graph = None
        final_decision_val = "CONTINUE"
        
        try:
            # 2. Bottom-Up 抽取 (G_B)
            if verbose: logger.info("步骤 1: 执行 Bottom-Up 抽取 (G_B)...")
            graph_b = self.extractor.extract(text)
            result.log_graph("G_B", graph_b)
            result.log_step("bottom_up_extraction", {"node_count": len(graph_b.nodes)})
            
            # 3. Top-Down 展开 (G_T)
            if verbose: logger.info("步骤 2: 执行 Top-Down 展开 (G_T)...")
            graph_t = self.expander.expand_goal(goal)
            result.log_graph("G_T", graph_t)
            result.log_step("top_down_expansion", {"node_count": len(graph_t.nodes)})
            
            # 4. 融合 (G_F)
            if verbose: logger.info("步骤 3: 语义图融合 (G_F)...")
            current_graph = self.fusion.fuse(graph_b, graph_t)
            result.log_graph("G_F", current_graph)
            result.log_step("initial_fusion", {"node_count": len(current_graph.nodes)})
            
            # 5. 迭代闭环自适应展开
            iterations = 0
            depth = 0
            
            while iterations < self.max_iterations and depth < self.max_depth:
                iterations += 1
                if verbose: logger.info(f"迭代 {iterations}: 评估图状态及判停准则...")
                
                # 5.1 评估
                decision = self.halting.should_halt(current_graph, goal=goal, iteration=iterations, depth=depth)
                final_decision_val = decision.decision.value
                
                result.log_step("halting_evaluation", {
                    "iteration": iterations,
                    "decision": final_decision_val,
                    "reason": decision.reason,
                    "node_count": len(current_graph.nodes)
                })
                
                if verbose: logger.info(f"  [Halting] 当前决策: {final_decision_val} (原因: {decision.reason})")
                
                # 5.2 退出判断
                if final_decision_val in ["HALT", "DROP", "HITL"]:
                    break
                
                # 5.3 执行展开 LOOP
                if verbose: logger.info("  [Expander] 调用 LLM 进行智能全图上下文扩展...")
                
                increment_graph = self.expander.expand_graph(current_graph)
                
                # 清理增量图中的悬空边（在记录快照前）
                # 这些边可能引用了在语义去重中被删除的节点
                valid_edges = []
                for edge in increment_graph.edges:
                    # 检查边的两端是否都在增量图或当前图中
                    source_in_increment = edge.source in increment_graph.nodes
                    target_in_increment = edge.target in increment_graph.nodes
                    source_in_current = edge.source in current_graph.nodes
                    target_in_current = edge.target in current_graph.nodes
                    
                    if (source_in_increment or source_in_current) and (target_in_increment or target_in_current):
                        valid_edges.append(edge)
                    else:
                        if verbose:
                            logger.warning(f"  [Expander] 增量图包含悬空边: {edge.source}->{edge.target}, 已过滤")
                
                increment_graph.edges = valid_edges
                
                # 记录增量（已清理）
                result.log_graph(f"loop_{iterations}_increment", increment_graph)
                
                # 合并逻辑
                parent_id = increment_graph.metadata.get("parent_node_id")
                
                # 将增量合入主图（节点优先）
                for node in increment_graph.nodes.values():
                    if node.id not in current_graph.nodes:
                        current_graph.add_node(node)
                
                # 合并边（确保 source 和 target 都存在）
                skipped_edges = 0
                for edge in increment_graph.edges:
                    # 检查边的两端节点是否都存在
                    source_exists = edge.source in current_graph.nodes
                    target_exists = edge.target in current_graph.nodes
                    
                    if source_exists and target_exists:
                        try:
                            current_graph.add_edge(edge)
                        except Exception as e:
                            if verbose:
                                logger.warning(f"  [Merge] 跳过重复边: {edge.source}->{edge.target} ({e})")
                            skipped_edges += 1
                    else:
                        if verbose:
                            missing = []
                            if not source_exists: missing.append(f"source={edge.source}")
                            if not target_exists: missing.append(f"target={edge.target}")
                            logger.warning(f"  [Merge] 跳过悬空边: {edge.source}->{edge.target} (缺失: {', '.join(missing)})")
                        skipped_edges += 1
                
                if verbose and skipped_edges > 0:
                    logger.info(f"  [Merge] 共跳过 {skipped_edges} 条无效边")
                
                # 更新父节点状态
                if parent_id and parent_id in current_graph.nodes:
                    parent_node = current_graph.nodes[parent_id]
                    # 标记父节点已展开
                    parent_node.set_state("expandable", False)
                    parent_node.set_state('expanded', True)
                
                result.log_step("graph_increment_merged", {
                    "iteration": iterations,
                    "new_nodes": len(increment_graph.nodes),
                    "parent_node": parent_id
                })
                
                depth += 1
            
            # 6. 收尾与保存
            result.graph = current_graph
            result.record_metric("total_iterations", iterations)
            result.record_metric("final_node_count", len(current_graph.nodes))
            result.finish(final_decision=final_decision_val, success=True)

        except Exception as e:
            logger.error(f"编排器运行异常: {e}")
            import traceback
            traceback.print_exc()
            result.record_metric("error", str(e))
            result.finish(final_decision="ERROR", success=False)

        if verbose:
            logger.info(f"--- [Orchestrator] 运行结束. 最终状态: {final_decision_val} ---")
            
        return result
