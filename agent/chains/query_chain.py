from typing import List

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.tools import Tool

from agent.schemas.tool_decision import ToolDecision


def create_query_chain(llm, tools: List[Tool], tool_rag=None, knowledge_rag=None):
    """创建查询链 - 使用 LCEL + RAG 增强

    Args:
        llm: 语言模型
        tools: 可用工具列表
        tool_rag: 工具向量检索（可选）
        knowledge_rag: 知识向量检索（可选）
    """
    from langchain_core.prompts import PromptTemplate

    from agent.prompts import QUERY_TEMPLATE

    parser = JsonOutputParser(pydantic_object=ToolDecision)

    tool_descriptions = "\n".join([
        f"- {t.name}: {t.description}" for t in tools
    ])

    prompt = PromptTemplate.from_template(QUERY_TEMPLATE).partial(
        tool_descriptions=tool_descriptions,
        format_instructions=parser.get_format_instructions()
    )

    chain = prompt | llm | parser
    return chain
