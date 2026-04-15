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
from ..rag.tool_rag import init_tool_rag_from_backend
from ..rag.knowledge_rag import init_knowledge_rag
from ..memory.memory_manager import MemoryManager, WorkingMemory


class AgentCore:
    """Agent 核心引擎（简化版）"""

    def __init__(self, backend_url: str = "http://localhost:8080",
                 deepseek_api_key: str = None,
                 deepseek_base_url: str = "https://api.deepseek.com"):
        self.backend_url = backend_url
        self.api_key = deepseek_api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = deepseek_base_url

        # 初始化组件
        self.tool_rag = init_tool_rag_from_backend(backend_url)
        self.knowledge_rag = init_knowledge_rag()
        self.memory_manager = MemoryManager(max_short_term=20)
        self.router = Router(self.api_key, self.base_url)
        self.context_builder = ContextBuilder()
        self.tool_executor = SyncToolExecutor(backend_url)
        self.tool_executor.load_tools_from_backend()

        # 工作记忆
        self.working_memory = WorkingMemory()

        print("Agent 初始化完成")

    def chat(self, user_input: str, user_id: str = None, session_id: str = None) -> str:
        """
        处理用户对话
        """
        self.memory_manager.set_session(session_id or "default", user_id)

        print(f"\n========== 调试开始 ==========")
        print(f"【用户输入】 {user_input}")

        # 1. 意图识别
        intent, reason = self.router.classify(user_input)
        print(f"【意图识别】 {intent} ({reason})")

        # 2. 获取上下文
        context = self._build_context(user_input)

        # 3. 处理
        if intent == Intent.CHAT:
            response = self._handle_chat(user_input, context)
        elif intent == Intent.STATISTIC or intent == Intent.QUERY:
            response = self._handle_tool_call(user_input, context)
        else:
            response = "抱歉，我无法理解您的问题，请尝试重新描述。"

        print(f"【最终响应】 {response[:200]}...")
        print(f"========== 调试结束 ==========\n")

        # 4. 更新记忆
        self.memory_manager.add_turn(user_input, response)

        return response

    def _build_context(self, user_input: str) -> Dict:
        """构建上下文"""
        tools_desc = self.tool_rag.get_tool_description()
        knowledge = self.knowledge_rag.build_knowledge_context(user_input)
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
        prompt = self.context_builder.build_tool_call_prompt(user_input, context)
        print(f"【构建 Prompt】\n{prompt[:300]}...")

        try:
            llm_response = self._call_llm(prompt)
            print(f"【LLM 响应】 {llm_response[:200]}...")
        except Exception as e:
            return f"调用大模型失败：{str(e)}"

        # 解析工具调用
        tool_call = self._parse_tool_call(llm_response)
        print(f"【解析工具调用】 {tool_call}")

        if not tool_call:
            print(f"【工具调用】 未匹配到工具")
            return llm_response

        # 执行工具
        try:
            tool_result = self.tool_executor.execute([tool_call])
            print(f"【工具结果】 {tool_result[:200]}...")
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
        except:
            pass

        return None


class ReActAgent(AgentCore):
    """ReAct 模式的 Agent"""

    def _handle_tool_call(self, user_input: str, context: Dict) -> str:
        """ReAct 风格的工具调用"""
        max_iterations = 3
        current_input = user_input
        all_results = []

        available_tool_names = "/".join(self.tool_executor.tools.keys()) or "无"

        for i in range(max_iterations):
            prompt = f"""你是一个智能助手。当前任务：{current_input}

可用工具：
{context.get("tools", "无")}

历史工具结果：
{chr(10).join(all_results) if all_results else "无"}

请分析：
1. 当前已有什么信息？
2. 还需要什么信息？
3. 应该调用什么工具？

返回格式（JSON），直接返回JSON，不要包含其他文字：
{{"analysis": "你的分析", "tool": "{available_tool_names}之一，或null", "action": "具体action名称，或null", "params": {{"参数名": "参数值"}}或null}}

如果已有足够信息回答用户问题，analysis 中说明最终答案，tool 设为 null，action 设为 null。
"""

            try:
                llm_response = self._call_llm(prompt, temperature=0.3)
                print(f"【ReAct推理迭代 {i+1}】 {llm_response[:200]}...")
            except Exception as e:
                return f"推理失败：{str(e)}"

            parsed = self._parse_react_response(llm_response)
            if not parsed or not parsed.get("tool"):
                return parsed.get("analysis", llm_response) if parsed else llm_response

            tool_call = {
                "tool": parsed["tool"],
                "action": parsed["action"],
                "params": parsed.get("params", {})
            }

            try:
                result = self.tool_executor.execute([tool_call])
                print(f"【工具结果】 {result[:500]}...")

                # LLM 润色结果
                response_prompt = self.context_builder.build_response_prompt(
                    user_input, result, context
                )
                print(f"【润色 Prompt】\n{response_prompt[:300]}...")
                polished = self._call_llm(response_prompt)
                return polished
            except Exception as e:
                return f"工具执行失败：{str(e)}"

        return "抱歉，经过多次尝试仍无法完成您的请求。"

    def _parse_react_response(self, response: str) -> Optional[Dict]:
        """解析 ReAct 响应"""
        try:
            # 尝试找 JSON 对象（支持跨行）
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end > start:
                json_str = response[start:end+1]
                parsed = json.loads(json_str)
                if "tool" in parsed and "action" in parsed:
                    return parsed
        except:
            pass
        return None
