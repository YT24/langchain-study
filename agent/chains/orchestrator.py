import json
import logging
from typing import Optional, Dict, List, Any

from agent.chains.renderers import render_tool_result
from agent.chains.validators import normalize_tool_params, validate_required_params
from agent.schemas.tool_decision import ToolDecision

logger = logging.getLogger(__name__)


GREETING_TOKENS = ("你好", "hello", "hi")
SAFE_LOG_LENGTH = 120


def redact_for_log(value: Any, max_length: int = SAFE_LOG_LENGTH) -> str:
    text = str(value)
    replacements = {
        "userId=": "userId=***",
        "user_id=": "user_id=***",
        "orderNo=": "orderNo=***",
        "order_no=": "order_no=***",
    }
    for target, replacement in replacements.items():
        if target in text:
            start = text.index(target) + len(target)
            end = start
            while end < len(text) and not text[end].isspace() and text[end] not in ',;':
                end += 1
            text = text[:text.index(target)] + replacement + text[end:]
    return text[:max_length] + "..." if len(text) > max_length else text


def summarize_for_log(value: Any, max_length: int = SAFE_LOG_LENGTH) -> str:
    return redact_for_log(value, max_length=max_length)


def is_greeting(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in GREETING_TOKENS)


def should_fallback_to_chat(text: str) -> bool:
    return is_greeting(text)


def resolve_intent_type(intent_result, user_input: str) -> str:
    if isinstance(intent_result, dict):
        intent = intent_result.get("intent")
        reason = intent_result.get("reason", "")
        if intent:
            logger.info(f"【意图识别】类型: {intent}, 原因: {reason}")
            return intent

    intent_obj = intent_result if hasattr(intent_result, 'intent') else None
    if intent_obj:
        logger.info(f"【意图识别】类型: {intent_obj.intent}, 原因: {intent_obj.reason}")
        return intent_obj.intent

    fallback_intent = "chat" if should_fallback_to_chat(user_input) else "unknown"
    logger.warning(f"【意图识别】解析失败，使用兜底分类: {fallback_intent}")
    return fallback_intent


