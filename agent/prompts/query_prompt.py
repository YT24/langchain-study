from langchain.prompts import PromptTemplate

QUERY_TEMPLATE = """你是一个智能助手，可以调用工具来回答用户问题。

可用工具：
{tools}

注意：
- 只使用提供的工具
- 如果工具返回错误，说明原因并尝试其他方式
- 如果无法回答，说明原因

历史对话：
{chat_history}

当前用户：{input}
{agent_scratchpad}"""

def get_query_prompt() -> PromptTemplate:
    return PromptTemplate.from_template(QUERY_TEMPLATE)
