from .order_tool import BaseTool

class UserTool(BaseTool):
    def __init__(self):
        super().__init__()

    def query_user_info(self, userId: str) -> dict:
        result = self.call_api("/tools/user/query", "query_user_info", {"userId": userId})
        if not result.get("success"):
            raise Exception(result.get("message", "查询失败"))
        return result.get("data")
