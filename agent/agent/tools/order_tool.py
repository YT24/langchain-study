import requests
from typing import Dict, Any, Optional, List

class BaseTool:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url

    def call_api(self, endpoint: str, action: str, params: Dict[str, Any]) -> Dict:
        url = f"{self.base_url}{endpoint}"
        payload = {"action": action, "params": params}
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()


class OrderTool(BaseTool):
    def __init__(self):
        super().__init__()

    def query_order_list(self, userId: str, status: Optional[str] = None,
                         minAmount: Optional[float] = None,
                         maxAmount: Optional[float] = None,
                         startDate: Optional[str] = None,
                         endDate: Optional[str] = None) -> List[Dict]:
        params = {"userId": userId}
        if status:
            params["status"] = status
        if minAmount is not None:
            params["minAmount"] = minAmount
        if maxAmount is not None:
            params["maxAmount"] = maxAmount
        if startDate:
            params["startDate"] = startDate
        if endDate:
            params["endDate"] = endDate

        result = self.call_api("/tools/order/query", "query_order_list", params)
        if not result.get("success"):
            raise Exception(result.get("message", "查询失败"))
        return result.get("data", [])

    def query_order_detail(self, orderNo: str) -> Optional[Dict]:
        result = self.call_api("/tools/order/query", "query_order_detail", {"orderNo": orderNo})
        if not result.get("success"):
            raise Exception(result.get("message", "查询失败"))
        return result.get("data")

    def query_order_statistics(self, userId: str,
                                minAmount: Optional[float] = None,
                                maxAmount: Optional[float] = None) -> Dict:
        params = {"userId": userId}
        if minAmount is not None:
            params["minAmount"] = minAmount
        if maxAmount is not None:
            params["maxAmount"] = maxAmount
        result = self.call_api("/tools/order/query", "query_order_statistics", params)
        if not result.get("success"):
            raise Exception(result.get("message", "查询失败"))
        return result.get("data", {})
