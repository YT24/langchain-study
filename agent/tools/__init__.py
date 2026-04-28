import logging
from .order_tool import ORDER_TOOLS
from .user_tool import USER_TOOLS
from .inventory_tool import INVENTORY_TOOLS
from .registry import get_registry

logger = logging.getLogger(__name__)


def create_all_tools() -> list:
    """创建所有工具并从注册中心获取启用列表"""
    registry = get_registry()

    for tool in ORDER_TOOLS:
        registry.register(tool, category="订单管理", icon="shopping-cart", display_name=tool.name)
    for tool in USER_TOOLS:
        registry.register(tool, category="用户管理", icon="user", display_name=tool.name)
    for tool in INVENTORY_TOOLS:
        registry.register(tool, category="库存管理", icon="package", display_name=tool.name)

    tools = registry.get_all()
    logger.info(f"【工具初始化】共注册 {len(tools)} 个工具")
    return tools


__all__ = ["create_all_tools"]
