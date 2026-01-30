"""
DataSet API

统一数据集浏览接口：
- /datasets                         列出支持的数据集
- /datasets/{dataset_id}/splits     列出 split
- /datasets/{dataset_id}/samples    分页预览
- /datasets/{dataset_id}/sample/... 单条样本（标准化 + raw）

说明：
- 已统一整合 DocRED 数据集到 DataSet API 体系
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Any, Dict

from python_service.services.dataset_service import DatasetService
from starlette.concurrency import run_in_threadpool

router = APIRouter()
svc = DatasetService()


@router.get("/datasets")
async def list_datasets() -> Dict[str, Any]:
    return {"datasets": svc.list_datasets()}


@router.get("/datasets/{dataset_id}/splits")
async def list_splits(dataset_id: str = Path(..., description="数据集 ID，如 docred/fever/cuad/scifact")):
    try:
        return {"dataset_id": dataset_id, "splits": svc.list_splits(dataset_id)}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_id}/samples")
async def list_samples(
    dataset_id: str = Path(..., description="数据集 ID"),
    split: str = Query("train", description="split，如 train/dev/test 或 DocRED 的 train_annotated/dev/test"),
    page: int = Query(1, ge=1, description="页码（从1开始）"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    try:
        # 大文件读取/解析放到 threadpool，避免阻塞事件循环造成“看似卡死”
        return await run_in_threadpool(svc.list_samples_preview, dataset_id, split, page, page_size)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        # HF 下载失败、无网络等
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_id}/sample/{split}/{index}")
async def get_sample(
    dataset_id: str = Path(..., description="数据集 ID"),
    split: str = Path(..., description="split"),
    index: int = Path(..., ge=0, description="样本索引"),
    include_raw: bool = Query(False, description="是否包含 raw 原始样本（可能很大，默认 false）"),
    max_context_chars: int = Query(
        20000,
        ge=0,
        le=200000,
        description="context 最大返回字符数（0 表示不返回 context；默认 20000，避免长合同/论文导致卡顿）",
    ),
):
    try:
        raw = await run_in_threadpool(svc.get_raw_sample, dataset_id, split, index)
        norm = await run_in_threadpool(svc.normalize_sample, dataset_id, split, index, raw, include_raw)

        # 截断长 context，避免单条样本巨大导致服务/前端卡死
        if isinstance(norm.get("context"), str):
            ctx: str = norm["context"]
            if max_context_chars == 0:
                norm["context"] = ""
                norm["context_truncated"] = True
                norm["context_total_chars"] = len(ctx)
            elif len(ctx) > max_context_chars:
                norm["context"] = ctx[:max_context_chars] + "..."
                norm["context_truncated"] = True
                norm["context_total_chars"] = len(ctx)
            else:
                norm["context_truncated"] = False
                norm["context_total_chars"] = len(ctx)
        return norm
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except IndexError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

