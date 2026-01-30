"""
REBEL 三元组抽取器（合并重构版）
将原 utils/rebel_extractor.py 的逻辑合并至此，消除架构分层混乱。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple, Any, Dict

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from kgforge.models import Edge, Graph, Node
from kgforge.utils import get_logger
from kgforge.components.base import BaseExtractor
from kgforge.protocols import IPreloadable, IConfigurable

logger = get_logger(__name__)

# 局部默认配置
DEFAULT_REBEL_MODEL = "Babelscape/rebel-large"
DEFAULT_REBEL_MAX_LENGTH = 512


def _split_sentences_regex(text: str) -> List[Tuple[int, int, str]]:
    """正则分句（spaCy 不可用时的降级方案）"""
    if not text:
        return []
    sentences: List[Tuple[int, int, str]] = []
    sentence_endings = re.compile(r"([.!?。！？]\s+|\.\s*$)")
    start = 0
    for match in sentence_endings.finditer(text):
        end = match.end()
        sent = text[start:end].strip()
        if sent:
            sentences.append((start, end, sent))
        start = end
    if start < len(text):
        sent = text[start:].strip()
        if sent:
            sentences.append((start, len(text), sent))
    return sentences


def _try_build_spacy_sentencizer(lang: str):
    """
    构造 spaCy 分句器（不依赖下载语言模型）。
    返回 nlp 或 None（如果 spaCy 未安装/初始化失败）。
    """
    try:
        import spacy  # type: ignore

        nlp = spacy.blank(lang)
        if "sentencizer" not in nlp.pipe_names:
            nlp.add_pipe("sentencizer")
        return nlp
    except Exception as e:
        logger.warning(f"spaCy 分句初始化失败，将降级为正则分句：{e}")
        return None


@dataclass(frozen=True)
class _SentenceSpan:
    start: int
    end: int
    text: str
    tokens: int


class RebelExtractorAppliance(BaseExtractor, IPreloadable, IConfigurable):
    """
    基于 REBEL 的三元组抽取器具
    直接集成了模型推理逻辑，不再依赖 utils 包。
    """
    name = "rebel"

    def __init__(self, config: Dict[str, Any] = None, **kwargs):
        # 兼容工厂模式传递的 kwargs
        mapped_config = (config or {}).copy()
        mapped_config.update(kwargs)
        super().__init__(mapped_config)
        
        # 从 config 提取参数，设置默认值
        self.model_name = self.config.get("model_name", DEFAULT_REBEL_MODEL)
        self.device = self.config.get("device") or ("cuda" if torch.cuda.is_available() else "cpu")
        
        self.window_size = int(self.config.get("window_size", 480))
        self.overlap_tokens = int(self.config.get("overlap_tokens", 64))
        self.align_sentence_boundary = bool(self.config.get("align_sentence_boundary", True))
        
        self.batch_size = self.config.get("batch_size")
        self.num_beams = int(self.config.get("num_beams", 3))
        self.max_new_tokens = int(self.config.get("max_new_tokens", 384))
        self.length_penalty = float(self.config.get("length_penalty", 1.1))
        
        self.use_spacy_sentence_split = bool(self.config.get("use_spacy_sentence_split", True))
        self.spacy_lang = self.config.get("spacy_lang", "en")
        
        # 内部状态
        self.tokenizer = None
        self.model = None
        self._initialized = False
        self._spacy_nlp = None

    @classmethod
    def get_component_spec(cls) -> Dict[str, Any]:
        return {
            "id": "rebel",
            "name": "REBEL抽取器",
            "description": "基于 Babelscape/rebel-large 模型，从非结构化文本中抽取实体关系三元组。支持滑动窗口和批处理推理。",
            "params": {
                "model_name": {"type": "string", "default": DEFAULT_REBEL_MODEL, "description": "HuggingFace 模型路径"},
                "device": {"type": "string", "enum": ["cpu", "cuda", "mps"], "default": "cpu"},
                "window_size": {"type": "integer", "default": 480, "description": "滑动窗口大小(token)"},
                "batch_size": {"type": "integer", "default": 2, "description": "推理 batch 大小"}
            },
            "capabilities": ["Configurable", "Preloadable"]
        }

    # ==================== Core Implementation (Ported from Utils) ====================

    def _initialize(self):
        """延迟加载模型（首次使用时）"""
        if self._initialized:
            return
        
        try:
            logger.info(f"正在加载 REBEL 模型: {self.model_name} (设备: {self.device})...")
            # logger.info("注意：首次运行需要下载模型（约1.5GB），请确保网络连接正常")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            self._initialized = True
            logger.info("REBEL 模型加载完成")
        except Exception as e:
            error_msg = (
                f"REBEL 模型加载失败: {e}\n"
                f"可能的原因：\n"
                f"1. 网络连接问题（需要从 HuggingFace 下载模型）\n"
                f"2. 磁盘空间不足（模型约需 1.5GB）\n"
                f"3. 模型名称错误或不可用\n"
                f"请检查网络连接和磁盘空间后重试"
            )
            # raise RuntimeError(error_msg) from e
            logger.error(error_msg)
            raise e

    def _ensure_spacy(self):
        if not self.use_spacy_sentence_split:
            return
        if self._spacy_nlp is None:
            self._spacy_nlp = _try_build_spacy_sentencizer(self.spacy_lang)

    def _count_tokens(self, text: str) -> int:
        assert self.tokenizer is not None
        return len(self.tokenizer.encode(text, add_special_tokens=False))

    def _split_sentences(self, text: str) -> List[Tuple[int, int, str]]:
        if not text:
            return []

        if self.use_spacy_sentence_split:
            self._ensure_spacy()
            if self._spacy_nlp is not None:
                doc = self._spacy_nlp(text)
                spans: List[Tuple[int, int, str]] = []
                for sent in doc.sents:
                    s = text[sent.start_char : sent.end_char].strip()
                    if s:
                        spans.append((sent.start_char, sent.end_char, s))
                if spans:
                    return spans

        return _split_sentences_regex(text)

    def _create_windows(self, text: str, max_length: int) -> List[Tuple[int, int, str, int]]:
        if not self._initialized:
            self._initialize()
        assert self.tokenizer is not None

        if not text or not text.strip():
            return []
        
        effective_window = max(16, min(int(max_length), int(self.window_size)))
        effective_overlap = max(0, min(int(self.overlap_tokens), effective_window - 1))
        
        if self._count_tokens(text) <= effective_window:
            return [(0, len(text), text, 0)]
        
        if not self.align_sentence_boundary:
            approx_chars_per_token = 4
            step = max(1, (effective_window - effective_overlap) * approx_chars_per_token)
            win_chars = effective_window * approx_chars_per_token
            windows: List[Tuple[int, int, str, int]] = []
            start = 0
            cid = 0
            while start < len(text):
                end = min(start + win_chars, len(text))
                windows.append((start, end, text[start:end], cid))
                cid += 1
                if end >= len(text):
                    break
                start += step
            return windows

        # spaCy/正则分句 + token 计数聚合
        raw_sents = self._split_sentences(text)
        if not raw_sents:
            return [(0, len(text), text, 0)]

        sent_spans: List[_SentenceSpan] = []
        for s_start, s_end, s_text in raw_sents:
            tok = self._count_tokens(s_text)
            sent_spans.append(_SentenceSpan(start=s_start, end=s_end, text=s_text, tokens=tok))

        windows: List[Tuple[int, int, str, int]] = []
        current: List[_SentenceSpan] = []
        current_tokens = 0
        cid = 0

        def flush_window():
            nonlocal cid, current, current_tokens
            if not current:
                return
            w_start = current[0].start
            w_end = current[-1].end
            windows.append((w_start, w_end, text[w_start:w_end], cid))
            cid += 1

            if effective_overlap <= 0:
                current = []
                current_tokens = 0
                return

            kept: List[_SentenceSpan] = []
            kept_tokens = 0
            for s in reversed(current):
                if kept_tokens + s.tokens <= effective_overlap:
                    kept.insert(0, s)
                    kept_tokens += s.tokens
                else:
                    break
            current = kept
            current_tokens = kept_tokens

        for sent in sent_spans:
            if sent.tokens > effective_window:
                if current:
                    flush_window()
                logger.warning(
                    f"检测到超长句子（tokens={sent.tokens} > window={effective_window}），"
                    "将单独作为窗口并在 tokenize 阶段截断。"
                )
                windows.append((sent.start, sent.end, text[sent.start:sent.end], cid))
                cid += 1
                current = []
                current_tokens = 0
                continue

            if current and (current_tokens + sent.tokens > effective_window):
                flush_window()

            current.append(sent)
            current_tokens += sent.tokens

        if current:
            flush_window()

        logger.info(
            f"创建了 {len(windows)} 个滑动窗口（window={effective_window} tokens）"
        )
        return windows
    
    def _generate_batched(self, window_texts: List[str], max_length: int) -> List[str]:
        assert self.tokenizer is not None
        assert self.model is not None

        tokenized = self.tokenizer(
            window_texts,
            max_length=max_length,
            padding=True,
            truncation=True,
            return_tensors="pt",
        ).to(self.device)
            
        model_limit = 1024 # Simplified for safety
        max_input_len = int(tokenized["input_ids"].shape[1])
        available = max(16, model_limit - max_input_len - 8)
        max_new = max(16, min(int(self.max_new_tokens), int(available)))
        
        with torch.no_grad():
            outputs = self.model.generate(
                **tokenized,
                max_new_tokens=max_new,
                num_beams=self.num_beams,
                num_return_sequences=1,
                do_sample=False,
                early_stopping=True,
                length_penalty=self.length_penalty,
                pad_token_id=self.tokenizer.pad_token_id or self.tokenizer.eos_token_id,
                )
            
        decoded: List[str] = []
        for i in range(outputs.shape[0]):
            decoded.append(self.tokenizer.decode(outputs[i], skip_special_tokens=False))
        return decoded
    
    def _merge_triples(self, all_triples: List[List[Tuple[str, str, str, float, int]]]) -> List[Tuple[str, str, str, float, int]]:
        flat_triples = []
        for triples in all_triples:
            flat_triples.extend(triples)
        
        if not flat_triples:
            return []
        
        seen = {}
        unique_triples = []
        
        for triple in flat_triples:
            head, relation, tail, score, chunk_id = triple
            normalized = (
                ' '.join(head.split()).lower(),
                ' '.join(relation.split()).lower(),
                ' '.join(tail.split()).lower()
            )
            
            if normalized not in seen:
                seen[normalized] = {
                    'triple': (' '.join(head.split()), ' '.join(relation.split()), ' '.join(tail.split()), score, chunk_id),
                    'chunk_ids': {chunk_id}
                }
            else:
                seen[normalized]['chunk_ids'].add(chunk_id)
                if score > seen[normalized]['triple'][3]:
                    seen[normalized]['triple'] = (
                        seen[normalized]['triple'][0],
                        seen[normalized]['triple'][1],
                        seen[normalized]['triple'][2],
                        score,
                        seen[normalized]['triple'][4]
                    )
        
        for normalized, data in seen.items():
            h, r, t, s, cid = data['triple']
            unique_triples.append((h, r, t, s, cid))
        
        return unique_triples
    
    def _extract_triples(self, text: str, max_length: int = 512) -> List[Tuple[str, str, str, float]]:
        if not text or not text.strip():
            return []
        
        if not self._initialized:
            self._initialize()
        assert self.tokenizer is not None
        assert self.model is not None

        max_length = int(max_length or DEFAULT_REBEL_MAX_LENGTH)
        windows = self._create_windows(text, max_length=max_length)
        if not windows:
            return []

        bs = self.batch_size
        if bs is None:
            bs = 8 if str(self.device).startswith("cuda") else 2
        bs = max(1, int(bs))

        all_triples: List[List[Tuple[str, str, str, float, int]]] = []

        for batch_start in range(0, len(windows), bs):
            batch = windows[batch_start : batch_start + bs]
            batch_texts = [w[2] for w in batch]
            decoded_list = self._generate_batched(batch_texts, max_length=max_length)

            for local_i, decoded in enumerate(decoded_list):
                window_idx = batch_start + local_i
                chunk_id = batch[local_i][3]
                triples = self._parse_triples(decoded, window_idx)
                triples_with_chunk = []
                for triple in triples:
                    if self._is_valid_triple(triple):
                        triples_with_chunk.append((*triple, chunk_id))
                all_triples.append(triples_with_chunk)
            
            merged = self._merge_triples(all_triples)
            return [(h, r, t, s) for h, r, t, s, _ in merged]
        return []

    def _is_valid_triple(self, triple: Tuple[str, str, str, float]) -> bool:
        head, relation, tail, score = triple
        if not head or not relation or not tail: return False
        if '<subj>' in head or '<obj>' in head or '<triplet>' in head: return False
        if '<subj>' in relation or '<obj>' in relation or '<triplet>' in relation: return False
        if '<subj>' in tail or '<obj>' in tail or '<triplet>' in tail: return False
        if len(head) < 1 or len(relation) < 1 or len(tail) < 1: return False
        return True
    
    def _parse_triples(self, decoded_text: str, window_idx: int = -1) -> List[Tuple[str, str, str, float]]:
        triples: List[Tuple[str, str, str, float]] = []
        decoded_text = re.sub(r"</?s>", "", decoded_text)
        
        def _clean(x: str) -> str:
            x = re.sub(r"</?triplet>|</?subj>|</?obj>", "", x)
            return " ".join(x.strip().split())

        triplet_pattern = r"<triplet>(.*?)(?=</triplet>|<triplet>|$)"
        for match in re.finditer(triplet_pattern, decoded_text, re.DOTALL):
            content = match.group(1).strip()
            if not content: continue
            
            first_subj = content.find("<subj>")
            if first_subj == -1: continue
            head = _clean(content[:first_subj])
            if not head: continue
            
            pos = first_subj
            while True:
                subj_idx = content.find("<subj>", pos)
                if subj_idx == -1: break
                obj_idx = content.find("<obj>", subj_idx + len("<subj>"))
                if obj_idx == -1: break

                tail_raw = content[subj_idx + len("<subj>") : obj_idx]

                next_markers = []
                next_subj = content.find("<subj>", obj_idx + len("<obj>"))
                if next_subj != -1: next_markers.append(next_subj)
                next_triplet = content.find("<triplet>", obj_idx + len("<obj>"))
                if next_triplet != -1: next_markers.append(next_triplet)
                next_close = content.find("</triplet>", obj_idx + len("<obj>"))
                if next_close != -1: next_markers.append(next_close)

                rel_end = min(next_markers) if next_markers else len(content)
                rel_raw = content[obj_idx + len("<obj>") : rel_end]

                tail = _clean(tail_raw)
                relation = _clean(rel_raw)
                
                if head and relation and tail:
                    triples.append((head, relation, tail, 1.0))

                pos = rel_end
        
        return triples

    # ==================== Interface Implementation ====================

    def extract(self, text: str, graph_id: Optional[str] = None) -> Graph:
        """从文本抽取三元组并构建图 G_B (IExtractor 接口实现)"""
        logger.info(f"开始抽取图结构，文本长度: {len(text)} 字符")
        try:
            triples = self._extract_triples(text)
        except Exception as e:
            logger.error(f"抽取失败: {e}")
            raise e
            
        logger.info(f"抽取到 {len(triples)} 个三元组")
        
        graph = Graph(graph_id=graph_id or "G_B")
        graph.source = "bottom_up"
        
        node_map = {}
        for head, relation, tail, score in triples:
            if head not in node_map:
                head_node = Node(
                    node_id=f"entity_{len(node_map)}",
                    label=head,
                    node_type="entity",
                    state={"expandable": True, "expanded": False},
                    metadata={"source": "rebel", "original_label": head}
                )
                node_map[head] = head_node
                graph.add_node(head_node)
            else:
                head_node = node_map[head]
            
            if tail not in node_map:
                tail_node = Node(
                    node_id=f"entity_{len(node_map)}",
                    label=tail,
                    node_type="entity",
                    state={"expandable": True, "expanded": False},
                    metadata={"source": "rebel", "original_label": tail}
                )
                node_map[tail] = tail_node
                graph.add_node(tail_node)
            else:
                tail_node = node_map[tail]
            
            edge = Edge(
                source=head_node.id,
                target=tail_node.id,
                relation=relation,
                weight=score,
                metadata={"source": "rebel"}
            )
            graph.add_edge(edge)
        
        logger.info(f"图构建完成: {len(graph.nodes)} 个节点, {len(graph.edges)} 条边")
        return graph

    def preload(self):
        """IPreloadable 接口实现"""
        self._initialize()

    def update_config(self, params: dict):
        """IConfigurable 接口实现：热更新推理参数"""
        if not params:
            return
            
        allowed_params = {
            "window_size", "overlap_tokens", "align_sentence_boundary",
            "batch_size", "num_beams", "max_new_tokens", "length_penalty",
            "use_spacy_sentence_split", "spacy_lang"
        }
        
        changes = []
        for key, value in params.items():
            if key in allowed_params:
                # 简单类型转换
                if key in ["window_size", "overlap_tokens", "batch_size", "num_beams", "max_new_tokens"]:
                    new_val = int(value) if value is not None else None
                elif key == "length_penalty":
                    new_val = float(value)
                elif key in ["align_sentence_boundary", "use_spacy_sentence_split"]:
                    new_val = bool(value)
                else:
                    new_val = value
                
                old_val = getattr(self, key, None)
                if old_val != new_val:
                    setattr(self, key, new_val)
                    changes.append(f"{key}: {old_val} -> {new_val}")
        
        if changes:
            logger.info(f"REBEL 配置已热更新: {', '.join(changes)}")
