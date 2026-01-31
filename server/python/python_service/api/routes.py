"""
API 路由 - 推理执行 (Concurrency Optimized)
使用 run_in_threadpool 避免 GIL 的尴尬，防止卡死 Event Loop。
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from starlette.concurrency import run_in_threadpool

router = APIRouter()

class InferenceRequest(BaseModel):
    goal: str
    text: str
    orchestrator: str = "dynamic_halting"
    components: Dict[str, str] = {}
    component_params: Dict[str, Any] = {}
    params: Dict[str, Any] = {}
    api_key: Optional[str] = None
    experiment_id: Optional[str] = None

@router.post("/infer")
async def infer(request: InferenceRequest):
    """
    通用推理入口。
    使用 run_in_threadpool 将同步的推理引擎分发到独立的线程执行，
    配合之前的“影子实例”确保线程间状态隔离。
    """
    try:
        from python_service.services.inference import InferenceEngine
        engine = InferenceEngine()
        
        # 这里的关键：不直接调用同步方法，而是扔进线程池
        result = await run_in_threadpool(
            engine.run_dynamic,
            goal=request.goal,
            text=request.text,
            orchestrator=request.orchestrator,
            components=request.components,
            component_params=request.component_params,
            params=request.params,
            api_key=request.api_key,
            experiment_id=request.experiment_id
        )
        return result
        return result
    except Exception as e:
        # User defined errors should bubble up
        from python_service.core.errors import PrismError
        if isinstance(e, PrismError):
            raise e
            
        import traceback
        print(f"Error in inference API: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel/{experiment_id}")
async def cancel_task(experiment_id: str):
    """
    取消正在运行的任务
    """
    try:
        from python_service.services.inference import InferenceEngine
        engine = InferenceEngine()
        success = engine.cancel_task(experiment_id)
        if success:
            return {"status": "cancelled", "experiment_id": experiment_id}
        else:
            return {"status": "not_found", "message": "Task not running or ID not found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health():
    return {"status": "healthy", "service": "v2-async-safe"}
