"""Memory RAG - 长期记忆向量检索"""
import logging
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class MemoryRAG:
    """对话摘要向量检索 - 使用 ChromaDB 实现语义搜索"""

    COLLECTION_NAME = "conversation_summaries"

    def __init__(self, embedding_manager, persist_directory: str = None):
        self.embedding_manager = embedding_manager
        self.persist_directory = persist_directory or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), ".chroma"
        )
        self._client = None
        self._collection = None
        self._initialized = False

    def _init_chroma(self):
        """初始化 ChromaDB"""
        if self._initialized:
            return

        try:
            import chromadb
            from chromadb.config import Settings

            os.makedirs(self.persist_directory, exist_ok=True)

            logger.info(f"【MemoryRAG】初始化 ChromaDB，路径: {self.persist_directory}")

            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )

            try:
                self._collection = self._client.get_collection(self.COLLECTION_NAME)
                logger.info(f"【MemoryRAG】加载已有集合，当前记忆数: {self._collection.count()}")
            except Exception:
                from rag.embeddings import get_embedding_dim
                dim = get_embedding_dim()
                self._collection = self._client.create_collection(
                    name=self.COLLECTION_NAME,
                    metadata={"dimension": dim}
                )
                logger.info(f"【MemoryRAG】创建新集合，维度: {dim}")

            self._initialized = True

        except ImportError:
            logger.warning("【MemoryRAG】ChromaDB 未安装，长期记忆将不可用")
            self._initialized = False
        except Exception as e:
            logger.error(f"【MemoryRAG】ChromaDB 初始化失败: {e}")
            self._initialized = False

    def add_memory(
        self,
        user_id: str,
        summary: str,
        key_entities: List[str],
        topics: List[str],
        conversation_turns: int
    ) -> Optional[str]:
        """添加对话摘要到向量数据库

        Args:
            user_id: 用户 ID
            summary: 对话摘要内容
            key_entities: 关键实体列表
            topics: 主题列表
            conversation_turns: 对话轮次数

        Returns:
            memory_id: 记忆 ID，失败返回 None
        """
        self._init_chroma()

        if not self._initialized or not self._collection:
            logger.warning("【MemoryRAG】未初始化，无法添加记忆")
            return None

        try:
            memory_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()

            # 构建完整文本用于 embedding
            entities_str = ", ".join(key_entities) if key_entities else "无"
            topics_str = ", ".join(topics) if topics else "无"
            full_text = f"用户 {user_id} 的对话摘要：{summary}。关键实体：{entities_str}。主题：{topics_str}。"

            metadata = {
                "user_id": user_id,
                "summary": summary,
                "key_entities": entities_str,
                "topics": topics_str,
                "conversation_turns": conversation_turns,
                "timestamp": timestamp
            }

            embedding = self.embedding_manager.embed_query(full_text)
            self._collection.add(
                ids=[memory_id],
                documents=[full_text],
                embeddings=[embedding],
                metadatas=[metadata]
            )

            logger.info(f"【MemoryRAG】添加记忆成功: user_id={user_id}, memory_id={memory_id}, 轮次={conversation_turns}")
            return memory_id

        except Exception as e:
            logger.error(f"【MemoryRAG】添加记忆失败: {e}")
            return None

    def search_by_embedding(self, query_embedding: List[float], user_id: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """使用已计算的 query embedding 检索用户相关记忆"""
        self._init_chroma()

        if not self._initialized or not self._collection:
            return []

        try:
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where={"user_id": user_id},
                include=["documents", "metadatas", "distances"]
            )

            memories = []
            if results and results['ids']:
                for i, memory_id in enumerate(results['ids'][0]):
                    distance = results['distances'][0][i] if 'distances' in results else 0
                    metadata = results['metadatas'][0][i] if 'metadatas' in results else {}
                    similarity = 1 - distance if distance is not None else 0

                    memories.append({
                        "memory_id": memory_id,
                        "summary": metadata.get('summary', ''),
                        "key_entities": metadata.get('key_entities', ''),
                        "topics": metadata.get('topics', ''),
                        "conversation_turns": metadata.get('conversation_turns', 0),
                        "timestamp": metadata.get('timestamp', ''),
                        "similarity": similarity,
                        "distance": distance
                    })

            return memories

        except Exception as e:
            logger.error(f"【MemoryRAG】检索失败: {e}")
            return []

    def search(self, query: str, user_id: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """语义检索用户相关记忆"""
        try:
            query_embedding = self.embedding_manager.embed_query(query)
            memories = self.search_by_embedding(query_embedding, user_id, top_k=top_k)
            logger.info(f"【MemoryRAG】检索 user_id={user_id}, query='{query}' 返回 {len(memories)} 条记忆")
            return memories
        except Exception as e:
            logger.error(f"【MemoryRAG】检索失败: {e}")
            return []

    def get_recent_memories(self, user_id: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """按时间获取用户最近的记忆

        Args:
            user_id: 用户 ID
            top_k: 返回数量

        Returns:
            记忆列表（按时间倒序）
        """
        self._init_chroma()

        if not self._initialized or not self._collection:
            return []

        try:
            results = self._collection.get(
                where={"user_id": user_id},
                include=["metadatas"]
            )

            if not results or not results['ids']:
                return []

            memories = []
            for i, memory_id in enumerate(results['ids']):
                metadata = results['metadatas'][i] if 'metadatas' in results else {}
                memories.append({
                    "memory_id": memory_id,
                    "summary": metadata.get('summary', ''),
                    "key_entities": metadata.get('key_entities', ''),
                    "topics": metadata.get('topics', ''),
                    "conversation_turns": metadata.get('conversation_turns', 0),
                    "timestamp": metadata.get('timestamp', '')
                })

            # 按时间倒序
            memories.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return memories[:top_k]

        except Exception as e:
            logger.error(f"【MemoryRAG】获取最近记忆失败: {e}")
            return []

    def count(self, user_id: str) -> int:
        """获取用户记忆数量"""
        self._init_chroma()

        if not self._initialized or not self._collection:
            return 0

        try:
            results = self._collection.get(
                where={"user_id": user_id},
                include=[]
            )
            return len(results['ids']) if results and results['ids'] else 0
        except Exception as e:
            logger.error(f"【MemoryRAG】计数失败: {e}")
            return 0

    def delete_user_memories(self, user_id: str):
        """删除用户所有记忆"""
        self._init_chroma()

        if not self._initialized or not self._collection:
            return

        try:
            results = self._collection.get(
                where={"user_id": user_id},
                include=["ids"]
            )
            if results and results['ids']:
                self._collection.delete(ids=results['ids'])
                logger.info(f"【MemoryRAG】删除用户 {user_id} 的 {len(results['ids'])} 条记忆")
        except Exception as e:
            logger.error(f"【MemoryRAG】删除记忆失败: {e}")
