from langchain.prompts import PromptTemplate

INTENT_TEMPLATE = """你是一个意图分类器。用户输入后，判断用户的意图：

可选意图：
- query: 需要查询具体数据（订单、用户、库存）
- statistic: 需要统计汇总（金额、数量、平均值）
- chat: 一般对话、问候、闲聊
- unknown: 完全无法理解

用户输入：{user_input}

{format_instructions}

返回格式（只返回JSON，不要其他内容）：
{{"intent": "query|statistic|chat|unknown", "reason": "简短判断理由"}}
"""

def get_intent_prompt() -> PromptTemplate:
    return PromptTemplate.from_template(INTENT_TEMPLATE)
