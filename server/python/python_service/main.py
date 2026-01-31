"""
Python FastAPI 服务
封装现有 dynhalting 模块，提供推理 API
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from python_service.core.errors import PrismError
from contextlib import asynccontextmanager
import sys
import os
import logging
from pathlib import Path

# 不再在这里手动修改 sys.path，建议在运行环境或通过 PYTHONPATH 设置

# 获取项目根目录
# 当前文件在 server/python/python_service/main.py
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))

# 【自动修复】将项目根目录加入模块搜索路径，避免 ModuleNotFoundError
if project_root not in sys.path:
    sys.path.append(project_root)

# 加载项目根目录的 .env 文件
try:
    from dotenv import load_dotenv
    env_file = Path(project_root) / '.env'
    if env_file.exists():
        try:
            load_dotenv(env_file)
            print(f"[Main] 已加载 .env 文件: {env_file}")
        except PermissionError as e:
            print(f"[Main] 警告: 无法读取 .env 文件（权限受限）：{e}")
    else:
        load_dotenv()
        print(f"[Main] 尝试加载默认 .env 文件")
except ImportError:
    print("[Main] 警告: python-dotenv 未安装，无法自动加载 .env 文件")
    print("[Main] 请安装: pip install python-dotenv")

from python_service.api.routes import router
from python_service.api.dataset_routes import router as dataset_router
from python_service.api.config_routes import router as config_router
from python_service.config.loader import get_config
from kgforge import get_logger

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """服务寿命周期管理：处理启动与关闭逻辑"""
    try:
        from python_service.core.logging import StreamingEventHandler
        from kgforge.utils.logger import register_global_handler
        
        # 注册实时日志处理器 (全局)
        register_global_handler(StreamingEventHandler())

        # [v3.0 Feature] 启动热重载服务 (Identify core/kgforge/components path)
        # 获取 core/kgforge/components 的绝对路径
        # project_root 已在前面计算得到
        components_path = Path(project_root) / "core" / "kgforge" / "components"
        
        # 仅在 components 目录存在时启动
        if components_path.exists():
            from python_service.services.hot_reload import start_hot_reload_service
            start_hot_reload_service(str(components_path))

        # 懒加载服务
        from services.lifecycle import preload_all
        
        logger.info("服务启动：开始基于代码自省进行组件预热...")
        preload_all()
        
        logger.info("✓ 组件预热完成，服务就绪")
    except Exception as e:
        logger.error(f"组件预热失败: {e}")
        logger.warning("服务将继续运行，但组件将在首次使用时加载（可能较慢）")
    
    yield  # 服务运行中

app = FastAPI(
    title="PRISM: Platform for Reasoning, Inference, and Semantic Modeling",
    description="专为大语言模型设计的科研级动态推理与语义建模框架",
    version="2.0.0",
    lifespan=lifespan
)

@app.exception_handler(PrismError)
async def prism_exception_handler(request: Request, exc: PrismError):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由（统一前缀）
app.include_router(router, prefix="/api/v1")
app.include_router(dataset_router, prefix="/api/v1")
app.include_router(config_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Dynamic Halting Research Framework API", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
