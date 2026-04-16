from langchain_core.prompts import PromptTemplate
from config.loader import get

# 意图识别
INTENT_TEMPLATE = get("prompts.yml", "intent", "template")

# 查询链
QUERY_TEMPLATE = get("prompts.yml", "query", "template")

# 闲聊
CHAT_TEMPLATE = get("prompts.yml", "chat", "template")

# 结果润色
POLISH_TEMPLATE = get("prompts.yml", "polish", "template")


def get_intent_prompt() -> PromptTemplate:
    return PromptTemplate.from_template(INTENT_TEMPLATE)


def get_query_prompt() -> PromptTemplate:
    return PromptTemplate.from_template(QUERY_TEMPLATE)


def get_chat_prompt() -> PromptTemplate:
    return PromptTemplate.from_template(CHAT_TEMPLATE)


def get_polish_prompt() -> PromptTemplate:
    return PromptTemplate.from_template(POLISH_TEMPLATE)