def coerce_tool_decision(raw_response) -> Optional[ToolDecision]:
    if isinstance(raw_response, ToolDecision):
        return raw_response
    if isinstance(raw_response, dict):
        payload = raw_response
    else:
        if not isinstance(raw_response, str):
            raw_response = str(raw_response)
        text = raw_response.strip()
        start = text.find('{')
        end = text.rfind('}')
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            payload = json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            return None
    try:
        return ToolDecision.model_validate(payload)
    except Exception as e:
        logger.warning(f"【决策解析】结构化校验失败: {e}")
        return None


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
        self._memory_rag = None  # 长期记忆 RAG
        self._query_cache: Dict[str, Any] = {}  # 请求级缓存
        self._query_embedding_cache: Dict[str, List[float]] = {}

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

    def set_memory_rag(self, memory_rag):
        """设置长期记忆 RAG"""
        self._memory_rag = memory_rag
        logger.info("【MemoryRAG】已设置")

    def _keyword_search_tools(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """关键词匹配降级搜索

        当 ChromaDB 不可用时，使用关键词匹配找到相关工具
        """
        query_lower = query.lower()
        query_words = set(query_lower.replace("_", " ").split())

        scored_tools = []
        for name, tool in self._tools_map.items():
            desc_lower = tool.description.lower().replace("_", " ") if tool.description else ""

            # 计算关键词匹配分数
            matches = 0
            for word in query_words:
                if word in name.lower() or word in desc_lower:
                    matches += 1

            if matches > 0:
                # 部分匹配
                score = matches / len(query_words)
                scored_tools.append({
                    "tool_name": name,
                    "description": tool.description if tool.description else "",
                    "similarity": score,
                    "is_keyword_match": True
                })

        # 按分数排序
        scored_tools.sort(key=lambda x: x["similarity"], reverse=True)
        return scored_tools[:top_k]

    def _get_query_embedding(self, query: str) -> Optional[List[float]]:
        if query in self._query_embedding_cache:
            return self._query_embedding_cache[query]

        embedding_manager = None
        if self._tool_rag and hasattr(self._tool_rag, "embedding_manager"):
            embedding_manager = self._tool_rag.embedding_manager
        elif self._knowledge_rag and hasattr(self._knowledge_rag, "embedding_manager"):
            embedding_manager = self._knowledge_rag.embedding_manager
        elif self._memory_rag and hasattr(self._memory_rag, "embedding_manager"):
            embedding_manager = self._memory_rag.embedding_manager

        if not embedding_manager:
            return None

        try:
            query_embedding = embedding_manager.embed_query(query)
            self._query_embedding_cache[query] = query_embedding
            return query_embedding
        except Exception as e:
            logger.warning(f"【RAG检索】query embedding 计算失败: {e}")
            return None

    def _search_all_rag(self, query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """合并 RAG 检索（工具 + 知识）

        使用请求级缓存避免重复计算；长期记忆仍在 _get_rag_context 中单独处理。
        """
        cache_key = f"{user_id or '_'}:{query}"
        if cache_key in self._query_cache:
            logger.info("【RAG检索】使用缓存结果")
            return self._query_cache[cache_key]

        from agent.settings import get_settings
        settings = get_settings()

        result = {
            "tools": [],
            "knowledge": "",
            "error": None
        }
        query_embedding = self._get_query_embedding(query)

        if hasattr(self, '_tool_rag') and self._tool_rag:
            try:
                if query_embedding is not None and hasattr(self._tool_rag, "search_by_embedding"):
                    tools = self._tool_rag.search_by_embedding(query_embedding, top_k=settings.rag_top_k_tools)
                else:
                    tools = self._tool_rag.search(query, top_k=settings.rag_top_k_tools)
                if tools:
                    result["tools"] = tools
                    logger.info(f"【RAG检索】向量检索找到 {len(tools)} 个工具")
                else:
                    logger.warning("【RAG检索】向量检索无结果，降级到关键词匹配")
                    result["tools"] = self._keyword_search_tools(query, settings.rag_top_k_tools)
            except Exception as e:
                logger.warning(f"【RAG检索】向量检索失败: {e}，降级到关键词匹配")
                result["tools"] = self._keyword_search_tools(query, settings.rag_top_k_tools)
                result["error"] = str(e)

        if hasattr(self, '_knowledge_rag') and self._knowledge_rag:
            try:
                knowledge = self._knowledge_rag.get_relevant_knowledge(
                    query,
                    threshold=settings.rag_similarity_threshold,
                    query_embedding=query_embedding,
                )
                if knowledge:
                    result["knowledge"] = knowledge
                    logger.info("【RAG检索】找到相关业务知识")
            except Exception as e:
                logger.warning(f"【RAG检索】KnowledgeRAG 失败: {e}")

        self._query_cache[cache_key] = result
        return result

    def _get_rag_context(self, query: str, user_id: Optional[str] = None) -> str:
        """获取 RAG 上下文（相关工具 + 业务知识 + 长期记忆）"""
        from agent.settings import get_settings
        settings = get_settings()

        context_parts = []

        # 使用合并检索
        rag_result = self._search_all_rag(query, user_id)

        # 1. 构建工具上下文
        if rag_result["tools"]:
            tool_lines = ["【相关工具】（按相似度排序）："]
            for t in rag_result["tools"]:
                similarity = t.get('similarity', 0)
                match_type = "(关键词)" if t.get('is_keyword_match') else ""
                tool_lines.append(f"  - {t['tool_name']}: {t['description']} {match_type}(匹配度: {similarity:.2f})")
            context_parts.append("\n".join(tool_lines))

        # 2. 构建知识上下文
        if rag_result["knowledge"]:
            context_parts.append(rag_result["knowledge"])

        # 3. 长期记忆检索
        if self._memory_rag and user_id:
            try:
                query_embedding = self._get_query_embedding(query)
                if query_embedding is not None and hasattr(self._memory_rag, "search_by_embedding"):
                    memories = self._memory_rag.search_by_embedding(
                        query_embedding,
                        user_id,
                        top_k=settings.memory_rag_top_k,
                    )
                else:
                    memories = self._memory_rag.search(query, user_id, top_k=settings.memory_rag_top_k)
                if memories:
                    # 按相似度阈值过滤
                    threshold = settings.memory_similarity_threshold
                    filtered_memories = [m for m in memories if m.get('similarity', 0) >= threshold]
                    if filtered_memories:
                        memory_lines = ["【相关历史记忆】："]
                        for m in filtered_memories:
                            similarity = m.get('similarity', 0)
                            memory_lines.append(
                                f"  - 记忆({similarity:.2f}): {m.get('summary', '')} "
                                f"[实体: {m.get('key_entities', '')} | 主题: {m.get('topics', '')}]"
                            )
                        context_parts.append("\n".join(memory_lines))
                        logger.info(f"【MemoryRAG】检索到 {len(filtered_memories)} 条相关记忆（阈值: {threshold}）")
            except Exception as e:
                logger.warning(f"【MemoryRAG】检索失败: {e}")

        if context_parts:
            return "\n\n".join(context_parts)
        return ""

    def _generate_memory_summary(self, chat_history: str, conversation_turns: int) -> Optional[Dict[str, Any]]:
        """使用 LLM 生成对话摘要

        Args:
            chat_history: 对话历史
            conversation_turns: 对话轮次数

        Returns:
            摘要信息 dict 或 None
        """
        if not self.llm or not chat_history or chat_history == "无":
            return None

        from langchain_core.prompts import PromptTemplate
        from langchain_core.output_parsers.string import StrOutputParser

        template = """你是一个对话摘要助手。请分析以下对话历史，生成结构化摘要。

对话历史：
{chat_history}

请以 JSON 格式返回摘要，包含以下字段：
{{
    "summary": "对话的主要内容摘要（1-2句话）",
    "key_entities": ["关键实体1", "关键实体2"],  // 用户提到的具体事物、人名、数字等
    "topics": ["主题1", "主题2"]  // 对话涉及的主题领域
}}

直接返回 JSON，不要有其他内容："""

        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()

        try:
            result = chain.invoke({"chat_history": chat_history})
            logger.info(f"【摘要生成】LLM 返回: {result[:200]}")

            # 解析 JSON 并验证必需字段
            summary_data = self._parse_llm_json(result)
            if summary_data and all(k in summary_data for k in ["summary", "key_entities", "topics"]):
                summary_data["conversation_turns"] = conversation_turns
                # 确保 key_entities 和 topics 是列表
                if isinstance(summary_data["key_entities"], str):
                    summary_data["key_entities"] = [summary_data["key_entities"]]
                if isinstance(summary_data["topics"], str):
                    summary_data["topics"] = [summary_data["topics"]]
                return summary_data
            logger.warning(f"【摘要生成】LLM 返回格式异常: {result[:100]}")
            return None

        except Exception as e:
            logger.error(f"【摘要生成】失败: {e}")
            return None

    def _parse_llm_json(self, text: str) -> Optional[dict]:
        """解析 LLM 返回的 JSON"""
        try:
            text = text.strip()
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
        """根据名称查找工具（使用缓存 RAG + 关键词降级）"""
        from agent.settings import get_settings
        settings = get_settings()

        # 1. 直接匹配
        tool = self._tools_map.get(tool_name)
        if tool:
            logger.info(f"【工具查找】直接匹配: {tool_name}")
            return tool

        # 2. 尝试从缓存的 RAG 结果中查找
        cached_tools = None
        for query, cached in self._query_cache.items():
            if cached.get("tools"):
                for t in cached["tools"]:
                    if t.get("tool_name") == tool_name:
                        similarity = t.get("similarity", 0)
                        if similarity >= settings.tool_match_threshold:
                            matched = self._tools_map.get(tool_name)
                            if matched:
                                logger.info(f"【工具查找】缓存命中: {tool_name} (相似度: {similarity:.3f})")
                                return matched

        # 3. RAG 语义匹配
        if hasattr(self, '_tool_rag') and self._tool_rag:
            try:
                results = self._tool_rag.search(tool_name, top_k=1)
                if results:
                    best_match = results[0]
                    similarity = best_match.get('similarity', 0)
                    matched_name = best_match.get('tool_name')

                    logger.info(f"【工具查找】RAG匹配: {tool_name} → {matched_name} (相似度: {similarity:.3f})")

                    if similarity >= settings.tool_match_threshold:
                        matched_tool = self._tools_map.get(matched_name)
                        if matched_tool:
                            return matched_tool
                    else:
                        logger.warning(f"【工具查找】RAG匹配相似度太低: {similarity:.3f} < {settings.tool_match_threshold}")
            except Exception as e:
                logger.warning(f"【工具查找】RAG匹配失败: {e}")

        # 4. 关键词降级匹配
        logger.info(f"【工具查找】尝试关键词匹配: {tool_name}")
        keyword_results = self._keyword_search_tools(tool_name, top_k=1)
        if keyword_results:
            best = keyword_results[0]
            if best['similarity'] >= settings.tool_match_threshold * 0.8:  # 关键词阈值放宽
                matched = self._tools_map.get(best['tool_name'])
                if matched:
                    logger.info(f"【工具查找】关键词匹配: {tool_name} → {best['tool_name']} (分数: {best['similarity']:.3f})")
                    return matched

        logger.error(f"【工具查找】未找到工具: {tool_name}")
        return None

    def _normalize_params(self, params: dict, tool) -> dict:
        """规范化参数名：user_id -> userId 等"""
        if not hasattr(tool, 'input_schema') or not tool.input_schema:
            return params

        normalized = {}
        try:
            schema_fields = tool.input_schema.model_fields if hasattr(tool.input_schema, 'model_fields') else {}
            schema_field_names = set(schema_fields.keys())

            for key, value in params.items():
                if key in schema_field_names:
                    normalized[key] = value
                else:
                    alt1 = key.replace('_', '')
                    for schema_key in schema_field_names:
                        if schema_key.lower().replace('_', '') == alt1.lower().replace('_', ''):
                            normalized[schema_key] = value
                            break
                    else:
                        normalized[key] = value
        except Exception as e:
            logger.warning(f"【参数规范化】失败: {e}，使用原始参数")
            normalized = params

        return normalized

    def _execute_tool(self, tool_name: str, params: dict) -> str:
        """执行工具（带详细日志）"""
        logger.info("=" * 60)
        logger.info(f"【工具调用】>>> 开始调用工具: {tool_name}")
        logger.info(f"【工具调用】    请求参数: {summarize_for_log(params)}")

        tool = self._find_tool(tool_name)
        if not tool:
            available = list(self._tools_map.keys())
            logger.error(f"【工具调用】!!! 工具未找到: {tool_name}")
            return f"错误：未找到工具 '{tool_name}'，可用工具: {available}"

        params = normalize_tool_params(params, tool)
        missing = validate_required_params(params, tool)
        if missing:
            logger.warning(f"【工具调用】缺少必要参数: {missing}")
            return f"缺少必要参数: {', '.join(missing)}"

        logger.info(f"【工具调用】    规范化参数: {summarize_for_log(params)}")

        try:
            logger.info(f"【工具调用】    正在执行...")
            result = tool.invoke(params)
            result_preview = summarize_for_log(result, max_length=SAFE_LOG_LENGTH)
            logger.info(f"【工具调用】<<< 工具执行成功")
            logger.info(f"【工具调用】    返回结果: {result_preview}")
            logger.info("=" * 60)
            return result
        except Exception as e:
            logger.error(f"【工具调用】!!! 工具执行异常: {e}")
            logger.info("=" * 60)
            return f"工具执行失败: {str(e)}"

    def _polish_result(self, tool_result: str, user_question: str) -> str:
        """使用 LLM 润色工具返回结果"""
        from langchain_core.prompts import PromptTemplate
        from langchain_core.output_parsers.string import StrOutputParser

        template = """后端已返回以下查询结果：

{tool_result}

请用 1 句话简要说明查询到了什么（条数、关键摘要）。
直接返回这段话，不要重复表格内容，不要额外解释。"""

        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()

        try:
            polished = chain.invoke({
                "question": user_question,
                "tool_result": tool_result
            })
            logger.info("【结果润色】LLM 润色完成")
            return f"{polished}\n\n{tool_result}"
        except Exception as e:
            logger.error(f"【结果润色】失败: {e}，返回原始结果")
            return tool_result

    def process(self, user_input: str, user_id: Optional[str] = None) -> str:
        """处理用户输入"""
        try:
            logger.info("=" * 50)
            logger.info(f"【开始处理】用户输入: {summarize_for_log(user_input)}")

            # 清理请求级缓存
            self._query_cache.clear()
            self._query_embedding_cache.clear()

            # 1. 意图识别
            logger.info("【步骤1】开始意图识别...")
            intent_result = self.intent_chain.invoke({"user_input": user_input})
            logger.info(f"【步骤1】意图识别返回: {intent_result}, 类型: {type(intent_result)}")

            intent_type = resolve_intent_type(intent_result, user_input)

            # 2. 路由分发
            logger.info(f"【步骤2】开始路由分发，意图类型: {intent_type}")

            if intent_type in ("query", "statistic"):
                logger.info("【路由】进入查询/统计处理流程")
                logger.info(f"【历史记录】{summarize_for_log(self.memory_manager.get_history(user_id))}")

                # RAG 增强（使用缓存避免重复 embedding）
                rag_context = self._get_rag_context(user_input, user_id)

                raw_response = self.query_chain.invoke({
                    "input": user_input,
                    "chat_history": self.memory_manager.get_history(user_id),
                    "rag_context": rag_context
                })
                logger.info(f"【查询链返回】原始响应: {summarize_for_log(raw_response)}")

                decision = coerce_tool_decision(raw_response)
                logger.info(f"【调试】decision 内容: {decision}, _tools_map 工具数: {len(self._tools_map)}")

                need_tool = decision.need_tool if decision else None
                tool_name = decision.tool if decision else None

                logger.info(f"【调试】need_tool={need_tool}, tool={tool_name}")

                if decision and need_tool and tool_name:
                    params = decision.params
                    logger.info(f"【工具调用】{tool_name}，参数: {summarize_for_log(params)}")
                    tool_result = self._execute_tool(tool_name, params)
                    rendered_result = render_tool_result(tool_result, user_input)
                    logger.info("【结果渲染】本地表格生成完成")
                    logger.info("【结果润色】开始 LLM 一句话总结...")
                    response = self._polish_result(rendered_result, user_input)
                elif decision and not need_tool:
                    response = decision.answer or "无法理解您的问题"
                else:
                    response = str(raw_response)
                    logger.warning("【解析失败】降级为直接返回 LLM 输出")

            elif intent_type == "chat":
                logger.info("【路由】进入闲聊处理流程")
                response = self.chat_chain.invoke({
                    "input": user_input,
                    "chat_history": self.memory_manager.get_history(user_id)
                })
                logger.info(f"【闲聊链返回】类型: {type(response).__name__}, 内容: {summarize_for_log(response)}")
                if isinstance(response, dict):
                    response = response.get("text", str(response))
            else:
                logger.warning("【路由】无法识别意图，返回默认响应")
                response = "抱歉，我无法理解您的问题，请尝试重新描述。"

            # 3. 更新记忆
            logger.info("【步骤3】更新对话记忆")
            self.memory_manager.add_user_message(user_input, user_id)
            self.memory_manager.add_ai_message(str(response), user_id)

            # 4. 长期记忆：轮次计数和摘要生成
            turn_count = self.memory_manager.increment_turn(user_id)
            from agent.settings import get_settings
            settings = get_settings()
            threshold = settings.memory_summary_threshold

            if turn_count >= threshold and self._memory_rag:
                logger.info(f"【长期记忆】轮次达到阈值({turn_count}>={threshold})，开始生成摘要")
                chat_history = self.memory_manager.get_history(user_id)
                summary_data = self._generate_memory_summary(chat_history, turn_count)

                if summary_data:
                    memory_id = self._memory_rag.add_memory(
                        user_id=user_id,
                        summary=summary_data.get("summary", ""),
                        key_entities=summary_data.get("key_entities", []),
                        topics=summary_data.get("topics", []),
                        conversation_turns=summary_data.get("conversation_turns", turn_count)
                    )
                    if memory_id:
                        logger.info(f"【长期记忆】摘要已存储: {memory_id}")
                        self.memory_manager.trim_history(user_id, keep_last_pairs=settings.memory_recent_pairs)
                        self.memory_manager.reset_turn_count(user_id)
                        logger.info("【长期记忆】已裁剪短期记忆并重置轮次")
                    else:
                        logger.warning("【长期记忆】摘要存储失败")
                else:
                    logger.warning("【长期记忆】摘要生成失败")

            logger.info(f"【最终响应】{summarize_for_log(response)}")

            return str(response)

        except Exception as e:
            logger.error(f"【处理失败】错误: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
