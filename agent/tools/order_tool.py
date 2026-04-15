from langchain_core.tools import tool
from typing import Optional
import requests
import logging

logger = logging.getLogger(__name__)


def create_order_tools(base_url: str):
    """创建订单相关工具"""

    @tool
    def query_order_list(
        userId: str,
        status: Optional[str] = None,
        minAmount: Optional[float] = None,
        maxAmount: Optional[float] = None,
        startDate: Optional[str] = None,
        endDate: Optional[str] = None
    ) -> str:
        """查询用户订单列表

        Args:
            userId: 用户ID
            status: 订单状态（pending/paid/shipped/completed/cancelled）
            minAmount: 最小金额
            maxAmount: 最大金额
            startDate: 开始日期 (YYYY-MM-DD)
            endDate: 结束日期 (YYYY-MM-DD)

        Returns:
            订单列表JSON字符串
        """
        logger.info(f"【工具调用】query_order_list | 参数: userId={userId}, status={status}")
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

        logger.info(f"【工具调用】query_order_list | 请求后端: {base_url}/tools/order/query")
        resp = requests.post(
            f"{base_url}/tools/order/query",
            json={"action": "query_order_list", "params": params},
            timeout=30
        )
        result = resp.json()
        if not result.get("success"):
            logger.error(f"【工具调用】query_order_list | 失败: {result.get('message', '未知错误')}")
            return f"查询失败：{result.get('message', '未知错误')}"
        logger.info(f"【工具调用】query_order_list | 成功，返回 {len(result.get('data', []))} 条记录")
        return str(result.get("data", []))

    @tool
    def query_order_detail(orderNo: str) -> str:
        """查询订单详情

        Args:
            orderNo: 订单号

        Returns:
            订单详情JSON字符串
        """
        logger.info(f"【工具调用】query_order_detail | 参数: orderNo={orderNo}")
        resp = requests.post(
            f"{base_url}/tools/order/query",
            json={"action": "query_order_detail", "params": {"orderNo": orderNo}},
            timeout=30
        )
        result = resp.json()
        if not result.get("success"):
            logger.error(f"【工具调用】query_order_detail | 失败: {result.get('message', '未知错误')}")
            return f"查询失败：{result.get('message', '未知错误')}"
        logger.info(f"【工具调用】query_order_detail | 成功")
        return str(result.get("data", {}))

    @tool
    def query_order_statistics(
        userId: str,
        minAmount: Optional[float] = None,
        maxAmount: Optional[float] = None
    ) -> str:
        """查询用户订单统计

        Args:
            userId: 用户ID
            minAmount: 最小金额
            maxAmount: 最大金额

        Returns:
            订单统计信息（数量、总金额、平均金额）
        """
        logger.info(f"【工具调用】query_order_statistics | 参数: userId={userId}")
        params = {"userId": userId}
        if minAmount is not None:
            params["minAmount"] = minAmount
        if maxAmount is not None:
            params["maxAmount"] = maxAmount

        resp = requests.post(
            f"{base_url}/tools/order/query",
            json={"action": "query_order_statistics", "params": params},
            timeout=30
        )
        result = resp.json()
        if not result.get("success"):
            logger.error(f"【工具调用】query_order_statistics | 失败: {result.get('message', '未知错误')}")
            return f"查询失败：{result.get('message', '未知错误')}"
        logger.info(f"【工具调用】query_order_statistics | 成功: {result.get('data', {})}")
        return str(result.get("data", {}))

    return [query_order_list, query_order_detail, query_order_statistics]