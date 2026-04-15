from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.tools import Tool
from typing import List
from prompts.query_prompt import get_query_prompt


def create_query_chain(llm, tools: List[Tool], memory):
    """创建 ReAct 查询链"""
    prompt = get_query_prompt()

    agent = create_react_agent(llm, tools, prompt)

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        max_iterations=5,
        early_stopping_method="generate",
        verbose=True
    )
    return executor
