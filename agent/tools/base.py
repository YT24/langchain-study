import functools
import requests
from typing import Callable


def handle_tool_errors(func: Callable) -> Callable:
    """工具错误处理装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.Timeout:
            return "错误：请求超时，请稍后重试"
        except requests.exceptions.ConnectionError:
            return "错误：后端服务不可用，请检查服务状态"
        except Exception as e:
            return f"错误：{str(e)}"
    return wrapper