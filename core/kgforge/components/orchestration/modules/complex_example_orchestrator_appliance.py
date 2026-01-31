
import time
from typing import Any, Dict
from kgforge.components.base import BaseOrchestrator, TaskCancelledError
from kgforge.models import Graph
from kgforge.models.experiment_result import ExperimentResult
from kgforge.utils import get_logger

logger = get_logger(__name__)

class ComplexExampleOrchestratorAppliance(BaseOrchestrator):
    """
    复杂示例编排器
    
    演示一个完整的 Pipeline:
    Generator(Extractor) -> Filter(Processor) -> Enricher(Processor)
    
    展示了：
    1. Slot 定义
    2. 组件实例化
    3. 数据流转与中间结果记录
    4. Telemetry 实时反馈
    """
    name = "complex_example"
    display_name = "复杂示例编排器"

    def __init__(self, config: Dict[str, Any] = None, **kwargs):
        super().__init__(config or {}, **kwargs)

    @classmethod
    def get_required_slots(cls) -> Dict[str, str]:
        """
        定义此编排器需要的插槽类型。
        key: 插槽名 (用户在前端看到的配置项)
        value: 
        """
        return {
            "source_generator": "IExtractor",
            "data_filter": "IProcessor",
            "data_enricher": "IProcessor"
        }

    @classmethod
    def get_component_spec(cls) -> Dict[str, Any]:
        return {
            "id": "complex_example",
            "name": "复杂示例编排器",
            "slots": cls.get_required_slots(),
            "description": "一个标准的线性 Pipeline 示例：生成 -> 过滤 -> 增强。",
            "params": {}
        }

    def run(self, goal: str, text: str, verbose: bool = True, **kwargs) -> ExperimentResult:
        logger.info(f"--- [ComplexExample] 开始执行: {goal} ---")
        
        # 1. 实例化组件 (从 self.components 字典中获取已配置的实例)
        # 注意：BaseOrchestrator 会自动根据 factory 注入 self.components
        generator = self.components.get("source_generator")
        data_filter = self.components.get("data_filter")
        data_enricher = self.components.get("data_enricher")
        
        # 验证组件是否就绪
        if not all([generator, data_filter, data_enricher]):
            error_msg = "缺少必要的组件配置，请检查 Slot 映射。"
            logger.error(error_msg)
            raise ValueError(error_msg)

        result = ExperimentResult(graph=Graph(graph_id="final"))
        result.set_metadata("goal", goal)
        
        try:
            # Stage 1: Generation
            self.check_cancellation()
            logger.info("Stage 1: 生成数据 (Generator)...")
            # 传递参数给组件，Extractor 使用 extract(text)
            graph_raw = generator.extract(text)
            
            result.log_graph("raw_generated", graph_raw)
            logger.telemetry({"intermediate_stats": {"Stage1_Gen": {
                "node_count": len(graph_raw.nodes),
                "edge_count": len(graph_raw.edges)
            }}})
            
            # Stage 2: Filtering
            self.check_cancellation()
            logger.info(f"Stage 2: 过滤数据 (Filter) - 原始节点数: {len(graph_raw.nodes)}")
            # Processor 使用 process(graph)
            graph_filtered = data_filter.process(graph=graph_raw)
            
            result.log_graph("filtered", graph_filtered)
            logger.telemetry({"intermediate_stats": {"Stage2_Filter": {
                "node_count": len(graph_filtered.nodes),
                "edge_count": len(graph_filtered.edges),
                "dropped": len(graph_raw.nodes) - len(graph_filtered.nodes)
            }}})

            # Stage 3: Enrichment
            self.check_cancellation()
            logger.info("Stage 3: 数据增强 (Enricher)...")
            graph_final = data_enricher.process(graph=graph_filtered)
            
            # Finalize
            result.graph = graph_final
            result.finish(final_decision="COMPLETED", success=True)
            
            logger.info("--- [ComplexExample] 执行完成 ---")
            logger.telemetry({"intermediate_stats": {"Stage3_Final": {
                "node_count": len(graph_final.nodes),
                "edge_count": len(graph_final.edges)
            }}})
            
            return result

        except TaskCancelledError:
            logger.warning("任务被取消")
            result.finish("CANCELLED", False)
            return result
        except Exception as e:
            logger.error(f"执行异常: {e}")
            raise e

