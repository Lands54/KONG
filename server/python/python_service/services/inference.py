"""
Inference Engine (Full Telemetry Edition)
执行层：组装并运行动态推理管线。
遵循“服务器无知性原则”：全量透传编排器结果，不预设结果结构。
"""

import time
import threading
from typing import Dict, Any, Optional
from kgforge import get_logger
from kgforge.models import Graph
from python_service.schemas.graph_schema import graph_to_dict
from python_service.core.factory import UnifiedFactory
from kgforge.components.base import TaskCancelledError
from python_service.core.errors import PrismAuthError, PrismRateLimitError
from python_service.core.context import set_experiment_id, clear_experiment_id, get_current_stats, get_current_logs
import openai
import sys
import platform
# import pkg_resources # might be too heavy/deprecated, let's stick to basic env for now or try-catch

logger = get_logger(__name__)

# Global Registry for Cancellation Events
CANCELLATION_EVENTS: Dict[str, threading.Event] = {}

class InferenceEngine:
    """推理执行引擎"""

    def cancel_task(self, experiment_id: str) -> bool:
        """取消指定实验任务"""
        if experiment_id in CANCELLATION_EVENTS:
            logger.warning(f"Cancelling experiment: {experiment_id}")
            CANCELLATION_EVENTS[experiment_id].set()
            return True
        return False

    def run_dynamic(
        self,
        goal: str,
        text: str,
        orchestrator: str = "dynamic_halting",
        components: Optional[Dict[str, str]] = None,
        component_params: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        api_key: Optional[str] = None,
        experiment_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        start_time = time.time()
        
        if experiment_id:
            set_experiment_id(experiment_id)
        
        # 1. 注册取消信号
        cancel_event = threading.Event()
        if experiment_id:
            CANCELLATION_EVENTS[experiment_id] = cancel_event

        try:
            # 准备物化参数
            creation_params = (params or {}).copy()
            if components:
                 creation_params.update(components)
            
            if component_params:
                for comp_id, p in component_params.items():
                    creation_params[f"{comp_id}_params"] = p

            if api_key:
                creation_params["api_key"] = api_key

            logger.info(f"Materializing orchestration pipeline: {orchestrator} (ID: {experiment_id})")
            pipeline = UnifiedFactory.create_component("orchestrators", orchestrator, params=creation_params)
            
            # 注入取消句柄 (如果支持)
            if hasattr(pipeline, "set_cancellation_event"):
                pipeline.set_cancellation_event(cancel_event)

            # 执行
            result = pipeline.run(goal=goal, text=text, **(params or {}))
            
            # --- 结果全量映射 (Protocol-Aware) ---
            output = {
                "status": "success",
                "graph": graph_to_dict(result.graph) if hasattr(result, "graph") else {},
                "metrics": getattr(result, "metrics", {}),
                "intermediate_graphs": {
                    k: graph_to_dict(g) for k, g in getattr(result, "intermediate_graphs", {}).items()
                },
                "trace": getattr(result, "trace", []),
                "logs": get_current_logs(), # Persist full logs
                "intermediate_stats": {
                    **getattr(result, "intermediate_stats", {}),
                    **get_current_stats() 
                },
                "metadata": {
                    "orchestrator_id": orchestrator,
                    "execution_time_ms": int((time.time() - start_time) * 1000),
                    **getattr(result, "metadata", {})
                }
            }
            return output

        except TaskCancelledError:
            logger.warning(f"Task {experiment_id} cancelled by user.")
            return {"status": "cancelled", "message": "Task cancelled by user."}
        except openai.AuthenticationError as e:
            raise PrismAuthError(message=str(e), details=str(e))
        except openai.RateLimitError as e:
            raise PrismRateLimitError(message=str(e), details=str(e))
        except PrismError as e:
            # Allow known system errors to propagate unmodified
            raise e
        except Exception as e:
            logger.error(f"Inference Pipeline Error: {e}")
            raise RuntimeError(f"Pipeline failure: {str(e)}") from e
        finally:
            # 清理信号
            if experiment_id:
                if experiment_id in CANCELLATION_EVENTS:
                    del CANCELLATION_EVENTS[experiment_id]
                clear_experiment_id()
