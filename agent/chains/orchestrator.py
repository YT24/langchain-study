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
            logger.info("=" * 50)
            logger.info(f"【开始处理】用户输入: {user_input[:100]}")

            # 1. 意图识别
            logger.info("【步骤1】开始意图识别...")
            intent_result = self.intent_chain.invoke({"user_input": user_input})
            logger.info(f"【步骤1】意图识别返回: {intent_result}")

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
                response = self.query_chain.invoke({
                    "input": user_input,
                    "chat_history": self.memory_manager.get_history()
                })
                logger.info(f"【查询链返回】类型: {type(response).__name__}, 内容: {str(response)[:200]}")
                if isinstance(response, dict):
                    response = response.get("output", str(response))
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
