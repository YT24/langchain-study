"""Embedding 模型管理 - 支持本地 sentence-transformers 和 OpenAI-compatible embeddings"""
import logging
from functools import lru_cache
from typing import Callable, List, Optional

from agent.settings import get_settings

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
DEFAULT_EMBEDDING_DIM = 512


def _resolve_embedding_dimension(model, default: int = DEFAULT_EMBEDDING_DIM) -> int:
    getter = getattr(model, "get_sentence_embedding_dimension", None)
    if callable(getter):
        dim = getter()
        if dim:
            return dim

    getter = getattr(model, "get_embedding_dimension", None)
    if callable(getter):
        dim = getter()
        if dim:
            return dim

    return default


class EmbeddingManager:
    """Embedding 管理器，支持本地和云端 embeddings"""

    def __init__(
        self,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
        provider: str = "local",
        base_url: str = "",
        api_key: str = "",
    ):
        self.model_name = model_name
        self.provider = provider
        self.base_url = base_url
        self.api_key = api_key
        self._embedding_fn: Optional[Callable[[List[str]], List[List[float]]]] = None
        self._model = None

    def _load_local_model(self) -> bool:
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"【Embedding】加载本地模型: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"【Embedding】模型加载完成，维度: {_resolve_embedding_dimension(self._model)}")
            return True
        except Exception as e:
            logger.error(f"【Embedding】本地模型加载失败: {e}")
            return False

    def _build_local_embedding_fn(self) -> Callable[[List[str]], List[List[float]]]:
        if not self._load_local_model():
            raise RuntimeError("本地 embedding 模型初始化失败")

        def embed_texts(texts: List[str]) -> List[List[float]]:
            embeddings = self._model.encode(texts, normalize_embeddings=True)
            return embeddings.tolist()

        return embed_texts

    def _build_openai_compatible_embedding_fn(self) -> Callable[[List[str]], List[List[float]]]:
        if not self.api_key or not self.base_url:
            raise RuntimeError("OpenAI-compatible embedding provider 缺少 base_url 或 api_key")

        from langchain_openai import OpenAIEmbeddings

        embeddings = OpenAIEmbeddings(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
        )
        return embeddings.embed_documents

    def _get_embedding_fn(self) -> Callable[[List[str]], List[List[float]]]:
        if self._embedding_fn is not None:
            return self._embedding_fn

        if self.provider == "local":
            self._embedding_fn = self._build_local_embedding_fn()
            return self._embedding_fn

        if self.provider == "openai_compatible":
            logger.warning("【Embedding】使用 OpenAI-compatible provider")
            self._embedding_fn = self._build_openai_compatible_embedding_fn()
            return self._embedding_fn

        raise RuntimeError(f"不支持的 embedding provider: {self.provider}")

    def embed(self, texts: List[str]) -> List[List[float]]:
        embed_fn = self._get_embedding_fn()
        try:
            return embed_fn(texts)
        except Exception as e:
            logger.error(f"【Embedding】embedding 失败: {e}")
            raise

    def embed_query(self, text: str) -> List[float]:
        return self.embed([text])[0]


_embedding_manager: Optional[EmbeddingManager] = None


@lru_cache
def get_embedding_model() -> EmbeddingManager:
    global _embedding_manager
    if _embedding_manager is None:
        settings = get_settings()
        _embedding_manager = EmbeddingManager(
            model_name=settings.embedding_model,
            provider=settings.embedding_provider,
            base_url=settings.embedding_base_url,
            api_key=settings.embedding_api_key,
        )
    return _embedding_manager


def get_embedding_dim() -> int:
    manager = get_embedding_model()
    if manager._model:
        return _resolve_embedding_dimension(manager._model)
    return DEFAULT_EMBEDDING_DIM


def validate_embedding_setup() -> None:
    manager = get_embedding_model()
    manager._get_embedding_fn()


def reset_embedding_model() -> None:
    global _embedding_manager
    _embedding_manager = None
    get_embedding_model.cache_clear()


def create_embedding_manager_for_tests(**kwargs) -> EmbeddingManager:
    return EmbeddingManager(**kwargs)


__all__ = [
    "EmbeddingManager",
    "get_embedding_model",
    "get_embedding_dim",
    "validate_embedding_setup",
    "reset_embedding_model",
    "create_embedding_manager_for_tests",
]
