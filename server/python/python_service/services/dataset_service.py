"""
通用数据集服务（DataSet API）

目标：
- 统一浏览不同类型的数据集（本地 DocRED / HuggingFace datasets：FEVER、CUAD、SciFact 等）
- 提供稳定的“标准化样本 schema”，同时保留 raw 以便调试

注意：
- HuggingFace datasets 需要联网下载（首次），会自动缓存到本机
- 该服务内部做了简单的进程内缓存，避免重复 load_dataset
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import os
import json
from pathlib import Path
import re

from kgforge import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class DatasetSpec:
    dataset_id: str
    display_name: str
    task_type: str  # fact_verification / legal_compliance / scientific_evidence / relation_extraction ...
    source: str  # local / hf
    hf_name: Optional[str] = None
    hf_config: Optional[str] = None
    trust_remote_code: bool = False
    description: str = ""


# Removed dynhalting-dependent get_project_root


class DatasetService:
    """
    DataSet API 的统一入口。
    - 本地 DocRED：读取 `data/DocRED/data/*.json`
    - HF 数据集：用 datasets.load_dataset
    """

    def __init__(self):
        # 获取项目根目录 (Independent calculation)
        # server/python/python_service/services/dataset_service.py -> KONG/ (4 levels up)
        self._root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
        self._cache: Dict[Tuple[str, str], Any] = {}  # (dataset_id, split) -> dataset split object
        # DocRED 本地 JSON 缓存（避免每次分页都 json.load 大文件导致卡顿/阻塞）
        self._docred_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._docred_mtimes: Dict[str, float] = {}
        # FEVER：Wikipedia 页面内容缓存（按需抓取，避免重复网络请求）
        self._fever_wiki_cache: Dict[str, str] = {}
        # SciFact：corpus doc_id -> (title, abstract_lines) 缓存（规模小，可常驻内存）
        self._scifact_corpus_map: Optional[Dict[int, Dict[str, Any]]] = None

        self._specs: Dict[str, DatasetSpec] = {
            # 兼容现有 DocRED（本地）
            "docred": DatasetSpec(
                dataset_id="docred",
                display_name="DocRED",
                task_type="relation_extraction",
                source="local",
                description="关系抽取（DocRED）。顶层可视为 goal=标题/关系提示，底层为文章句子。",
            ),
            # A. 事实核查
            "fever": DatasetSpec(
                dataset_id="fever",
                display_name="FEVER",
                task_type="fact_verification",
                source="hf",
                hf_name="fever",
                hf_config="v1.0",
                trust_remote_code=True,
                description="事实核查：给定 claim，从维基证据中判断 SUPPORTS/REFUTES/NOT ENOUGH INFO。",
            ),
            # B. 合同/合规
            "cuad": DatasetSpec(
                dataset_id="cuad",
                display_name="CUAD",
                task_type="legal_compliance",
                source="hf",
                # 说明：官方 `cuad` repo 在当前 datasets 生态下容易出现数据文件/脚本兼容问题；
                # 这里选用可用的 QA 版本（含 question/context/answers）。
                hf_name="chenghao/cuad_qa",
                trust_remote_code=True,
                description="合同理解（QA）：给定条款问题（question/query），在长合同 context 中定位/抽取答案证据。",
            ),
            # C. 科学证据
            "scifact": DatasetSpec(
                dataset_id="scifact",
                display_name="SciFact",
                task_type="scientific_evidence",
                source="hf",
                hf_name="scifact",
                # scifact 数据集分为 corpus/claims 两个 config；这里默认 claims（更接近“假设/断言 + 证据”）
                hf_config="claims",
                trust_remote_code=True,
                description="科学证据：给定 claim，在论文摘要中检索支持/反驳证据。",
            ),
        }

        # DocRED 本地文件映射（沿用现有 docred_routes 的命名）
        self._docred_files = {
            "train_annotated": "train_annotated.json",
            "train_distant": "train_distant.json",
            "dev": "dev.json",
            "test": "test.json",
        }

    def list_datasets(self) -> List[Dict[str, Any]]:
        return [
            {
                "dataset_id": s.dataset_id,
                "display_name": s.display_name,
                "task_type": s.task_type,
                "source": s.source,
                "hf_name": s.hf_name,
                "hf_config": s.hf_config,
                "trust_remote_code": s.trust_remote_code,
                "description": s.description,
            }
            for s in self._specs.values()
        ]

    def get_spec(self, dataset_id: str) -> DatasetSpec:
        if dataset_id not in self._specs:
            raise KeyError(f"未知数据集: {dataset_id}")
        return self._specs[dataset_id]

    # -------------------------
    # 统一“标准化样本 schema”
    # -------------------------
    def normalize_sample(
        self,
        dataset_id: str,
        split: str,
        index: int,
        raw: Dict[str, Any],
        include_raw: bool = False,
    ) -> Dict[str, Any]:
        """
        输出统一 schema（尽量）：
        - query: claim / question / goal
        - context: 文本（可能为长文档、证据集合或拼接）
        - label: 支持/反驳/类别 等
        - evidence: （可选）证据列表（句子/段落/span）
        - raw: 原始样本（保留调试）
        """

        def pick_first(*keys: str) -> Optional[Any]:
            for k in keys:
                if k in raw and raw[k] is not None:
                    return raw[k]
            return None

        query = None
        context = None
        label = None
        evidence = None

        if dataset_id == "docred":
            # 内部集成算法无关的数据展示逻辑
            def _docred_to_text(s):
                sents = s.get("sents", [])
                text_parts = [" ".join(sent) if isinstance(sent, list) else sent for sent in sents]
                return " ".join(text_parts)

            def _extract_goal(s):
                if "title" in s: return s["title"]
                if "abstract" in s: return s["abstract"][:200]
                labels = s.get("labels", [])
                if labels and isinstance(labels[0], dict):
                    return f"提取文本中的{labels[0].get('r', '关键')}关系"
                return "从文本中提取实体和关系"

            query = _extract_goal(raw)
            context = _docred_to_text(raw)
            label = "relation_extraction"
            evidence = {
                "sents": raw.get("sents", []),
                "vertexSet": raw.get("vertexSet", []),
                "labels": raw.get("labels", []),
            }
        elif dataset_id == "fever":
            # 常见字段：claim/label/evidence
            query = pick_first("claim", "query", "sentence")
            label = pick_first("label", "verdict", "gold_label")
            wiki_title = raw.get("evidence_wiki_url")
            sent_id = raw.get("evidence_sentence_id")

            evidence = {
                "evidence_wiki_url": wiki_title,
                "evidence_sentence_id": sent_id,
                "evidence_id": raw.get("evidence_id"),
                "evidence_annotation_id": raw.get("evidence_annotation_id"),
            }

            # FEVER v1.0 通常不给出具体证据句文本，只有指针。
            # 为了让前端/实验“能用”，这里按需拉取 Wikipedia 页面文本，并尽量定位到对应句子。
            context = pick_first("context", "wiki_sentences")
            if (not context) and wiki_title:
                try:
                    page_text = self._fever_fetch_wikipedia_page(wiki_title)
                    evidence_text = self._fever_pick_sentence(page_text, sent_id)
                    evidence["evidence_text"] = evidence_text
                    # 给 bottom-up 一段可读文本：优先证据句，否则返回页面开头
                    context = evidence_text or page_text
                except Exception as e:
                    # 网络不可用/解析失败：退化为 claim（至少可跑通管线）
                    logger.warning(f"FEVER 证据文本获取失败（title={wiki_title}）：{e}")
                    context = query
            if (not context) and query:
                context = query
        elif dataset_id == "cuad":
            # 常见字段：question/context/answers
            query = pick_first("question", "query")
            context = pick_first("context", "contract", "text")
            label = pick_first("answers", "answer", "label")
            evidence = pick_first("answers", "evidence")
        elif dataset_id == "scifact":
            # 常见字段：claim/abstract/evidence/label
            query = pick_first("claim", "query")
            # scifact/claims config：字段名是 evidence_label/evidence_sentences/cited_doc_ids
            label = pick_first("evidence_label", "label", "verdict")
            context = pick_first("abstract", "abstracts", "text")
            evidence = pick_first("evidence_sentences", "evidence", "rationale", "sentences")
            if (not context) and evidence:
                # 如果只有证据句子，拼成 context
                try:
                    context = "\n".join([str(x) for x in evidence])
                except Exception:
                    pass
            # claims config 通常只有 doc_id 指针；用 corpus 把 abstract 补齐，这样“能用”
            if not context:
                cited = raw.get("cited_doc_ids") or []
                doc_id = raw.get("evidence_doc_id")
                picked_id = None
                try:
                    if isinstance(doc_id, int) and doc_id > 0:
                        picked_id = doc_id
                    elif isinstance(cited, list) and cited:
                        picked_id = int(cited[0])
                except Exception:
                    picked_id = None

                if picked_id is not None:
                    try:
                        doc = self._scifact_get_doc(picked_id)
                        if doc:
                            title = doc.get("title") or ""
                            abs_lines = doc.get("abstract") or []
                            if isinstance(abs_lines, list):
                                abs_text = "\n".join([str(x) for x in abs_lines if x is not None])
                            else:
                                abs_text = str(abs_lines)
                            context = (title + "\n\n" + abs_text).strip() if title else abs_text
                            # 如果 evidence_sentences 是“句子索引”，同时给出 evidence_text
                            if isinstance(evidence, list) and evidence and all(isinstance(x, int) for x in evidence):
                                ev_text = []
                                for i in evidence:
                                    if 0 <= i < len(abs_lines):
                                        ev_text.append(str(abs_lines[i]))
                                if ev_text:
                                    raw_ev = raw.get("evidence_sentences")
                                    # 在 evidence 字段里补充 text（不改变原结构）
                                    evidence = {"sentence_ids": raw_ev, "evidence_text": ev_text}
                    except Exception as e:
                        logger.warning(f"SciFact corpus 补齐失败（doc_id={picked_id}）：{e}")

            if (not context) and query:
                # 最终兜底：至少返回 claim
                context = query
        else:
            query = pick_first("query", "question", "claim", "goal", "title")
            context = pick_first("context", "text", "document", "abstract")
            label = pick_first("label", "answer", "answers")
            evidence = pick_first("evidence", "rationale")

        # 兜底为字符串，避免前端展示崩掉
        if isinstance(query, list):
            query = " ".join([str(x) for x in query if x is not None])
        if isinstance(context, list):
            context = "\n".join([str(x) for x in context if x is not None])

        out = {
            "dataset_id": dataset_id,
            "split": split,
            "index": index,
            "query": query,
            "context": context,
            "label": label,
            "evidence": evidence,
        }
        if include_raw:
            out["raw"] = raw
        return out

    def _fever_fetch_wikipedia_page(self, title: str) -> str:
        """
        使用 Wikipedia API 获取页面纯文本（英文）。
        注意：这是一个“可用性优先”的实现，用于把 FEVER 的证据指针变成可读文本。
        """
        title_norm = str(title).strip()
        if not title_norm:
            return ""
        if title_norm in self._fever_wiki_cache:
            return self._fever_wiki_cache[title_norm]

        import requests

        headers = {
            # Wikipedia 对无 UA/异常 UA 有时会 403，这里加一个稳定 UA
            "User-Agent": "KONG-DynHalting/0.1 (+https://example.com; contact: local-dev)"
        }
        resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            headers=headers,
            params={
                "action": "query",
                "format": "json",
                "prop": "extracts",
                "explaintext": 1,
                "redirects": 1,
                "titles": title_norm,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        pages = (data.get("query") or {}).get("pages") or {}
        extract = ""
        for _, page in pages.items():
            extract = page.get("extract") or ""
            break
        extract = re.sub(r"\n{3,}", "\n\n", extract).strip()
        # 控制缓存大小：只缓存前 200k 字符，够用了，避免内存爆
        self._fever_wiki_cache[title_norm] = extract[:200_000]
        return self._fever_wiki_cache[title_norm]

    def _fever_pick_sentence(self, page_text: str, sentence_id: Any) -> str:
        """从 Wikipedia 页面文本中按 sentence_id 取一句（尽力而为，句子切分可能与 FEVER 标注不完全一致）"""
        if not page_text:
            return ""
        try:
            sid = int(sentence_id)
        except Exception:
            sid = -1

        # 简单句分割（英文）
        sents = re.split(r"(?<=[.!?])\s+", page_text)
        sents = [s.strip() for s in sents if s.strip()]
        if 0 <= sid < len(sents):
            return sents[sid]
        # 兜底：返回开头一小段
        return (page_text[:400] + "...") if len(page_text) > 400 else page_text

    def _scifact_get_doc(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """从 scifact/corpus 中按 doc_id 获取论文信息（title/abstract）"""
        if doc_id <= 0:
            return None
        if self._scifact_corpus_map is None:
            self._scifact_corpus_map = self._load_scifact_corpus_map()
        return self._scifact_corpus_map.get(int(doc_id))

    def _load_scifact_corpus_map(self) -> Dict[int, Dict[str, Any]]:
        """加载 scifact/corpus 的小规模映射（约 5k 篇），用于把 doc_id 指针变成可读摘要。"""
        try:
            from datasets import load_dataset

            ds = load_dataset("scifact", "corpus", split="train", trust_remote_code=True)
            out: Dict[int, Dict[str, Any]] = {}
            for row in ds:
                try:
                    did = int(row.get("doc_id"))
                except Exception:
                    continue
                out[did] = {
                    "doc_id": did,
                    "title": row.get("title"),
                    "abstract": row.get("abstract"),
                    "structured": row.get("structured"),
                }
            logger.info(f"SciFact corpus 已加载: {len(out)} 篇")
            return out
        except Exception as e:
            logger.warning(f"SciFact corpus 加载失败：{e}")
            return {}

    # -------------------------
    # 读取样本（local / hf）
    # -------------------------
    def list_splits(self, dataset_id: str) -> List[str]:
        spec = self.get_spec(dataset_id)
        if spec.source == "local" and dataset_id == "docred":
            return list(self._docred_files.keys())

        # HF：尽量通过 datasets 获取 split 列表；如果失败，就返回常见 split
        try:
            from datasets import get_dataset_split_names

            if spec.hf_name:
                return list(get_dataset_split_names(spec.hf_name, spec.hf_config, trust_remote_code=spec.trust_remote_code))
        except Exception as e:
            logger.warning(f"获取 splits 失败（{dataset_id}）：{e}")

        # CUAD(qa) 常见只有 train/test
        if dataset_id == "cuad":
            return ["train", "test"]
        return ["train", "validation", "test"]

    def _load_docred_split(self, split: str) -> List[Dict[str, Any]]:
        if split not in self._docred_files:
            raise KeyError(f"未知 DocRED split: {split}")
        path = os.path.join(self._root, "data", "DocRED", "data", self._docred_files[split])
        if not os.path.exists(path):
            raise FileNotFoundError(f"DocRED 文件不存在: {path}")
        # mtime cache
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            raise FileNotFoundError(f"DocRED 文件不可访问: {path}")

        if path in self._docred_cache and self._docred_mtimes.get(path) == mtime:
            return self._docred_cache[path]

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            parsed = data
        elif isinstance(data, dict) and "data" in data:
            parsed = data["data"]
        else:
            raise ValueError(f"不支持的 DocRED 格式: {path}")

        self._docred_cache[path] = parsed
        self._docred_mtimes[path] = mtime
        return parsed

    def _docred_preview(self, sample: Dict[str, Any]) -> Tuple[str, str, int]:
        """
        DocRED 预览构造（避免拼接全文导致 CPU/内存压力）
        Returns: (goal, preview_text, approx_len)
        """
        # 内部集成算法无关的数据展示逻辑
        def _extract_goal_local(s):
            if "title" in s: return s["title"]
            if "abstract" in s: return s["abstract"][:200]
            labels = s.get("labels", [])
            if labels and isinstance(labels[0], dict):
                return f"提取文本中的{labels[0].get('r', '关键')}关系"
            return "从文本中提取实体和关系"

        goal = _extract_goal_local(sample)
        sents = sample.get("sents", [])
        # 取前 2 句拼接作为 preview
        preview_parts: List[str] = []
        for sent in sents[:2]:
            if isinstance(sent, list):
                preview_parts.append(" ".join(sent))
            elif isinstance(sent, str):
                preview_parts.append(sent)
        preview_text = " ".join(preview_parts)
        return goal, preview_text, len(preview_text)

    def _load_hf_split(self, spec: DatasetSpec, split: str):
        key = (spec.dataset_id, split)
        if key in self._cache:
            return self._cache[key]

        try:
            from datasets import load_dataset

            if not spec.hf_name:
                raise ValueError(f"{spec.dataset_id} 未配置 hf_name")
            ds = load_dataset(
                spec.hf_name,
                spec.hf_config,
                split=split,
                trust_remote_code=spec.trust_remote_code,
            )
            self._cache[key] = ds
            return ds
        except Exception as e:
            msg = str(e)
            if "Dataset scripts are no longer supported" in msg:
                raise RuntimeError(
                    f"当前环境的 `datasets` 版本不支持脚本型数据集（{spec.hf_name}）。\n"
                    f"解决方案：请将 datasets 降级到 <4.0.0（例如 3.x），或使用项目内置 `.conda` 环境运行服务。\n"
                    f"原始错误: {msg}"
                ) from e
            raise RuntimeError(
                f"加载 HuggingFace 数据集失败: dataset={spec.hf_name}, config={spec.hf_config}, split={split}, error={e}"
            ) from e

    def get_total(self, dataset_id: str, split: str) -> int:
        spec = self.get_spec(dataset_id)
        if spec.source == "local" and dataset_id == "docred":
            data = self._load_docred_split(split)
            return len(data)
        ds = self._load_hf_split(spec, split)
        return len(ds)

    def get_raw_sample(self, dataset_id: str, split: str, index: int) -> Dict[str, Any]:
        spec = self.get_spec(dataset_id)
        if index < 0:
            raise IndexError("index 必须 >= 0")

        if spec.source == "local" and dataset_id == "docred":
            data = self._load_docred_split(split)
            if index >= len(data):
                raise IndexError(f"索引超出范围（{index} >= {len(data)}）")
            return data[index]

        ds = self._load_hf_split(spec, split)
        if index >= len(ds):
            raise IndexError(f"索引超出范围（{index} >= {len(ds)}）")
        sample = ds[index]
        # datasets 返回的是 dict-like
        return dict(sample)

    def list_samples_preview(
        self,
        dataset_id: str,
        split: str,
        page: int,
        page_size: int,
    ) -> Dict[str, Any]:
        # DocRED：分页预览走轻量路径（不 normalize 全文 context）
        if dataset_id == "docred":
            data = self._load_docred_split(split)
            total = len(data)
            start = (page - 1) * page_size
            end = min(start + page_size, total)
            if start >= total:
                return {
                    "dataset_id": dataset_id,
                    "split": split,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total + page_size - 1) // page_size,
                    "samples": [],
                }

            previews: List[Dict[str, Any]] = []
            for idx in range(start, end):
                sample = data[idx]
                goal, preview_text, approx_len = self._docred_preview(sample)
                previews.append(
                    {
                        "index": idx,
                        "query": goal,
                        "context_preview": (preview_text[:240] + "...") if len(preview_text) > 240 else preview_text,
                        "context_length": approx_len,
                        "label": "relation_extraction",
                        "meta": {
                            "sentence_count": len(sample.get("sents", [])),
                            "entity_count": len(sample.get("vertexSet", [])),
                            "relation_count": len(sample.get("labels", [])),
                        },
                    }
                )

            return {
                "dataset_id": dataset_id,
                "split": split,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "samples": previews,
            }

        total = self.get_total(dataset_id, split)
        start = (page - 1) * page_size
        end = min(start + page_size, total)
        if start >= total:
            return {
                "dataset_id": dataset_id,
                "split": split,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "samples": [],
            }

        previews: List[Dict[str, Any]] = []
        for idx in range(start, end):
            raw = self.get_raw_sample(dataset_id, split, idx)
            # 预览接口不返回 raw，避免大字段导致服务/前端卡顿
            norm = self.normalize_sample(dataset_id, split, idx, raw, include_raw=False)
            context = norm.get("context") or ""
            query = norm.get("query") or ""
            previews.append(
                {
                    "index": idx,
                    "query": query,
                    "context_preview": (context[:240] + "...") if isinstance(context, str) and len(context) > 240 else context,
                    "context_length": len(context) if isinstance(context, str) else None,
                    "label": norm.get("label"),
                }
            )

        return {
            "dataset_id": dataset_id,
            "split": split,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "samples": previews,
        }

