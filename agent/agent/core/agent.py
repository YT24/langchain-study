"""
Agent Core - Agent 核心引擎
"""
import json
import os
import requests
from typing import Dict, Optional, Tuple
from .router import Router, Intent
from .context_builder import ContextBuilder
from .tool_executor import SyncToolExecutor
from ..rag.vector_store import VectorStore
from ..rag.tool_rag import ToolRAG, init_tool_rag_from_backend
from ..rag.knowledge_rag import KnowledgeRAG
from ..memory.memory_manager import MemoryManager, WorkingMemory


class AgentCore:
    """Agent 核心引擎"""

    def __init__(self,
                 backend_url: str = "http://localhost:8080",
                 vector_store_dir: str = "./vector_store",
                 deepseek_api_key: str = None,
                 deepseek_base_url: str = "https://api.deepseek.com"):
        self.backend_url = backend_url
        self.api_key = deepseek_api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = deepseek_base_url

        # 初始化组件
        self.vector_store = VectorStore(persist_directory=vector_store_dir)
        self.tool_rag = init_tool_rag_from_backend(self.vector_store, backend_url)
        self.knowledge_rag = KnowledgeRAG(self.vector_store)
        self.memory_manager = MemoryManager(self.vector_store, max_short_term=10)
        self.router = Router(self.api_key, self.base_url)
        self.context_builder = ContextBuilder()
        self.tool_executor = SyncToolExecutor(backend_url)
        self.tool_executor.register_default_tools()

        # 工作记忆
        self.working_memory = WorkingMemory()

        # 初始化知识库
        self._init_knowledge()

    def _init_knowledge(self):
        """初始化知识库"""
        try:
            self.knowledge_rag.init_default_knowledge()
            print("知识库初始化完成")
        except Exception as e:
            print(f"知识库初始化失败: {e}")

    def chat(self, user_input: str, user_id: str = None, session_id: str = None) -> str:
        """
        处理用户对话

        Args:
            user_input: 用户输入
            user_id: 用户ID
            session_id: 会话ID

        Returns:
            Agent 响应
        """
        # 设置会话
        self.memory_manager.set_session(session_id or "default", user_id)

        print(f"\n========== DEBUG START ==========")
        print(f"[INPUT] {user_input}")

        # 1. 意图识别
        intent, reason = self.router.classify(user_input)
        print(f"[INTENT] {intent} ({reason})")

        # 2. 获取上下文
        context = self._build_context(user_input)

        # 3. 根据意图处理
        if intent == Intent.CHAT:
            response = self._handle_chat(user_input, context)
        elif intent == Intent.STATISTIC or intent == Intent.QUERY:
            response = self._handle_tool_call(user_input, context)
        else:
            response = "抱歉，我无法理解您的问题，请尝试重新描述。"

        print(f"[RESPONSE] {response[:200]}...")
        print(f"========== DEBUG END ==========\n")

        # 4. 更新记忆
        self.memory_manager.add_turn(user_input, response)

        return response

    def _build_context(self, user_input: str) -> Dict:
        """构建上下文"""
        # RAG 检索
        tools_desc = self.tool_rag.build_tool_description_from_rag(user_input, top_k=5)
        knowledge = self.knowledge_rag.build_knowledge_context(user_input, top_k=3)
        memory = self.memory_manager.build_memory_context(user_input)
        history = self.memory_manager.get_recent_context(3)

        return {
            "tools": tools_desc,
            "knowledge": knowledge,
            "memory": memory,
            "history": history
        }

    def _handle_chat(self, user_input: str, context: Dict) -> str:
        """处理闲聊"""
        prompt = self.context_builder.build(user_input, context)

        try:
            response = self._call_llm(prompt)
            return response
        except Exception as e:
            return f"抱歉，发生了错误：{str(e)}"

    def _handle_tool_call(self, user_input: str, context: Dict) -> str:
        """处理工具调用"""
        # 构建工具调用 prompt
        prompt = self.context_builder.build_tool_call_prompt(user_input, context)
        print(f"[TOOL_CALL_PROMPT]\n{prompt[:300]}...")

        # 调用 LLM 获取工具调用
        try:
            llm_response = self._call_llm(prompt)
            print(f"[LLM_RESPONSE] {llm_response[:200]}...")
        except Exception as e:
            return f"调用大模型失败：{str(e)}"

        # 解析工具调用
        tool_call = self._parse_tool_call(llm_response)
        print(f"[PARSED_TOOL_CALL] {tool_call}")

        if not tool_call:
            # LLM 返回的不是工具调用，当作普通回复
            return llm_response

        # 执行工具
        try:
            tool_result = self.tool_executor.execute([tool_call])
            print(f"[TOOL_RESULT] {tool_result[:200]}...")
        except Exception as e:
            return f"工具执行失败：{str(e)}"

        # 生成最终响应
        response_prompt = self.context_builder.build_response_prompt(
            user_input, tool_result, context
        )

        try:
            final_response = self._call_llm(response_prompt)
            return final_response
        except Exception as e:
            return f"生成响应失败：{str(e)}\n\n工具返回：{tool_result}"

    def _call_llm(self, prompt: str, temperature: float = 0.7) -> str:
        """调用 DeepSeek LLM"""
        if not self.api_key:
            return "错误：未设置 DEEPSEEK_API_KEY 环境变量"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature
        }
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]

    def _parse_tool_call(self, llm_response: str) -> Optional[Dict]:
        """解析 LLM 返回的工具调用"""
        try:
            for line in llm_response.split('\n'):
                line = line.strip()
                if line.startswith('{') and line.endswith('}'):
                    parsed = json.loads(line)
                    if "tool" in parsed and "action" in parsed:
                        return {
                            "tool": parsed["tool"],
                            "action": parsed["action"],
                            "params": parsed.get("params", {})
                        }

            # 尝试从整个响应中提取
            start = llm_response.find('{')
            end = llm_response.rfind('}') + 1
            if start != -1 and end > start:
                parsed = json.loads(llm_response[start:end])
                if "tool" in parsed and "action" in parsed:
                    return {
                        "tool": parsed["tool"],
                        "action": parsed["action"],
                        "params": parsed.get("params", {})
                    }
        except (json.JSONDecodeError, Exception):
            pass

        return None


