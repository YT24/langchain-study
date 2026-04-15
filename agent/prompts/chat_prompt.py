from langchain_core.prompts import PromptTemplate

CHAT_TEMPLATE = """你是一个小助手，友善地回答用户问题。

历史对话：
{chat_history}

当前用户：{input}
助手："""

def get_chat_prompt() -> PromptTemplate:
    return PromptTemplate.from_template(CHAT_TEMPLATE)
