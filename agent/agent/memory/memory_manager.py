"""
Memory Manager - 记忆管理模块
实现短期记忆和长期记忆
"""
import json
import time
from typing import List, Dict, Any, Optional
from collections import deque
from ..rag.vector_store import VectorStore


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

    def __str__(self) -> str:
        return f"User: {self.user}\nAssistant: {self.assistant}"


class MemoryManager:
    """记忆管理器"""

    def __init__(self, vector_store: VectorStore, max_short_term: int = 10):
        self.vector_store = vector_store
        self.max_short_term = max_short_term
        self.short_term: deque = deque(maxlen=max_short_term)  # 短期记忆
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

        # 检查是否需要总结并存储长期记忆
        if len(self.short_term) >= self.max_short_term:
            self._summarize_and_store()

    def _summarize_and_store(self):
        """总结短期记忆并存储到长期记忆"""
        if not self.short_term:
            return

        # 提取关键信息
        facts = []
        for turn in self.short_term:
            facts.append(f"用户问：{turn.user}")
            facts.append(f"助手答：{turn.assistant}")
            if turn.tool_calls:
                for tc in turn.tool_calls:
                    facts.append(f"调用工具：{tc.get('tool')}.{tc.get('action')}")

        summary = "；".join(facts[-6:])  # 取最近的信息

        # 存储到向量库
        if self.user_id:
            self.vector_store.add_texts(
                collection="user_memory",
                texts=[f"用户{self.user_id}的对话记忆：{summary}"],
                metadatas=[{
                    "user_id": self.user_id,
                    "session_id": self.session_id,
                    "type": "conversation_summary"
                }]
            )

        # 清空短期记忆
        self.short_term.clear()

    def add_fact(self, content: str, memory_type: str = "fact"):
        """添加事实到长期记忆"""
        if not self.user_id:
            return

        self.vector_store.add_texts(
            collection="user_memory",
            texts=[content],
            metadatas=[{
                "user_id": self.user_id,
                "memory_type": memory_type,
                "session_id": self.session_id
            }]
        )

    def search_memory(self, query: str, top_k: int = 3) -> List[Dict]:
        """检索长期记忆"""
        if not self.user_id:
            return []

        # 检索用户相关的记忆
        results = self.vector_store.search(
            collection="user_memory",
            query=f"用户{self.user_id} {query}",
            top_k=top_k
        )

        # 过滤只返回该用户相关的记忆
        return [r for r in results if r["metadata"].get("user_id") == self.user_id]

    def get_recent_context(self, k: int = 5) -> str:
        """获取最近K轮对话"""
        recent = list(self.short_term)[-k:]
        if not recent:
            return ""

        lines = []
        for i, turn in enumerate(recent):
            lines.append(f"第{len(recent)-i}轮：用户：{turn.user}")
            if turn.tool_calls:
                for tc in turn.tool_calls:
                    lines.append(f"      工具：{tc.get('tool')}.{tc.get('action')}")
            lines.append(f"      助手：{turn.assistant}")

        return "\n".join(lines)

    def get_context(self, user_input: str) -> Dict[str, Any]:
        """获取完整上下文"""
        # 检索相关长期记忆
        relevant_memories = self.search_memory(user_input)

        # 获取短期记忆
        recent = self.get_recent_context(3)

        return {
            "relevant_memories": relevant_memories,
            "recent_conversation": recent,
            "short_term_count": len(self.short_term)
        }

    def build_memory_context(self, user_input: str) -> str:
        """构建记忆上下文"""
        context = self.get_context(user_input)

        parts = []

        # 添加相关记忆
        if context["relevant_memories"]:
            parts.append("\n用户相关记忆：")
            for mem in context["relevant_memories"][:2]:
                parts.append(f"- {mem['content']}")

        # 添加最近对话
        if context["recent_conversation"]:
            parts.append(f"\n最近对话：\n{context['recent_conversation']}")

        return "\n".join(parts) if parts else ""


class WorkingMemory:
    """工作记忆 - 当前任务状态"""

    def __init__(self):
        self.pending_params: Dict[str, Any] = {}  # 待填充参数
        self.current_tool: str = None
        self.current_action: str = None
        self.state: str = "init"  # init, waiting_param, executing, done

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
