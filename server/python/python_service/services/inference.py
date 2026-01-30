"""
Inference Engine (Full Telemetry Edition)
执行层：组装并运行动态推理管线。
遵循“服务器无知性原则”：全量透传编排器结果，不预设结果结构。
"""

import time
from typing import Dict, Any, Optional
from kgforge import get_logger
from kgforge.models import Graph
from schemas.graph_schema import graph_to_dict
from python_service.core.factory import UnifiedFactory

logger = get_logger(__name__)

class InferenceEngine:
    """推理执行引擎"""

    def run_dynamic(
        self,
        goal: str,
        text: str,
        orchestrator: str = "dynamic_halting",
        components: Optional[Dict[str, str]] = None,
        component_params: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        start_time = time.time()
        
        # 准备物化参数
        creation_params = (params or {}).copy()
        if components:
             creation_params.update(components)
        
        if component_params:
            for comp_id, p in component_params.items():
                creation_params[f"{comp_id}_params"] = p

        if api_key:
            creation_params["api_key"] = api_key

        try:
            logger.info(f"Materializing orchestration pipeline: {orchestrator}")
            pipeline = UnifiedFactory.create_component("orchestrators", orchestrator, params=creation_params)
            
            # 执行
            result = pipeline.run(goal=goal, text=text, **(params or {}))
            
            # --- 结果全量映射 (Protocol-Aware) ---
            # 我们通过 hasattr 探测结果对象中可能存在的“数据桶”
            output = {
                "status": "success",
                "graph": graph_to_dict(result.graph) if hasattr(result, "graph") else {},
                "metrics": getattr(result, "metrics", {}),
                "intermediate_graphs": {
                    k: graph_to_dict(g) for k, g in getattr(result, "intermediate_graphs", {}).items()
                },
                "trace": getattr(result, "trace", []),
                "intermediate_stats": getattr(result, "intermediate_stats", {}),
                "metadata": {
                    "orchestrator_id": orchestrator,
                    "execution_time_ms": int((time.time() - start_time) * 1000),
                    **getattr(result, "metadata", {})
                }
            }
            return output

        except Exception as e:
            logger.error(f"Inference Pipeline Error: {e}")
            raise RuntimeError(f"Pipeline failure: {str(e)}") from e
