from langchain_core.tools import tool
import requests
import logging

logger = logging.getLogger(__name__)


def create_user_tools(base_url: str):
    """创建用户相关工具"""

    @tool
    def query_user_info(userId: str) -> str:
        """查询用户信息

        Args:
            userId: 用户ID

        Returns:
            用户信息JSON字符串
        """
        logger.info(f"【工具调用】query_user_info | 参数: userId={userId}")
        resp = requests.post(
            f"{base_url}/tools/user/query",
            json={"action": "query_user_info", "params": {"userId": userId}},
            timeout=30
        )
        result = resp.json()
        if not result.get("success"):
            logger.error(f"【工具调用】query_user_info | 失败: {result.get('message', '未知错误')}")
            return f"查询失败：{result.get('message', '未知错误')}"
        logger.info(f"【工具调用】query_user_info | 成功")
        return str(result.get("data", {}))

    return [query_user_info]