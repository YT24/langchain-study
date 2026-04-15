from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from langchain_core.outputs import Generation
from schemas.intent import Intent
from prompts.intent_prompt import get_intent_prompt
from typing import Union


def create_intent_chain(llm):
    """创建意图识别链"""
    parser = PydanticOutputParser(pydantic_object=Intent)
    prompt = get_intent_prompt().partial(format_instructions=parser.get_format_instructions())

    chain = LLMChain(llm=llm, prompt=prompt, output_parser=parser)
    return chain


def parse_intent_result(result: Union[str, Generation, dict]) -> Intent:
    """解析意图识别结果"""
    if isinstance(result, dict):
        return result.get("intent", result.get("text", None))
    elif isinstance(result, Generation):
        return parser.parse(result.text)
    else:
        return result
