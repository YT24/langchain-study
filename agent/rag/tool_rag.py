"""Tool RAG - 基于向量数据库的工具语义检索"""
import logging
import os
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ToolRAG:
    """工具向量检索 - 使用 ChromaDB 实现语义搜索"""

    def __init__(self, embedding_manager, persist_directory: str = None):
        self.embedding_manager = embedding_manager
        # 默认持久化到 .chroma 目录
        self.persist_directory = persist_directory or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), ".chroma"
        )
        self._client = None
        self._collection = None
        self._initialized = False
        self._tools_meta: Dict[str, Dict[str, Any]] = {}  # tool_name -> metadata

    def _init_chroma(self):
        """初始化 ChromaDB"""
        if self._initialized:
            return

        try:
            import chromadb
            from chromadb.config import Settings

            os.makedirs(self.persist_directory, exist_ok=True)

            logger.info(f"【ToolRAG】初始化 ChromaDB，路径: {self.persist_directory}")

            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )

            # 尝试获取已有集合，或创建新集合
            try:
                self._collection = self._client.get_collection("tool_descriptions")
                logger.info(f"【ToolRAG】加载已有集合，当前工具数: {self._collection.count()}")
            except Exception:
                from rag.embeddings import get_embedding_dim
                dim = get_embedding_dim()
                self._collection = self._client.create_collection(
                    name="tool_descriptions",
                    metadata={"dimension": dim}
                )
                logger.info(f"【ToolRAG】创建新集合，维度: {dim}")

            self._initialized = True

        except ImportError:
            logger.warning("【ToolRAG】ChromaDB 未安装，将使用关键词匹配")
            self._initialized = False
        except Exception as e:
            logger.error(f"【ToolRAG】ChromaDB 初始化失败: {e}")
            self._initialized = False

    def load_tools(self, tools: List[Any]):
        """加载工具描述到向量数据库

        Args:
            tools: LangChain Tool 对象列表
        """
        self._init_chroma()

        if not tools:
            logger.warning("【ToolRAG】没有工具需要加载")
            return

        logger.info(f"【ToolRAG】开始加载 {len(tools)} 个工具")

        # 清空旧数据（如果存在）
        try:
            if self._collection.count() > 0:
                self._client.delete_collection("tool_descriptions")
                from rag.embeddings import get_embedding_dim
                dim = get_embedding_dim()
                self._collection = self._client.create_collection(
                    name="tool_descriptions",
                    metadata={"dimension": dim}
                )
                self._tools_meta.clear()
        except Exception:
            pass

        # 准备数据
        ids = []
        texts = []
        metadatas = []

        for tool in tools:
            tool_id = tool.name
            # 组合工具的描述信息用于 embedding
            description = tool.description if hasattr(tool, 'description') else str(tool)

            # 获取工具参数信息
            params_info = ""
            if hasattr(tool, 'input_schema') and tool.input_schema:
                try:
                    if hasattr(tool.input_schema, 'model_fields'):
                        fields = tool.input_schema.model_fields
                        params_info = ", ".join([
                            f"{name}: {field.annotation.__name__ if hasattr(field.annotation, '__name__') else str(field.annotation)}"
                            for name, field in fields.items()
                        ])
                except Exception:
                    pass

            # 组合完整文本
            full_text = f"{tool.name}: {description}"
            if params_info:
                full_text += f". 参数: {params_info}"

            ids.append(tool_id)
            texts.append(full_text)
            metadatas.append({
                "tool_name": tool.name,
                "description": description,
                "params_info": params_info
            })
            self._tools_meta[tool_id] = {
                "tool": tool,
                "description": description
            }

        # 批量添加
        if self._initialized and self._collection:
            try:
                embeddings = self.embedding_manager.embed(texts)
                self._collection.add(
                    ids=ids,
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
                logger.info(f"【ToolRAG】成功索引 {len(tools)} 个工具")
            except Exception as e:
                logger.error(f"【ToolRAG】索引失败: {e}，将使用关键词匹配")

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """语义检索最相关的工具

        Args:
            query: 用户查询
            top_k: 返回数量

        Returns:
            工具信息列表
        """
        # 如果未初始化或集合为空，返回空
        if not self._initialized or not self._collection:
            return []

        if self._collection.count() == 0:
            logger.warning("【ToolRAG】索引为空")
            return []

        try:
            # 获取 query 的 embedding
            query_embedding = self.embedding_manager.embed_query(query)

            # 检索
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )

            # 整理结果
            tools = []
            if results and results['ids']:
                for i, tool_id in enumerate(results['ids'][0]):
                    distance = results['distances'][0][i] if 'distances' in results else 0
                    metadata = results['metadatas'][0][i] if 'metadatas' in results else {}

                    # 将距离转换为相似度 (0-1, 越大越相似)
                    similarity = 1 - distance if distance is not None else 0

                    tools.append({
                        "tool_name": tool_id,
                        "description": metadata.get('description', ''),
                        "params_info": metadata.get('params_info', ''),
                        "similarity": similarity,
                        "distance": distance
                    })

            logger.info(f"【ToolRAG】检索 query='{query}' 返回 {len(tools)} 个结果")
            for t in tools:
                logger.info(f"  - {t['tool_name']}: 相似度={t['similarity']:.3f}")

            return tools

        except Exception as e:
            logger.error(f"【ToolRAG】检索失败: {e}")
            return []

    def find_similar_tools(self, query: str, threshold: float = 0.5) -> List[str]:
        """查找相似的工具名

        Args:
            query: 查询
            threshold: 相似度阈值 (0-1)

        Returns:
            工具名列表
        """
        results = self.search(query, top_k=5)
        return [
            r['tool_name'] for r in results
            if r['similarity'] >= threshold
        ]

    def reload(self, tools: List[Any]):
        """重新加载工具"""
        self._initialized = False
        self._tools_meta.clear()
        self.load_tools(tools)
