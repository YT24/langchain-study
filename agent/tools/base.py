import functools
import logging
from typing import Callable

logger = logging.getLogger(__name__)


def handle_tool_errors(func: Callable) -> Callable:
    """工具错误处理装饰器：统一捕获异常并返回友好消息"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"【工具异常】{func.__name__}: {e}")
            return f"工具执行失败：{str(e)}"
    return wrapper
