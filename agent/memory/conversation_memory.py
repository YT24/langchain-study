from langchain_classic.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage
from typing import Optional


class ConversationMemoryManager:
    """对话记忆管理器"""

    def __init__(self, max_token_limit: int = 2000):
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output",
            input_key="input",
            max_token_limit=max_token_limit
        )

    def add_user_message(self, message: str) -> None:
        """添加用户消息"""
        self.memory.chat_memory.add_user_message(HumanMessage(content=message))

    def add_ai_message(self, message: str) -> None:
        """添加 AI 消息"""
        self.memory.chat_memory.add_ai_message(AIMessage(content=message))

    def get_history(self) -> str:
        """获取格式化后的历史记录"""
        variables = self.memory.load_memory_variables({})
        messages = variables.get("chat_history", [])
        if not messages:
            return "无"
        return "\n".join([
            f"用户: {m.content if hasattr(m, 'content') else str(m)}"
            if isinstance(m, HumanMessage) else
            f"助手: {m.content if hasattr(m, 'content') else str(m)}"
            for m in messages
        ])

    def clear(self) -> None:
        """清空记忆"""
        self.memory.clear()

    def save_context(self, input_str: str, output_str: str) -> None:
        """保存对话上下文"""
        self.memory.save_context(
            {"input": input_str},
            {"output": output_str}
        )
