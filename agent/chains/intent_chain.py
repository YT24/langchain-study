from agent.prompts import get_intent_prompt
from agent.schemas.intent import Intent


def create_intent_chain(llm):
    """创建意图识别链 - 使用 LCEL"""
    from langchain_core.output_parsers import JsonOutputParser

    parser = JsonOutputParser(pydantic_object=Intent)
    prompt = get_intent_prompt().partial(format_instructions=parser.get_format_instructions())

    chain = prompt | llm | parser
    return chain


def parse_intent_result(result) -> Intent:
    """解析意图识别结果"""
    if isinstance(result, dict):
        return Intent(**result)
    return result
