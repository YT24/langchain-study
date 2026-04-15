from langchain_core.tools import tool
import requests


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
        resp = requests.post(
            f"{base_url}/tools/user/query",
            json={"action": "query_user_info", "params": {"userId": userId}},
            timeout=30
        )
        result = resp.json()
        if not result.get("success"):
            return f"查询失败：{result.get('message', '未知错误')}"
        return str(result.get("data", {}))

    return [query_user_info]