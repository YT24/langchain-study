from langchain_core.output_parsers.string import StrOutputParser

from agent.prompts import get_chat_prompt


def create_chat_chain(llm):
    """创建闲聊链 - 使用 LCEL"""
    prompt = get_chat_prompt()
    chain = prompt | llm | StrOutputParser()
    return chain
