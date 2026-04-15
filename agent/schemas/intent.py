from pydantic import BaseModel, Field
from typing import Literal


class Intent(BaseModel):
    """意图识别结果"""
    intent: Literal["query", "statistic", "chat", "unknown"] = Field(
        description="用户意图：query=查询数据, statistic=统计汇总, chat=闲聊, unknown=无法理解"
    )
    reason: str = Field(description="判断理由")