class ReActAgent(AgentCore):
    """ReAct 模式的 Agent - 推理 + 行动"""

    def _handle_tool_call(self, user_input: str, context: Dict) -> str:
        """ReAct 风格的工具调用"""
        max_iterations = 3
        current_input = user_input
        all_results = []

        for i in range(max_iterations):
            # 构建推理 prompt
            prompt = f"""你是一个智能助手。当前任务：{current_input}

历史工具结果：
{chr(10).join(all_results) if all_results else "无"}

请分析：
1. 当前已有什么信息？
2. 还需要什么信息？
3. 应该调用什么工具？

返回格式（JSON）：
{{"analysis": "分析", "tool": "工具名或null", "action": "action名或null", "params": {{}}或null}}

如果已有足够信息回答用户问题，analysis 中说明最终答案，tool 设为 null。
"""

            try:
                llm_response = self._call_llm(prompt, temperature=0.3)
                print(f"[REACT_ITER_{i+1}] {llm_response[:200]}...")
            except Exception as e:
                return f"推理失败：{str(e)}"

            # 解析响应
            parsed = self._parse_react_response(llm_response)
            if not parsed or not parsed.get("tool"):
                # 已有足够信息
                return parsed.get("analysis", llm_response) if parsed else llm_response

            # 执行工具
            tool_call = {
                "tool": parsed["tool"],
                "action": parsed["action"],
                "params": parsed.get("params", {})
            }

            try:
                result = self.tool_executor.execute([tool_call])
                all_results.append(f"[{parsed['tool']}.{parsed['action']}] {result}")
                current_input = f"基于之前的工具结果，继续完成：{user_input}"
            except Exception as e:
                return f"工具执行失败：{str(e)}"

        return "抱歉，经过多次尝试仍无法完成您的请求。"

    def _parse_react_response(self, response: str) -> Optional[Dict]:
        """解析 ReAct 响应"""
        try:
            for line in response.split('\n'):
                line = line.strip()
                if line.startswith('{') and line.endswith('}'):
                    return json.loads(line)
        except:
            pass
        return None
