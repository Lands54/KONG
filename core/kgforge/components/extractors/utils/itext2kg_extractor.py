"""
IText2KG / ATOM 抽取器适配器

设计原则：
- 依赖注入：LLM/embeddings 实例由外部（Factory/ModelLoader）构建后传入
- 单一职责：只负责调用 itext2kg 并转换为 dynhalting.Graph
- 可测试性：不直接读取环境变量，所有依赖可 mock

参考：
- https://github.com/AuvaLab/itext2kg
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple
import re
import time
import asyncio

from kgforge.utils import get_logger
from kgforge.models import Graph, Node, Edge


logger = get_logger(__name__)


_SENT_SPLIT_RE = re.compile(r"(?<=[。！？.!?])\s+")


def _split_sentences(text: str) -> List[str]:
    """轻量分句：优先 spaCy（如果装了），否则 regex"""
    text = (text or "").strip()
    if not text:
        return []

    try:
        import spacy  # type: ignore

        try:
            nlp = spacy.blank("en")
        except Exception:
            nlp = spacy.blank("xx")
        if "sentencizer" not in nlp.pipe_names:
            nlp.add_pipe("sentencizer")
        doc = nlp(text)
        sents = [s.text.strip() for s in doc.sents if s.text and s.text.strip()]
        return sents if sents else [text]
    except Exception:
        parts = [p.strip() for p in _SENT_SPLIT_RE.split(text) if p and p.strip()]
        return parts if parts else [text]


def _clamp_atomic_facts(facts: Iterable[str], *, max_facts: int, max_chars_per_fact: int) -> List[str]:
    """截断 atomic facts 数量和长度"""
    out: List[str] = []
    for f in facts:
        f = (f or "").strip()
        if not f:
            continue
        if len(f) > max_chars_per_fact:
            f = f[:max_chars_per_fact].rstrip() + "…"
        out.append(f)
        if len(out) >= max_facts:
            break
    return out


def _run_maybe_async(fn: Any, *args: Any, **kwargs: Any) -> Any:
    """兼容 itext2kg 的 API 既可能是 sync 也可能是 async"""
    res = fn(*args, **kwargs)
    if asyncio.iscoroutine(res):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(res)
        raise RuntimeError(
            "IText2KGExtractor 需要在非 async 线程/上下文中运行（或使用线程池 offload）。"
        )
    return res


def _normalize_triple_text(x: Any) -> str:
    """从 itext2kg Entity/dict 中提取文本"""
    if x is None:
        s = ""
    elif isinstance(x, dict):
        s = str(
            x.get("name")
            or x.get("label")
            or x.get("text")
            or x.get("id")
            or ""
        )
    else:
        s = str(getattr(x, "name", None) or getattr(x, "label", None) or getattr(x, "id", None) or x)
    return re.sub(r"\s+", " ", s).strip()


def _kg_to_triples(kg: Any) -> List[Tuple[str, str, str]]:
    """将 itext2kg KnowledgeGraph 解析为 (subj, rel, obj) 三元组"""
    rels = None
    for attr in ("relations", "relationship", "relationships", "edges"):
        if hasattr(kg, attr):
            rels = getattr(kg, attr)
            break

    if rels is None:
        for m in ("to_dict", "dict", "model_dump"):
            if hasattr(kg, m):
                try:
                    d = getattr(kg, m)()
                    if isinstance(d, dict):
                        rels = d.get("relations") or d.get("relationships") or d.get("edges")
                    break
                except Exception:
                    pass

    triples: List[Tuple[str, str, str]] = []
    if not rels:
        return triples

    for r in rels:
        if isinstance(r, dict):
            subj = (
                r.get("head") or r.get("subject") or r.get("subj") or r.get("source")
                or r.get("entity_1") or r.get("entity1") or r.get("startEntity")
                or r.get("start_entity") or r.get("start")
            )
            obj = (
                r.get("tail") or r.get("object") or r.get("obj") or r.get("target")
                or r.get("entity_2") or r.get("entity2") or r.get("endEntity")
                or r.get("end_entity") or r.get("end")
            )
            rel = (
                r.get("relation") or r.get("predicate") or r.get("rel")
                or r.get("type") or r.get("name")
            )
        else:
            subj = (
                getattr(r, "head", None) or getattr(r, "subject", None) or getattr(r, "subj", None)
                or getattr(r, "source", None) or getattr(r, "entity_1", None) or getattr(r, "entity1", None)
                or getattr(r, "startEntity", None) or getattr(r, "start_entity", None) or getattr(r, "start", None)
            )
            obj = (
                getattr(r, "tail", None) or getattr(r, "object", None) or getattr(r, "obj", None)
                or getattr(r, "target", None) or getattr(r, "entity_2", None) or getattr(r, "entity2", None)
                or getattr(r, "endEntity", None) or getattr(r, "end_entity", None) or getattr(r, "end", None)
            )
            rel = (
                getattr(r, "relation", None) or getattr(r, "predicate", None) or getattr(r, "rel", None)
                or getattr(r, "type", None) or getattr(r, "name", None)
            )

        s_subj = _normalize_triple_text(subj)
        s_obj = _normalize_triple_text(obj)
        s_rel = _normalize_triple_text(rel)
        if s_subj and s_obj and s_rel:
            triples.append((s_subj, s_rel, s_obj))
    return triples


class IText2KGExtractor:
    """
    基于 itext2kg/ATOM 的 Bottom-Up 抽取器
    
    设计：
    - 通过依赖注入接收已构建好的 LLM 和 embeddings 实例
    - 不直接读取环境变量或配置文件
    - 只负责调用 itext2kg 并将结果转换为 dynhalting.Graph
    """

    def __init__(
        self,
        llm_model: Any,
        embeddings_model: Any,
        # ATOM merge 阶段参数
        ent_threshold: float = 0.8,
        rel_threshold: float = 0.7,
        entity_name_weight: float = 0.8,
        entity_label_weight: float = 0.2,
        max_workers: int = 4,
        # 输入切分参数
        max_atomic_facts: int = 40,
        max_chars_per_fact: int = 280,
        # 时间戳格式
        obs_timestamp_format: str = "%d-%m-%Y",
    ):
        """
        Args:
            llm_model: LangChain chat model 实例（由外部构建，例如 ChatOpenAI）
            embeddings_model: LangChain embeddings model 实例（例如 OpenAIEmbeddings / SentenceTransformer adapter）
            ent_threshold: 实体相似度阈值
            rel_threshold: 关系相似度阈值
            entity_name_weight: 实体名称权重
            entity_label_weight: 实体标签权重
            max_workers: ATOM 并行 workers 数量
            max_atomic_facts: 最大 atomic facts 数量
            max_chars_per_fact: 每个 atomic fact 最大字符数
            obs_timestamp_format: 观察时间戳格式（传给 itext2kg）
        """
        self.llm_model = llm_model
        self.embeddings_model = embeddings_model

        self.ent_threshold = ent_threshold
        self.rel_threshold = rel_threshold
        self.entity_name_weight = entity_name_weight
        self.entity_label_weight = entity_label_weight
        self.max_workers = max_workers

        self.max_atomic_facts = max_atomic_facts
        self.max_chars_per_fact = max_chars_per_fact
        self.obs_timestamp_format = obs_timestamp_format

        self._atom = None
        self._initialized = False

    def _initialize(self):
        """延迟初始化 ATOM（触发依赖导入）"""
        if self._initialized:
            return

        try:
            from itext2kg.atom import Atom  # type: ignore
        except Exception as e:
            raise ImportError(
                "未安装 itext2kg。请安装：pip install -U itext2kg"
            ) from e

        self._atom = Atom(llm_model=self.llm_model, embeddings_model=self.embeddings_model)
        self._initialized = True
        logger.info("IText2KGExtractor 初始化完成")

    def extract_to_graph(self, text: str) -> Graph:
        """
        从文本抽取知识图谱
        
        Args:
            text: 输入文本
            
        Returns:
            dynhalting.Graph 实例
        """
        self._initialize()

        t0 = time.time()
        sents = _split_sentences(text)
        atomic_facts = _clamp_atomic_facts(
            sents,
            max_facts=self.max_atomic_facts,
            max_chars_per_fact=self.max_chars_per_fact
        )

        if not atomic_facts:
            g = Graph()
            g.source = "bottom_up"
            g._metadata.update({"extractor": "itext2kg", "reason": "empty_input"})
            return g

        obs_timestamp = time.strftime(self.obs_timestamp_format)
        logger.info(f"IText2KGExtractor 开始抽取: facts={len(atomic_facts)}, obs_timestamp={obs_timestamp}")

        kg = _run_maybe_async(
            self._atom.build_graph,
            atomic_facts=atomic_facts,
            obs_timestamp=obs_timestamp,
            existing_knowledge_graph=None,
            ent_threshold=self.ent_threshold,
            rel_threshold=self.rel_threshold,
            entity_name_weight=self.entity_name_weight,
            entity_label_weight=self.entity_label_weight,
            max_workers=self.max_workers,
        )

        triples = _kg_to_triples(kg)

        g = Graph()
        g.source = "bottom_up"
        g._metadata.update({
            "extractor": "itext2kg",
            "atomic_facts": len(atomic_facts),
            "obs_timestamp": obs_timestamp,
            "triple_count": len(triples),
            "elapsed_ms": int((time.time() - t0) * 1000),
        })

        node_id_by_label: Dict[str, str] = {}

        def get_or_add_node(label: str) -> str:
            label = label.strip()
            if label in node_id_by_label:
                return node_id_by_label[label]
            node_id = f"ent:{len(node_id_by_label) + 1}"
            node_id_by_label[label] = node_id
            g.add_node(Node(node_id, label, node_type="entity", state={"expandable": False}))
            return node_id

        for subj, rel, obj in triples:
            sid = get_or_add_node(subj)
            oid = get_or_add_node(obj)
            try:
                g.add_edge(Edge(source=sid, target=oid, relation=rel))
            except Exception as e:
                logger.debug(f"跳过无法添加的边: ({subj})-[{rel}]->({obj}) err={e}")

        logger.info(
            f"IText2KGExtractor 抽取完成: nodes={len(g.nodes)}, edges={len(g.edges)}, "
            f"elapsed_ms={g.metadata.get('elapsed_ms')}"
        )
        return g
