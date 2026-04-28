import logging
from langchain_core.tools import tool
from db.dao.user_dao import UserDAO

logger = logging.getLogger(__name__)
_dao = UserDAO()


@tool
def query_user_info(userId: str) -> str:
    """查询用户信息

    Args:
        userId: 用户ID

    Returns:
        用户信息JSON字符串
    """
    logger.info(f"【工具调用】query_user_info | userId={userId}")
    try:
        user = _dao.query_by_user_id(userId)
        if user:
            logger.info("【工具调用】query_user_info | 成功")
            import json
            return json.dumps(user, ensure_ascii=False, default=str)
        return f"未找到用户: {userId}"
    except Exception as e:
        logger.error(f"【工具调用】query_user_info | 异常: {e}")
        return f"查询用户信息失败: {str(e)}"


USER_TOOLS = [query_user_info]
