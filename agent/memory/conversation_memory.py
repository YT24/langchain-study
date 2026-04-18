from typing import Dict, Optional

from langchain_core.messages import AIMessage, HumanMessage


class ConversationMemoryManager:
    """多会话对话记忆管理器"""

    def __init__(self, max_token_limit: int = 2000):
        self.max_token_limit = max_token_limit
        self._sessions: Dict[str, list] = {}
        self._turn_counts: Dict[str, int] = {}
        self._memory_rag = None

    @staticmethod
    def _session_key(user_id: Optional[str] = None) -> str:
        return user_id or "_default_"

    def _get_memory(self, user_id: Optional[str] = None) -> list:
        key = self._session_key(user_id)
        if key not in self._sessions:
            self._sessions[key] = []
        return self._sessions[key]

    def _truncate_messages(self, messages: list) -> list:
        if self.max_token_limit <= 0:
            return messages

        approx_limit = max(self.max_token_limit // 20, 1)
        if len(messages) <= approx_limit:
            return messages
        return messages[-approx_limit:]

    @staticmethod
    def _format_message(message) -> str:
        if isinstance(message, HumanMessage):
            return f"用户: {message.content if hasattr(message, 'content') else str(message)}"
        return f"助手: {message.content if hasattr(message, 'content') else str(message)}"

    def _append_message(self, user_id: Optional[str], message) -> None:
        key = self._session_key(user_id)
        messages = self._get_memory(user_id)
        messages.append(message)
        self._sessions[key] = self._truncate_messages(messages)

    def set_memory_rag(self, memory_rag):
        """注入长期记忆模块"""
        self._memory_rag = memory_rag

    def increment_turn(self, user_id: Optional[str] = None) -> int:
        """增加对话轮次计数"""
        key = self._session_key(user_id)
        self._turn_counts[key] = self._turn_counts.get(key, 0) + 1
        return self._turn_counts[key]

    def get_turn_count(self, user_id: Optional[str] = None) -> int:
        """获取当前对话轮次"""
        key = self._session_key(user_id)
        return self._turn_counts.get(key, 0)

    def reset_turn_count(self, user_id: Optional[str] = None) -> None:
        """重置对话轮次计数"""
        self._turn_counts[self._session_key(user_id)] = 0

    def add_user_message(self, message: str, user_id: Optional[str] = None) -> None:
        """添加用户消息"""
        self._append_message(user_id, HumanMessage(content=message))

    def add_ai_message(self, message: str, user_id: Optional[str] = None) -> None:
        """添加 AI 消息"""
        self._append_message(user_id, AIMessage(content=message))

    def get_history(self, user_id: Optional[str] = None) -> str:
        """获取指定用户的历史记录"""
        messages = self._get_memory(user_id)
        if not messages:
            return "无"
        return "\n".join(self._format_message(message) for message in messages)

    def trim_history(self, user_id: Optional[str] = None, keep_last_pairs: int = 2) -> None:
        """裁剪历史记录，仅保留最近若干轮对话"""
        key = self._session_key(user_id)
        messages = self._get_memory(user_id)
        keep_count = max(keep_last_pairs, 0) * 2
        if keep_count <= 0:
            self._sessions[key] = []
            return
        if len(messages) > keep_count:
            self._sessions[key] = messages[-keep_count:]

    def clear(self, user_id: Optional[str] = None) -> None:
        """清空指定用户或所有记忆"""
        if user_id:
            key = self._session_key(user_id)
            self._sessions.pop(key, None)
            self._turn_counts.pop(key, None)
            return

        self._sessions.clear()
        self._turn_counts.clear()

    def save_context(self, input_str: str, output_str: str, user_id: Optional[str] = None) -> None:
        """保存对话上下文"""
        self.add_user_message(input_str, user_id)
        self.add_ai_message(output_str, user_id)

    def get_session_count(self) -> int:
        """获取当前会话数量"""
        return len(self._sessions)

    def load_memory_variables(self, user_id: Optional[str] = None) -> Dict[str, list]:
        return {"chat_history": list(self._get_memory(user_id))}

    def clear_messages(self, user_id: Optional[str] = None) -> None:
        self._sessions[self._session_key(user_id)] = []
