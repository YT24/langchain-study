from langchain_core.tools import Tool
from typing import List


def create_query_chain(llm, tools: List[Tool], memory, tool_rag=None, knowledge_rag=None):
    """创建查询链 - 使用 LCEL + RAG 增强

    Args:
        llm: 语言模型
        tools: 可用工具列表
        memory: 对话记忆
        tool_rag: 工具向量检索（可选）
        knowledge_rag: 知识向量检索（可选）
    """
    from langchain_core.output_parsers.string import StrOutputParser
    from langchain_core.prompts import PromptTemplate
    from prompts import QUERY_TEMPLATE

    # 基础工具描述
    tool_descriptions = "\n".join([
        f"- {t.name}: {t.description}" for t in tools
    ])

    # 只 partial tool_descriptions，rag_context 动态传入
    prompt = PromptTemplate.from_template(QUERY_TEMPLATE).partial(
        tool_descriptions=tool_descriptions
    )

    # 使用 LCEL 构建 chain
    chain = (
        prompt
        | llm
        | StrOutputParser()
    )

    return chain
