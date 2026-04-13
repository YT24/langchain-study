"""
Memory Manager - 记忆管理模块（简化版）
实现短期记忆和对话历史
"""
import time
from typing import List, Dict, Any, Optional
from collections import deque


class Turn:
    """对话轮次"""

    def __init__(self, user: str, assistant: str, tool_calls: List[Dict] = None, timestamp: float = None):
        self.user = user
        self.assistant = assistant
        self.tool_calls = tool_calls or []
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> Dict:
        return {
            "user": self.user,
            "assistant": self.assistant,
            "tool_calls": self.tool_calls,
            "timestamp": self.timestamp
        }


class MemoryManager:
    """记忆管理器（简化版）"""

    def __init__(self, max_short_term: int = 20):
        self.max_short_term = max_short_term
        self.short_term: deque = deque(maxlen=max_short_term)
        self.session_id = None
        self.user_id = None

    def set_session(self, session_id: str, user_id: str = None):
        """设置会话"""
        self.session_id = session_id
        self.user_id = user_id

    def add_turn(self, user_msg: str, assistant_msg: str, tool_calls: List[Dict] = None):
        """添加一轮对话"""
        turn = Turn(user=user_msg, assistant=assistant_msg, tool_calls=tool_calls)
        self.short_term.append(turn)

    def get_recent_context(self, k: int = 5) -> str:
        """获取最近K轮对话"""
        recent = list(self.short_term)[-k:]
        if not recent:
            return ""

        lines = []
        for turn in recent:
            lines.append(f"用户：{turn.user}")
            if turn.tool_calls:
                for tc in turn.tool_calls:
                    lines.append(f"  工具：{tc.get('tool')}.{tc.get('action')}")
            lines.append(f"助手：{turn.assistant}")

        return "\n".join(lines)

    def get_context(self, user_input: str) -> Dict[str, Any]:
        """获取完整上下文"""
        return {
            "recent_conversation": self.get_recent_context(5),
            "short_term_count": len(self.short_term)
        }

    def build_memory_context(self, user_input: str) -> str:
        """构建记忆上下文"""
        context = self.get_context(user_input)
        if context["recent_conversation"]:
            return f"\n最近对话：\n{context['recent_conversation']}"
        return ""


class WorkingMemory:
    """工作记忆 - 当前任务状态"""

    def __init__(self):
        self.pending_params: Dict[str, Any] = {}
        self.current_tool: str = None
        self.current_action: str = None
        self.state: str = "init"

    def set_tool_call(self, tool: str, action: str, params: Dict):
        """设置工具调用"""
        self.current_tool = tool
        self.current_action = action
        self.pending_params = params.copy()
        self.state = "waiting_param"

    def update_param(self, key: str, value: Any):
        """更新参数"""
        if key in self.pending_params:
            self.pending_params[key] = value

    def is_complete(self) -> bool:
        """检查参数是否完整"""
        return all(v is not None for v in self.pending_params.values())

    def get_missing_params(self) -> List[str]:
        """获取缺失参数"""
        return [k for k, v in self.pending_params.items() if v is None]

    def clear(self):
        """清空工作记忆"""
        self.pending_params = {}
        self.current_tool = None
        self.current_action = None
        self.state = "init"
