import json
import logging
from langchain_core.tools import tool
from db.dao.inventory_dao import InventoryDAO

logger = logging.getLogger(__name__)
_dao = InventoryDAO()


@tool
def query_inventory(sku: str) -> str:
    """按SKU查询库存

    Args:
        sku: 商品SKU

    Returns:
        库存信息JSON字符串
    """
    logger.info(f"【工具调用】query_inventory | sku={sku}")
    try:
        items = _dao.query_by_sku(sku)
        logger.info(f"【工具调用】query_inventory | 返回 {len(items)} 条记录")
        return json.dumps(items, ensure_ascii=False, default=str)
    except Exception as e:
        logger.error(f"【工具调用】query_inventory | 异常: {e}")
        return f"查询库存失败: {str(e)}"


@tool
def query_warehouse_stock(warehouse: str) -> str:
    """按仓库查询库存

    Args:
        warehouse: 仓库名称

    Returns:
        仓库库存列表JSON字符串
    """
    logger.info(f"【工具调用】query_warehouse_stock | warehouse={warehouse}")
    try:
        items = _dao.query_by_warehouse(warehouse)
        logger.info(f"【工具调用】query_warehouse_stock | 返回 {len(items)} 条记录")
        return json.dumps(items, ensure_ascii=False, default=str)
    except Exception as e:
        logger.error(f"【工具调用】query_warehouse_stock | 异常: {e}")
        return f"查询仓库库存失败: {str(e)}"


INVENTORY_TOOLS = [query_inventory, query_warehouse_stock]
