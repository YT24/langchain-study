import json
import logging
from decimal import Decimal
from typing import Optional
from langchain_core.tools import tool
from db.dao.order_dao import OrderDAO

logger = logging.getLogger(__name__)
_dao = OrderDAO()


def _to_json(data) -> str:
    """将数据转为 JSON 字符串，处理 Decimal 和日期类型"""
    def _default(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return str(obj)
    return json.dumps(data, ensure_ascii=False, default=_default)


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
    logger.info(f"【工具调用】query_order_list | userId={userId}, status={status}")
    try:
        has_amount = minAmount is not None or maxAmount is not None
        has_date = startDate is not None or endDate is not None

        if has_amount and has_date:
            orders = _dao.query_by_conditions(
                userId, status, minAmount, maxAmount, startDate, endDate
            )
        elif has_amount:
            orders = _dao.query_by_amount_range(userId, minAmount or 0, maxAmount or float('inf'))
            if status:
                orders = [o for o in orders if o["status"] == status]
        elif has_date:
            orders = _dao.query_by_date_range(userId, startDate, endDate)
            if status:
                orders = [o for o in orders if o["status"] == status]
        elif status:
            orders = _dao.query_by_user_and_status(userId, status)
        else:
            orders = _dao.query_by_user(userId)

        logger.info(f"【工具调用】query_order_list | 返回 {len(orders)} 条记录")
        return _to_json(orders)
    except Exception as e:
        logger.error(f"【工具调用】query_order_list | 异常: {e}")
        return f"查询订单列表失败: {str(e)}"


@tool
def query_order_detail(orderNo: str) -> str:
    """查询订单详情

    Args:
        orderNo: 订单号

    Returns:
        订单详情JSON字符串
    """
    logger.info(f"【工具调用】query_order_detail | orderNo={orderNo}")
    try:
        order = _dao.query_by_order_no(orderNo)
        if order:
            logger.info("【工具调用】query_order_detail | 成功")
            return _to_json(order)
        return f"未找到订单: {orderNo}"
    except Exception as e:
        logger.error(f"【工具调用】query_order_detail | 异常: {e}")
        return f"查询订单详情失败: {str(e)}"


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
    logger.info(f"【工具调用】query_order_statistics | userId={userId}")
    try:
        if minAmount is not None or maxAmount is not None:
            count = _dao.count_by_amount_range(
                userId, minAmount or 0, maxAmount or float('inf')
            )
            total = _dao.sum_amount_by_amount_range(
                userId, minAmount or 0, maxAmount or float('inf')
            )
        else:
            count = _dao.count_by_user(userId)
            total = _dao.sum_amount_by_user(userId)

        avg = total / count if count > 0 else 0
        result = {
            "orderCount": count,
            "totalAmount": round(total, 2),
            "averageAmount": round(avg, 2),
            "userId": userId
        }
        logger.info(f"【工具调用】query_order_statistics | 成功: {result}")
        return _to_json(result)
    except Exception as e:
        logger.error(f"【工具调用】query_order_statistics | 异常: {e}")
        return f"查询订单统计失败: {str(e)}"


ORDER_TOOLS = [query_order_list, query_order_detail, query_order_statistics]
