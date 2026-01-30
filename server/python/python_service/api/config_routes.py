"""
API 路由 - 配置层 (Blind Version)
不再对特定类别进行“特殊照顾”。
"""

from fastapi import APIRouter
from typing import Dict, Any, List
import os

from python_service.core.engine import engine
from python_service.services.lifecycle import warmer
from python_service.config.loader import get_config

router = APIRouter()

@router.get("/config/check")
async def check_config():
    """检查服务端环境配置 - 盲模式"""
    mask_key = lambda k: f"{k[:6]}...{k[-4:]}" if k and len(k) > 10 else "not set"
    
    # 统计所有 Ready 状态的组件 ID，不区分分类
    status_report = warmer.get_status_report()
    ready_instances = []
    
    for category, comps in status_report.items():
        for comp_id, state in comps.items():
            if state == "ready":
                ready_instances.append(f"{category}/{comp_id}")
                
    return {
        "api_key": mask_key(os.getenv("OPENROUTER_API_KEY")),
        "ready_instances": ready_instances, # 返回所有就绪组件，不单独点名 expanders
        "environment": get_config().get("environment", "development")
    }

@router.get("/models/status")
async def get_model_status():
    return {
        "success": True,
        "status": warmer.get_status_report()
    }

@router.get("/models/catalog")
async def get_catalog():
    return {
        "success": True,
        "catalog": engine.scan_all()
    }
