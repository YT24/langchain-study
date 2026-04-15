from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Agent 编排器 - 统一调度各 Chain"""

    def __init__(
        self,
        intent_chain,
        query_chain,
        chat_chain,
        memory_manager
    ):
        self.intent_chain = intent_chain
        self.query_chain = query_chain
        self.chat_chain = chat_chain
        self.memory_manager = memory_manager

    def process(self, user_input: str, user_id: Optional[str] = None) -> str:
        """处理用户输入"""
        try:
            # 1. 意图识别
            intent_result = self.intent_chain.invoke({"user_input": user_input})

            # 提取 Intent 对象
            intent_obj = intent_result if hasattr(intent_result, 'intent') else None

            if intent_obj:
                intent_type = intent_obj.intent
                logger.info(f"识别意图: {intent_type}, 原因: {intent_obj.reason}")
            else:
                # 降级处理：默认按查询处理
                intent_type = "query"
                logger.warning(f"意图识别降级，默认按 query 处理")

            # 2. 路由分发
            if intent_type in ("query", "statistic"):
                response = self.query_chain.invoke({
                    "input": user_input,
                    "chat_history": self.memory_manager.get_history()
                })
                if isinstance(response, dict):
                    response = response.get("output", str(response))
            elif intent_type == "chat":
                response = self.chat_chain.invoke({
                    "input": user_input,
                    "chat_history": self.memory_manager.get_history()
                })
                if isinstance(response, dict):
                    response = response.get("text", str(response))
            else:
                response = "抱歉，我无法理解您的问题，请尝试重新描述。"

            # 3. 更新记忆
            self.memory_manager.add_user_message(user_input)
            self.memory_manager.add_ai_message(str(response))

            return str(response)

        except Exception as e:
            logger.error(f"处理用户输入失败: {e}")
            raise
