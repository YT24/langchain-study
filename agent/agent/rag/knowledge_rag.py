"""
Knowledge RAG - 业务知识库
"""
from typing import List, Dict
from .vector_store import VectorStore


class KnowledgeRAG:
    """业务知识检索"""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.collection_name = "knowledge"

    def init_default_knowledge(self):
        """初始化默认业务知识"""
        knowledge_base = [
            {
                "category": "订单状态",
                "question": "订单状态有哪些？有什么区别？",
                "answer": "订单状态包括：pending(待支付，等待买家付款)、paid(已支付，买家已付款等待发货)、shipped(已发货，商品已发出)、completed(已完成，交易成功)、cancelled(已取消，订单已取消)"
            },
            {
                "category": "会员等级",
                "question": "会员等级有哪些？有什么区别？",
                "answer": "会员等级包括：normal(普通会员)、silver(银卡会员，享受9.5折优惠)、gold(金卡会员，享受9折优惠)、vip(VIP会员，享受8.5折优惠和专属客服)"
            },
            {
                "category": "查询规则",
                "question": "如何查询订单？支持哪些过滤条件？",
                "answer": "查询订单支持以下过滤条件：1)用户ID 2)订单状态 3)金额范围(minAmount, maxAmount) 4)日期范围(startDate, endDate)。例如：查询U001金额大于500的已完成订单"
            },
            {
                "category": "统计功能",
                "question": "如何统计订单数据？",
                "answer": "统计功能可以计算：订单数量(count)、总金额(sum)、平均金额(avg)。支持按用户ID和金额范围进行统计。例如：统计U001的订单总金额"
            },
            {
                "category": "库存查询",
                "question": "如何查询库存？",
                "answer": "库存查询支持两种方式：1)按SKU查询，显示该商品在所有仓库的库存 2)按仓库查询，显示该仓库所有商品的库存"
            }
        ]

        texts = []
        metadatas = []
        ids = []

        for i, kb in enumerate(knowledge_base):
            text = f"""
类别：{kb['category']}
问题：{kb['question']}
答案：{kb['answer']}
"""
            texts.append(text.strip())
            metadatas.append({"category": kb["category"]})
            ids.append(f"knowledge_{i}")

        self.vector_store.add_texts(
            collection=self.collection_name,
            texts=texts,
            metadatas=metadatas,
            ids=ids
        )

    def add_knowledge(self, category: str, question: str, answer: str):
        """添加知识"""
        import uuid
        text = f"""
类别：{category}
问题：{question}
答案：{answer}
"""
        self.vector_store.add_texts(
            collection=self.collection_name,
            texts=[text.strip()],
            metadatas=[{"category": category}],
            ids=[f"knowledge_{uuid.uuid4().hex[:8]}"]
        )

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """检索相关知识"""
        results = self.vector_store.search(
            collection=self.collection_name,
            query=query,
            top_k=top_k
        )
        return results

    def build_knowledge_context(self, query: str, top_k: int = 3) -> str:
        """构建知识上下文"""
        results = self.retrieve(query, top_k)

        if not results:
            return ""

        lines = ["\n相关业务知识："]
        for r in results:
            lines.append(f"- {r['content']}")

        return "\n".join(lines)
