"""
IText2KG 抽取器构建器

职责：
- 从配置和环境变量构建 LLM/embeddings 实例
- 将构建好的实例注入 IText2KGExtractor
- 与抽取器本身解耦，便于测试和复用
"""

from typing import Any, Dict, Optional
import os


def build_itext2kg_extractor(params: Optional[Dict[str, Any]] = None):
    """
    从配置参数构建 IText2KGExtractor
    
    职责分离：
    - 本函数负责读取环境变量、构建 LLM/embeddings
    - IText2KGExtractor 只负责调用 itext2kg
    
    Args:
        params: 配置参数（从 modules.yaml 读取）
        
    Returns:
        IText2KGExtractor 实例
    """
    from .itext2kg_extractor import IText2KGExtractor
    
    params = params or {}
    
    # 1. 读取 API key（从环境变量，固定为 OPENROUTER_API_KEY）
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "构建 IText2KGExtractor 失败：环境变量 OPENROUTER_API_KEY 未设置。"
            "请在项目根目录 .env 文件中设置：OPENROUTER_API_KEY=your-key"
        )
    
    # 2. 构建 LLM（LangChain ChatOpenAI）
    try:
        from langchain_openai import ChatOpenAI  # type: ignore
    except Exception as e:
        raise ImportError(
            "未安装 langchain_openai。请安装：pip install -U langchain-openai langchain"
        ) from e
    
    chat_model = params.get("chat_model", "google/gemini-2.5-flash-lite")
    base_url = params.get("base_url", "https://openrouter.ai/api/v1")
    llm_max_tokens = params.get("llm_max_tokens", 512)
    llm_timeout = params.get("llm_timeout", 60)
    llm_max_retries = params.get("llm_max_retries", 0)
    
    llm_kwargs = {
        "model": chat_model,
        "temperature": 0.0,
        "max_tokens": int(llm_max_tokens),
        "timeout": int(llm_timeout),
        "max_retries": int(llm_max_retries),
    }
    if base_url:
        llm_kwargs["base_url"] = base_url
    
    try:
        llm_model = ChatOpenAI(api_key=api_key, **llm_kwargs)
    except TypeError:
        llm_model = ChatOpenAI(openai_api_key=api_key, **llm_kwargs)
    
    # 3. 构建 embeddings
    embeddings_model_name = params.get("embeddings_model", "sentence-transformers/all-MiniLM-L6-v2")
    
    if embeddings_model_name.startswith("sentence-transformers/"):
        # 使用本地 sentence-transformers
        embeddings_model = _build_sentence_transformer_embeddings(embeddings_model_name)
    else:
        # 使用远程 OpenAI-compatible embeddings
        try:
            from langchain_openai import OpenAIEmbeddings  # type: ignore
        except Exception as e:
            raise ImportError(
                "未安装 langchain_openai.OpenAIEmbeddings。请安装：pip install -U langchain-openai"
            ) from e
        
        emb_kwargs = {"model": embeddings_model_name}
        if base_url:
            emb_kwargs["base_url"] = base_url
        try:
            embeddings_model = OpenAIEmbeddings(api_key=api_key, **emb_kwargs)
        except TypeError:
            embeddings_model = OpenAIEmbeddings(openai_api_key=api_key, **emb_kwargs)
    
    # 4. 构建抽取器（依赖注入）
    extractor_params = {
        "llm_model": llm_model,
        "embeddings_model": embeddings_model,
        "ent_threshold": params.get("ent_threshold", 0.8),
        "rel_threshold": params.get("rel_threshold", 0.7),
        "entity_name_weight": params.get("entity_name_weight", 0.8),
        "entity_label_weight": params.get("entity_label_weight", 0.2),
        "max_workers": params.get("max_workers", 4),
        "max_atomic_facts": params.get("max_atomic_facts", 40),
        "max_chars_per_fact": params.get("max_chars_per_fact", 280),
        "obs_timestamp_format": params.get("obs_timestamp_format", "%d-%m-%Y"),
    }
    
    return IText2KGExtractor(**extractor_params)


def _build_sentence_transformer_embeddings(model_name: str):
    """构建 sentence-transformers 的 LangChain 适配器"""
    from sentence_transformers import SentenceTransformer  # type: ignore
    
    class SentenceTransformerAdapter:
        def __init__(self, model_name: str):
            self._model = SentenceTransformer(model_name)
        
        def embed_documents(self, texts):
            vecs = self._model.encode(texts, normalize_embeddings=True)
            return [v.tolist() for v in vecs]
        
        async def aembed_documents(self, texts):
            return self.embed_documents(texts)
        
        def embed_query(self, text):
            v = self._model.encode([text], normalize_embeddings=True)[0]
            return v.tolist()
        
        async def aembed_query(self, text):
            return self.embed_query(text)
    
    return SentenceTransformerAdapter(model_name)
