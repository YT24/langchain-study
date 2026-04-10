"""
Tool Executor - 工具执行器
"""
import json
import time
from typing import Dict, List, Any, Optional


class ToolExecutor:
    """工具执行器"""

    def __init__(self, backend_url: str = "http://localhost:8080"):
        self.backend_url = backend_url
        self.tools = {}  # 注册的工具

    def register_tool(self, name: str, tool_instance: Any):
        """注册工具"""
        self.tools[name] = tool_instance

    def register_default_tools(self):
        """注册默认工具"""
        from ..tools.order_tool import OrderTool
        from ..tools.user_tool import UserTool
        from ..tools.inventory_tool import InventoryTool

        self.register_tool("OrderTool", OrderTool())
        self.register_tool("UserTool", UserTool())
        self.register_tool("InventoryTool", InventoryTool())

    async def execute(self, tool_calls: List[Dict]) -> str:
        """
        执行工具调用

        Args:
            tool_calls: [{"tool": "OrderTool", "action": "query_order_list", "params": {...}}]

        Returns:
            工具执行结果的字符串表示
        """
        results = []

        for call in tool_calls:
            tool_name = call.get("tool")
            action = call.get("action")
            params = call.get("params", {})

            if tool_name not in self.tools:
                results.append(f"错误：未知工具 {tool_name}")
                continue

            tool = self.tools[tool_name]
            method_name = action.replace("_", "_")  # 假设方法名就是 action

            if not hasattr(tool, method_name):
                results.append(f"错误：{tool_name} 没有 {action} 方法")
                continue

            try:
                method = getattr(tool, method_name)
                start_time = time.time()
                result = method(**params)
                duration = int((time.time() - start_time) * 1000)

                # 记录日志
                self._log_call(tool_name, action, params, str(result)[:500], duration)

                results.append(json.dumps(result, ensure_ascii=False))

            except Exception as e:
                results.append(f"执行错误：{str(e)}")

        return "\n\n".join(results) if results else "没有执行任何工具"

    def _log_call(self, tool_name: str, action: str, params: Dict, result: str, duration_ms: int):
        """记录工具调用日志"""
        try:
            import requests
            requests.post(
                f"{self.backend_url}/api/tools/log",
                json={
                    "toolName": tool_name,
                    "action": action,
                    "params": json.dumps(params, ensure_ascii=False),
                    "result": result,
                    "durationMs": duration_ms
                },
                timeout=5
            )
        except Exception as e:
            print(f"日志记录失败: {e}")


class SyncToolExecutor(ToolExecutor):
    """同步版本的工具执行器"""

    def execute(self, tool_calls: List[Dict]) -> str:
        """同步执行"""
        results = []

        for call in tool_calls:
            tool_name = call.get("tool")
            action = call.get("action")
            params = call.get("params", {})

            if tool_name not in self.tools:
                results.append(f"错误：未知工具 {tool_name}")
                continue

            tool = self.tools[tool_name]

            try:
                method = getattr(tool, action)
                start_time = time.time()
                result = method(**params)
                duration = int((time.time() - start_time) * 1000)

                self._log_call(tool_name, action, params, str(result)[:500], duration)

                if isinstance(result, list):
                    results.append(json.dumps(result, ensure_ascii=False))
                elif isinstance(result, dict):
                    results.append(json.dumps(result, ensure_ascii=False))
                else:
                    results.append(str(result))

            except Exception as e:
                results.append(f"执行错误：{str(e)}")

        return "\n\n".join(results) if results else "没有执行任何工具"
