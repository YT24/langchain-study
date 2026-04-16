"""Embedding 模型管理 - 支持本地 sentence-transformers 和 OpenAI embeddings"""
import os
import logging
from typing import List, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

# 默认使用本地 BGE 模型（中文效果好）
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
DEFAULT_EMBEDDING_DIM = 512


class EmbeddingManager:
    """Embedding 管理器，支持本地和云端 embeddings"""

    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL):
        self.model_name = model_name
        self._embedding_fn = None
        self._model = None

    def _load_local_model(self):
        """加载本地 sentence-transformers 模型"""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"【Embedding】加载本地模型: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"【Embedding】模型加载完成，维度: {self._model.get_embedding_dimension()}")
            return True
        except Exception as e:
            logger.error(f"【Embedding】本地模型加载失败: {e}")
            return False

    def _get_embedding_fn(self):
        """获取 embedding 函数"""
        if self._embedding_fn is not None:
            return self._embedding_fn

        # 优先尝试本地模型
        if self._load_local_model():
            def embed_texts(texts: List[str]) -> List[List[float]]:
                embeddings = self._model.encode(texts, normalize_embeddings=True)
                return embeddings.tolist()

            self._embedding_fn = embed_texts
            return self._embedding_fn

        # 降级：使用 OpenAI embeddings
        logger.warning("【Embedding】降级使用 OpenAI text-embedding-3-small")
        try:
            from langchain_openai import OpenAIEmbeddings
            embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url=f"{os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')}/v1"
            )
            self._embedding_fn = embeddings.embed_texts
            return self._embedding_fn
        except Exception as e:
            logger.error(f"【Embedding】OpenAI embeddings 初始化失败: {e}")
            raise RuntimeError("无法初始化 embedding 模型")

    def embed(self, texts: List[str]) -> List[List[float]]:
        """获取文本的 embedding"""
        embed_fn = self._get_embedding_fn()
        try:
            return embed_fn(texts)
        except Exception as e:
            logger.error(f"【Embedding】embedding 失败: {e}")
            raise

    def embed_query(self, text: str) -> List[float]:
        """获取单个查询的 embedding"""
        return self.embed([text])[0]


# 全局单例
_embedding_manager: Optional[EmbeddingManager] = None


@lru_cache
def get_embedding_model() -> EmbeddingManager:
    """获取全局 embedding 管理器（单例）"""
    global _embedding_manager
    if _embedding_manager is None:
        _embedding_manager = EmbeddingManager()
    return _embedding_manager


def get_embedding_dim() -> int:
    """获取 embedding 维度"""
    manager = get_embedding_model()
    if manager._model:
        return manager._model.get_embedding_dimension()
    return DEFAULT_EMBEDDING_DIM
