"""
Knowledge RAG - 业务知识管理（简化版）
"""
from typing import List, Dict


class KnowledgeRAG:
    """业务知识检索（简化版）"""

    DEFAULT_KNOWLEDGE = """
相关业务知识：
1. 订单状态包括：pending(待支付)、paid(已支付)、shipped(已发货)、completed(已完成)、cancelled(已取消)
2. 会员等级包括：normal(普通)、silver(银卡)、gold(金卡)、vip(VIP)
3. 查询订单支持按金额范围(minAmount, maxAmount)和日期范围(startDate, endDate)过滤
4. 统计功能可计算订单数量(count)、总金额(sum)、平均金额(avg)
5. 库存查询支持按SKU和按仓库两种方式
"""

    def __init__(self):
        self.knowledge = self.DEFAULT_KNOWLEDGE

    def add_knowledge(self, category: str, question: str, answer: str):
        """添加知识"""
        self.knowledge += f"\n{category}：{question} - {answer}"

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """检索相关知识"""
        return [{"content": self.knowledge, "metadata": {"category": "general"}}]

    def build_knowledge_context(self, query: str, top_k: int = 3) -> str:
        """构建知识上下文"""
        return self.knowledge


def init_knowledge_rag() -> KnowledgeRAG:
    """初始化知识库"""
    return KnowledgeRAG()
