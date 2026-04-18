"""Knowledge RAG - 业务知识向量检索"""
import logging
import os
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


# 内置业务知识库
BUILTIN_KNOWLEDGE = [
    {
        "id": "order_status",
        "category": "订单状态",
        "content": """订单状态说明：
        - pending: 待处理
        - processing: 处理中
        - shipped: 已发货
        - delivered: 已送达
        - cancelled: 已取消
        - refunded: 已退款""",
        "keywords": ["订单状态", "订单情况", "发货", "取消", "退款"]
    },
    {
        "id": "vip_levels",
        "category": "会员等级",
        "content": """会员等级说明：
        - bronze: 青铜会员，享受 9.8 折
        - silver: 白银会员，享受 9.5 折
        - gold: 黄金会员，享受 9 折
        - platinum: 铂金会员，享受 8.5 折
        - diamond: 钻石会员，享受 8 折，专属客服""",
        "keywords": ["会员", "等级", "折扣", "VIP"]
    },
    {
        "id": "payment_methods",
        "category": "支付方式",
        "content": """支持的支付方式：
        - wechat: 微信支付
        - alipay: 支付宝
        - card: 银行卡
        - credit: 信用支付
        - points: 积分支付""",
        "keywords": ["支付", "付款", "微信", "支付宝", "银行卡"]
    },
    {
        "id": "return_policy",
        "category": "退换货政策",
        "content": """退换货政策：
        - 7天内可无理由退货
        - 15天内可换货
        - 生鲜食品不支持退货
        - 定制商品不支持退换
        - 退货需保持商品完好""",
        "keywords": ["退货", "退换", "退款", "售后"]
    },
    {
        "id": "shipping_info",
        "category": "配送信息",
        "content": """配送说明：
        - 普通配送: 3-7天送达，运费5元
        - 快速配送: 1-2天送达，运费15元
        - 同城配送: 当日达，运费20元
        - 满99元免运费""",
        "keywords": ["配送", "快递", "运费", "发货", "送达"]
    },
    {
        "id": "points_rules",
        "category": "积分规则",
        "content": """积分规则：
        - 每消费1元得1积分
        - 积分可抵扣现金，100积分=1元
        - 生日当天双倍积分
        - 新会员首单双倍积分
        - 积分年底不清零""",
        "keywords": ["积分", "抵扣", "兑换"]
    }
]


class KnowledgeRAG:
    """业务知识向量检索"""

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

            logger.info(f"【KnowledgeRAG】初始化 ChromaDB，路径: {self.persist_directory}")

            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )

            try:
                self._collection = self._client.get_collection("business_knowledge")
                logger.info(f"【KnowledgeRAG】加载已有知识库，当前条目数: {self._collection.count()}")
            except Exception:
                from agent.rag.embeddings import get_embedding_dim
                dim = get_embedding_dim()
                self._collection = self._client.create_collection(
                    name="business_knowledge",
                    metadata={"dimension": dim}
                )
                logger.info(f"【KnowledgeRAG】创建新知识库集合，维度: {dim}")

            self._initialized = True

        except ImportError:
            logger.warning("【KnowledgeRAG】ChromaDB 未安装")
            self._initialized = False
        except Exception as e:
            logger.error(f"【KnowledgeRAG】ChromaDB 初始化失败: {e}")
            self._initialized = False

    def load_knowledge(self, additional_knowledge: List[Dict[str, Any]] = None):
        """加载业务知识到向量数据库

        Args:
            additional_knowledge: 额外的知识条目 [{id, category, content, keywords}]
        """
        self._init_chroma()

        # 合并内置和额外知识
        all_knowledge = BUILTIN_KNOWLEDGE.copy()
        if additional_knowledge:
            all_knowledge.extend(additional_knowledge)

        logger.info(f"【KnowledgeRAG】开始加载 {len(all_knowledge)} 条知识")

        # 清空旧数据
        try:
            if self._collection.count() > 0:
                self._client.delete_collection("business_knowledge")
                from agent.rag.embeddings import get_embedding_dim
                dim = get_embedding_dim()
                self._collection = self._client.create_collection(
                    name="business_knowledge",
                    metadata={"dimension": dim}
                )
        except Exception:
            pass

        # 准备数据
        ids = []
        texts = []
        metadatas = []

        for item in all_knowledge:
            item_id = item["id"]
            # 组合文本用于 embedding
            full_text = f"{item['category']}: {item['content']}"

            ids.append(item_id)
            texts.append(full_text)
            metadatas.append({
                "category": item.get("category", ""),
                "content": item.get("content", ""),
                "keywords": ",".join(item.get("keywords", []))
            })

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
                logger.info(f"【KnowledgeRAG】成功索引 {len(all_knowledge)} 条知识")
            except Exception as e:
                logger.error(f"【KnowledgeRAG】索引失败: {e}")

    def search_by_embedding(self, query_embedding: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        """使用已计算的 query embedding 检索相关知识"""
        if not self._initialized or not self._collection:
            return []

        if self._collection.count() == 0:
            logger.warning("【KnowledgeRAG】知识库为空")
            return []

        try:
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )

            knowledge = []
            if results and results['ids']:
                for i, item_id in enumerate(results['ids'][0]):
                    distance = results['distances'][0][i] if 'distances' in results else 0
                    metadata = results['metadatas'][0][i] if 'metadatas' in results else {}
                    similarity = 1 - distance if distance is not None else 0

                    knowledge.append({
                        "id": item_id,
                        "category": metadata.get('category', ''),
                        "content": metadata.get('content', ''),
                        "keywords": metadata.get('keywords', '').split(','),
                        "similarity": similarity
                    })

            return knowledge

        except Exception as e:
            logger.error(f"【KnowledgeRAG】检索失败: {e}")
            return []

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """检索相关知识

        Args:
            query: 用户查询
            top_k: 返回数量

        Returns:
            知识条目列表
        """
        try:
            query_embedding = self.embedding_manager.embed_query(query)
            knowledge = self.search_by_embedding(query_embedding, top_k=top_k)
            logger.info(f"【KnowledgeRAG】检索 query='{query}' 返回 {len(knowledge)} 条结果")
            return knowledge
        except Exception as e:
            logger.error(f"【KnowledgeRAG】检索失败: {e}")
            return []

    def get_relevant_knowledge(
        self,
        query: str,
        threshold: float = 0.3,
        query_embedding: Optional[List[float]] = None,
    ) -> str:
        """获取相关知识文本（合并为可读格式）"""
        results = (
            self.search_by_embedding(query_embedding, top_k=3)
            if query_embedding is not None
            else self.search(query, top_k=3)
        )
        relevant = [r for r in results if r['similarity'] >= threshold]

        if not relevant:
            return ""

        lines = ["【相关业务知识】"]
        for item in relevant:
            lines.append(f"\n{item['category']}：{item['content']}")

        return "\n".join(lines)
