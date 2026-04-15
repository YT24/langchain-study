from typing import List
from langchain_core.tools import Tool
import logging

logger = logging.getLogger(__name__)


def create_all_tools(base_url: str) -> List[Tool]:
    """创建所有工具实例（动态加载，失败时使用 fallback）"""
    from .dynamic_loader import DynamicToolLoader

    loader = DynamicToolLoader(base_url)
    tools = loader.load_all_tools()

    # 检查动态加载的工具是否有效（至少有参数或能正常工作）
    if tools:
        # 测试第一个工具看是否能正常调用
        try:
            test_tool = tools[0]
            logger.info(f"【工具加载】动态加载了 {len(tools)} 个工具，验证可用性...")
            # 如果工具没有参数定义，认为是无效的
            if not hasattr(test_tool, 'input_schema'):
                raise ValueError("工具缺少 input_schema")
        except Exception as e:
            logger.warning(f"【工具加载】动态工具验证失败: {e}，使用备用工具")
            tools = create_fallback_tools(base_url)
    else:
        logger.warning("【工具加载】动态加载返回空，使用备用工具")
        tools = create_fallback_tools(base_url)

    return tools


def create_fallback_tools(base_url: str) -> List[Tool]:
    """备用硬编码工具（当动态加载失败时使用）"""
    from .order_tool import create_order_tools
    from .user_tool import create_user_tools
    from .inventory_tool import create_inventory_tools

    tools = []
    tools.extend(create_order_tools(base_url))
    tools.extend(create_user_tools(base_url))
    tools.extend(create_inventory_tools(base_url))
    return tools


def reload_tools(base_url: str) -> List[Tool]:
    """重新加载工具（用于热更新）"""
    return create_all_tools(base_url)


__all__ = ["create_all_tools", "create_fallback_tools", "reload_tools"]