from langchain_core.tools import Tool
from typing import List


def create_query_chain(llm, tools: List[Tool], memory):
    """创建查询链 - 使用 LCEL（DeepSeek 不支持 bind_tools，改用 JSON 输出解析）"""
    from langchain_core.output_parsers.string import StrOutputParser
    from prompts.query_prompt import get_query_prompt

    # 构建工具描述
    tool_descriptions = "\n".join([
        f"- {t.name}: {t.description}" for t in tools
    ])

    prompt = get_query_prompt()

    # 使用 LCEL 构建 chain（不使用 bind_tools，改用 JSON 输出解析）
    chain = (
        prompt.partial(tool_descriptions=tool_descriptions)
        | llm
        | StrOutputParser()
    )

    return chain
