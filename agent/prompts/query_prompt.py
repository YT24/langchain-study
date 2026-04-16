from langchain_core.prompts import PromptTemplate

QUERY_TEMPLATE = """你是一个智能助手。

历史：{chat_history}

用户：{input}

{rag_context}

可用工具：
{tool_descriptions}

规则：查询订单/用户/库存用工具，其他直接回答。参考【相关工具】中的匹配结果。

只返回JSON：
{{"need_tool": true/false, "tool": "工具名", "params": {{"参数名": "值"}}, "answer": "直接回答"}}

只返回JSON："""

def get_query_prompt() -> PromptTemplate:
    return PromptTemplate.from_template(QUERY_TEMPLATE)
