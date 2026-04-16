from langchain_classic.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage
from typing import Optional, Dict


class ConversationMemoryManager:
    """多会话对话记忆管理器"""

    def __init__(self, max_token_limit: int = 2000):
        self.max_token_limit = max_token_limit
        self._sessions: Dict[str, ConversationBufferMemory] = {}
        self._turn_counts: Dict[str, int] = {}  # 追踪对话轮次
        self._memory_rag = None  # 长期记忆模块

    def set_memory_rag(self, memory_rag):
        """注入长期记忆模块"""
        self._memory_rag = memory_rag

    def increment_turn(self, user_id: Optional[str] = None) -> int:
        """增加对话轮次计数"""
        key = user_id or "_default_"
        self._turn_counts[key] = self._turn_counts.get(key, 0) + 1
        return self._turn_counts[key]

    def get_turn_count(self, user_id: Optional[str] = None) -> int:
        """获取当前对话轮次"""
        key = user_id or "_default_"
        return self._turn_counts.get(key, 0)

    def reset_turn_count(self, user_id: Optional[str] = None) -> None:
        """重置对话轮次计数"""
        key = user_id or "_default_"
        self._turn_counts[key] = 0

    def _get_memory(self, user_id: Optional[str] = None) -> ConversationBufferMemory:
        """获取用户对应的 memory 实例"""
        key = user_id or "_default_"

        if key not in self._sessions:
            self._sessions[key] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="output",
                input_key="input",
                max_token_limit=self.max_token_limit
            )

        return self._sessions[key]

    def add_user_message(self, message: str, user_id: Optional[str] = None) -> None:
        """添加用户消息"""
        memory = self._get_memory(user_id)
        memory.chat_memory.add_user_message(HumanMessage(content=message))

    def add_ai_message(self, message: str, user_id: Optional[str] = None) -> None:
        """添加 AI 消息"""
        memory = self._get_memory(user_id)
        memory.chat_memory.add_ai_message(AIMessage(content=message))

    def get_history(self, user_id: Optional[str] = None) -> str:
        """获取指定用户的历史记录"""
        memory = self._get_memory(user_id)
        variables = memory.load_memory_variables({})
        messages = variables.get("chat_history", [])
        if not messages:
            return "无"
        return "\n".join([
            f"用户: {m.content if hasattr(m, 'content') else str(m)}"
            if isinstance(m, HumanMessage) else
            f"助手: {m.content if hasattr(m, 'content') else str(m)}"
            for m in messages
        ])

    def clear(self, user_id: Optional[str] = None) -> None:
        """清空指定用户或所有记忆"""
        if user_id:
            key = user_id
            if key in self._sessions:
                self._sessions[key].clear()
                del self._sessions[key]
        else:
            self._sessions.clear()

    def save_context(self, input_str: str, output_str: str, user_id: Optional[str] = None) -> None:
        """保存对话上下文"""
        memory = self._get_memory(user_id)
        memory.save_context(
            {"input": input_str},
            {"output": output_str}
        )

    def get_session_count(self) -> int:
        """获取当前会话数量"""
        return len(self._sessions)
