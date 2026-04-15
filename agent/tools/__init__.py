from typing import List
from langchain_core.tools import Tool


def create_all_tools(base_url: str) -> List[Tool]:
    """创建所有工具实例"""
    from .order_tool import create_order_tools
    from .user_tool import create_user_tools
    from .inventory_tool import create_inventory_tools

    tools = []
    tools.extend(create_order_tools(base_url))
    tools.extend(create_user_tools(base_url))
    tools.extend(create_inventory_tools(base_url))
    return tools


__all__ = ["create_all_tools"]