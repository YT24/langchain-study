from langchain_core.tools import tool
import requests
import logging

logger = logging.getLogger(__name__)


def create_inventory_tools(base_url: str):
    """创建库存相关工具"""

    @tool
    def query_inventory(sku: str) -> str:
        """按SKU查询库存

        Args:
            sku: 商品SKU

        Returns:
            库存信息JSON字符串
        """
        logger.info(f"【工具调用】query_inventory | 参数: sku={sku}")
        resp = requests.post(
            f"{base_url}/tools/inventory/query",
            json={"action": "query_inventory", "params": {"sku": sku}},
            timeout=30
        )
        result = resp.json()
        if not result.get("success"):
            logger.error(f"【工具调用】query_inventory | 失败: {result.get('message', '未知错误')}")
            return f"查询失败：{result.get('message', '未知错误')}"
        logger.info(f"【工具调用】query_inventory | 成功")
        return str(result.get("data", []))

    @tool
    def query_warehouse_stock(warehouse: str) -> str:
        """按仓库查询库存

        Args:
            warehouse: 仓库名称

        Returns:
            仓库库存列表JSON字符串
        """
        logger.info(f"【工具调用】query_warehouse_stock | 参数: warehouse={warehouse}")
        resp = requests.post(
            f"{base_url}/tools/inventory/query",
            json={"action": "query_warehouse_stock", "params": {"warehouse": warehouse}},
            timeout=30
        )
        result = resp.json()
        if not result.get("success"):
            logger.error(f"【工具调用】query_warehouse_stock | 失败: {result.get('message', '未知错误')}")
            return f"查询失败：{result.get('message', '未知错误')}"
        logger.info(f"【工具调用】query_warehouse_stock | 成功")
        return str(result.get("data", []))

    return [query_inventory, query_warehouse_stock]