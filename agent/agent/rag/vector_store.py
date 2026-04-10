"""
向量数据库模块
支持 ChromaDB 作为向量存储
"""
import os
from typing import List, Dict, Optional

from langchain.vectorstores import Chroma


# 为了兼容国内环境，使用自定义 embedding
class DeepSeekEmbeddings:
    """使用 DeepSeek API 的 embedding"""
    def __init__(self, api_key: str = None, api_base: str = "https://api.deepseek.com"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.api_base = api_base

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        import requests
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "input": texts
        }
        response = requests.post(
            f"{self.api_base}/embeddings",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        return [item["embedding"] for item in result["data"]]

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]


class VectorStore:
    """向量存储管理器"""

    COLLECTIONS = {
        "tools": "agent_tools",
        "knowledge": "agent_knowledge",
        "user_memory": "user_memories",
        "conversations": "conversation_summaries"
    }

    def __init__(self, persist_directory: str = "./vector_store"):
        self.persist_directory = persist_directory
        self.embeddings = DeepSeekEmbeddings()
        self._init_collections()

    def _init_collections(self):
        """初始化所有集合"""
        self.collections = {}
        for name, collection_name in self.COLLECTIONS.items():
            self.collections[name] = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )

    def add_texts(self, collection: str, texts: List[str], metadatas: List[Dict] = None, ids: List[str] = None):
        """添加文本到指定集合"""
        if collection not in self.collections:
            raise ValueError(f"Unknown collection: {collection}")

        ids = ids or [f"doc_{i}" for i in range(len(texts))]
        self.collections[collection].add_texts(texts=texts, metadatas=metadatas, ids=ids)
        self.collections[collection].persist()

    def search(self, collection: str, query: str, top_k: int = 5) -> List[Dict]:
        """检索相似文本"""
        if collection not in self.collections:
            raise ValueError(f"Unknown collection: {collection}")

        results = self.collections[collection].similar_search_with_score(query, k=top_k)
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score
            }
            for doc, score in results
        ]

    def delete_collection(self, collection: str):
        """删除集合"""
        if collection in self.collections:
            self.collections[collection].delete_collection()
            del self.collections[collection]

    def get_collection(self, collection: str) -> Optional[Chroma]:
        """获取集合"""
        return self.collections.get(collection)
