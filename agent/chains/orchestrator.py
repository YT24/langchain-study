from typing import Optional
import logging
import json
import re

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Agent 编排器 - 统一调度各 Chain"""

    def __init__(
        self,
        intent_chain,
        query_chain,
        chat_chain,
        memory_manager,
        llm=None
    ):
        self.intent_chain = intent_chain
        self.query_chain = query_chain
        self.chat_chain = chat_chain
        self.memory_manager = memory_manager
        self.llm = llm
        self._tools_map = {}  # 工具名到工具对象的映射
        self._tool_rag = None
        self._knowledge_rag = None

    def set_tools(self, tools):
        """设置可用工具（由 dependencies.py 调用）"""
        self._tools_map = {t.name: t for t in tools}
        logger.info(f"【工具注册】已注册 {len(self._tools_map)} 个工具: {list(self._tools_map.keys())}")
        for name, tool in self._tools_map.items():
            logger.info(f"【工具注册】  - {name}: {tool.description[:50] if hasattr(tool, 'description') else 'N/A'}...")

    def set_tool_rag(self, tool_rag):
        """设置工具 RAG"""
        self._tool_rag = tool_rag
        logger.info("【ToolRAG】已设置")

    def set_knowledge_rag(self, knowledge_rag):
        """设置知识 RAG"""
        self._knowledge_rag = knowledge_rag
        logger.info("【KnowledgeRAG】已设置")

    def _parse_llm_json(self, text: str) -> Optional[dict]:
        """解析 LLM 返回的 JSON"""
        try:
            text = text.strip()
            # 尝试提取 JSON 对象（支持嵌套）
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1 and end > start:
                json_str = text[start:end+1]
                return json.loads(json_str)
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"【JSON解析失败】{e}, 原始内容: {text[:200]}")
            return None

    def _find_tool(self, tool_name: str):
        """根据名称查找工具（支持大小写不敏感）"""
        # 直接匹配
        tool = self._tools_map.get(tool_name)
        if tool:
            return tool

        # 大小写不敏感匹配
        tool_name_lower = tool_name.lower().replace(" ", "_").replace("-", "_")
        for name, t in self._tools_map.items():
            if name.lower().replace(" ", "_").replace("-", "_") == tool_name_lower:
                return t

        # 包含匹配
        for name, t in self._tools_map.items():
            if tool_name_lower in name.lower().replace(" ", "_").replace("-", "_"):
                return t

        return None

    def _normalize_params(self, params: dict, tool) -> dict:
        """规范化参数名：user_id -> userId 等"""
        if not hasattr(tool, 'input_schema') or not tool.input_schema:
            return params

        normalized = {}
        # 获取工具 schema 中的字段名
        try:
            schema_fields = tool.input_schema.model_fields if hasattr(tool.input_schema, 'model_fields') else {}
            schema_field_names = set(schema_fields.keys())

            for key, value in params.items():
                # 尝试直接匹配
                if key in schema_field_names:
                    normalized[key] = value
                else:
                    # 尝试转换：user_id -> userId 或 userId -> user_id
                    alt1 = key.replace('_', '')
                    alt2 = ''.join('_' + c.lower() if c.isupper() else c for c in key)

                    for schema_key in schema_field_names:
                        if schema_key.lower().replace('_', '') == alt1.lower().replace('_', ''):
                            normalized[schema_key] = value
                            break
                    else:
                        # 没找到匹配，使用原参数名
                        normalized[key] = value
        except Exception as e:
            logger.warning(f"【参数规范化】失败: {e}，使用原始参数")
            normalized = params

        return normalized

    def _get_rag_context(self, query: str) -> str:
        """获取 RAG 上下文（相关工具 + 业务知识）"""
        from config import get_settings
        settings = get_settings()

        context_parts = []

        # 1. Tool RAG 检索
        if hasattr(self, '_tool_rag') and self._tool_rag:
            try:
                similar_tools = self._tool_rag.search(query, top_k=settings.rag_top_k_tools)
                if similar_tools:
                    tool_lines = ["【相关工具】（按相似度排序）："]
                    for t in similar_tools:
                        similarity = t.get('similarity', 0)
                        tool_lines.append(f"  - {t['tool_name']}: {t['description']} (匹配度: {similarity:.2f})")
                    context_parts.append("\n".join(tool_lines))
                    logger.info(f"【RAG检索】找到 {len(similar_tools)} 个相关工具")
            except Exception as e:
                logger.warning(f"【RAG检索】ToolRAG 失败: {e}")

        # 2. Knowledge RAG 检索
        if hasattr(self, '_knowledge_rag') and self._knowledge_rag:
            try:
                relevant_knowledge = self._knowledge_rag.get_relevant_knowledge(
                    query, threshold=settings.rag_similarity_threshold
                )
                if relevant_knowledge:
                    context_parts.append(relevant_knowledge)
                    logger.info("【RAG检索】找到相关业务知识")
            except Exception as e:
                logger.warning(f"【RAG检索】KnowledgeRAG 失败: {e}")

        if context_parts:
            return "\n\n".join(context_parts)
        return ""

    def _execute_tool(self, tool_name: str, params: dict) -> str:
        """执行工具"""
        logger.info(f"【工具执行】准备执行 {tool_name}，参数: {params}")

        tool = self._find_tool(tool_name)
        if not tool:
            available = list(self._tools_map.keys())
            return f"错误：未找到工具 '{tool_name}'，可用工具: {available}"

        # 规范化参数名
        params = self._normalize_params(params, tool)
        logger.info(f"【工具执行】规范化后参数: {params}")

        try:
            result = tool.invoke(params)
            logger.info(f"【工具执行】{tool_name} 执行成功")
            return result
        except Exception as e:
            logger.error(f"【工具执行】{tool_name} 执行失败: {e}")
            return f"工具执行失败: {str(e)}"

    def _polish_result(self, tool_result: str, user_question: str) -> str:
        """使用 LLM 润色工具返回结果"""
        from langchain_core.prompts import PromptTemplate
        from langchain_core.output_parsers.string import StrOutputParser

        template = """你是一个智能助手。用户问了以下问题：

