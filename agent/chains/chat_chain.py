from langchain.chains import LLMChain
from prompts.chat_prompt import get_chat_prompt


def create_chat_chain(llm):
    """创建闲聊链"""
    prompt = get_chat_prompt()
    return LLMChain(llm=llm, prompt=prompt)