问题：{question}

后端工具返回了原始数据：

{tool_result}

请将上述数据以清晰的 Markdown 格式返回给用户，包括：
1. 简要说明查询结果
2. 用表格或列表展示关键数据
3. 如有需要，添加简单总结

直接返回 Markdown 内容，不要额外解释："""

        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()

        try:
            polished = chain.invoke({
                "question": user_question,
                "tool_result": tool_result
            })
            logger.info("【结果润色】LLM 润色完成")
            return polished
        except Exception as e:
            logger.error(f"【结果润色】失败: {e}，返回原始结果")
            return tool_result

    def process(self, user_input: str, user_id: Optional[str] = None) -> str:
        """处理用户输入"""
        try:
            logger.info("=" * 50)
            logger.info(f"【开始处理】用户输入: {user_input[:100]}")

            # 1. 意图识别
            logger.info("【步骤1】开始意图识别...")
            intent_result = self.intent_chain.invoke({"user_input": user_input})
            logger.info(f"【步骤1】意图识别返回: {intent_result}, 类型: {type(intent_result)}")

            # 提取 Intent 对象
            intent_obj = intent_result if hasattr(intent_result, 'intent') else None

            if intent_obj:
                intent_type = intent_obj.intent
                logger.info(f"【意图识别】类型: {intent_type}, 原因: {intent_obj.reason}")
            else:
                # 降级处理：默认按查询处理
                intent_type = "query"
                logger.warning(f"【意图识别】降级处理，默认按 query 处理")

            # 2. 路由分发
            logger.info(f"【步骤2】开始路由分发，意图类型: {intent_type}")

            if intent_type in ("query", "statistic"):
                logger.info("【路由】进入查询/统计处理流程")
                logger.info(f"【历史记录】{self.memory_manager.get_history()[:200]}")

                # RAG 增强：检索相关工具和知识
                rag_context = self._get_rag_context(user_input)

                raw_response = self.query_chain.invoke({
                    "input": user_input,
                    "chat_history": self.memory_manager.get_history(),
                    "rag_context": rag_context
                })
                logger.info(f"【查询链返回】原始响应: {str(raw_response)[:300]}")

                # 解析 JSON
                parsed = self._parse_llm_json(raw_response)
                logger.info(f"【调试】parsed 内容: {parsed}, _tools_map 工具数: {len(self._tools_map)}")

                need_tool = parsed.get("need_tool") if parsed else None
                tool_name = parsed.get("tool") if parsed else None

                # 处理字符串 "true" 的情况
                if isinstance(need_tool, str):
                    need_tool = need_tool.lower() == "true"

                logger.info(f"【调试】need_tool={need_tool}, tool={tool_name}")

                if parsed and need_tool and tool_name:
                    params = parsed.get("params", {})
                    logger.info(f"【工具调用】{tool_name}，参数: {params}")
                    tool_result = self._execute_tool(tool_name, params)
                    # 润色结果
                    logger.info("【结果润色】开始润色工具返回结果...")
                    response = self._polish_result(tool_result, user_input)
                elif parsed and not need_tool:
                    response = parsed.get("answer", "无法理解您的问题")
                else:
                    # 降级：直接返回 LLM 输出
                    response = raw_response
                    logger.warning("【解析失败】降级为直接返回 LLM 输出")

            elif intent_type == "chat":
                logger.info("【路由】进入闲聊处理流程")
                response = self.chat_chain.invoke({
                    "input": user_input,
                    "chat_history": self.memory_manager.get_history()
                })
                logger.info(f"【闲聊链返回】类型: {type(response).__name__}, 内容: {str(response)[:200]}")
                if isinstance(response, dict):
                    response = response.get("text", str(response))
            else:
                logger.warning("【路由】无法识别意图，返回默认响应")
                response = "抱歉，我无法理解您的问题，请尝试重新描述。"

            # 3. 更新记忆
            logger.info("【步骤3】更新对话记忆")
            self.memory_manager.add_user_message(user_input)
            self.memory_manager.add_ai_message(str(response))
            logger.info(f"【最终响应】{str(response)[:100]}")

            return str(response)

        except Exception as e:
            logger.error(f"【处理失败】错误: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
