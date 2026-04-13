"""
Tool Executor - 工具执行器
支持从后端动态加载工具
"""
import json
import time
from typing import Dict, List, Any, Optional
import requests


class SyncToolExecutor:
    """同步工具执行器"""

    # Python 工具类映射
    TOOL_CLASSES = {
        "OrderTool": None,  # 延迟导入
        "UserTool": None,
        "InventoryTool": None
    }

    def __init__(self, backend_url: str = "http://localhost:8080"):
        self.backend_url = backend_url
        self.tools = {}  # 注册的工具 {tool_name: instance}
        self.available_tools = []  # 后端可用工具列表

    def load_tools_from_backend(self):
        """从后端加载可用工具并注册"""
        try:
            response = requests.get(f"{self.backend_url}/tools", timeout=10)
            response.raise_for_status()
            result = response.json()

            if result.get("success"):
                self.available_tools = result.get("data", [])
                self._register_available_tools()
                print(f"已从后端加载 {len(self.available_tools)} 个工具")
            else:
                print("从后端获取工具失败")

        except Exception as e:
            print(f"从后端加载工具失败: {e}，使用空工具集")

    def _register_available_tools(self):
        """根据后端返回的工具注册 Python 工具"""
        # 清空现有工具
        self.tools = {}

        # 延迟导入工具类
        if self.TOOL_CLASSES.get("OrderTool") is None:
            from ..tools.order_tool import OrderTool
            from ..tools.user_tool import UserTool
            from ..tools.inventory_tool import InventoryTool
            self.TOOL_CLASSES["OrderTool"] = OrderTool
            self.TOOL_CLASSES["UserTool"] = UserTool
            self.TOOL_CLASSES["InventoryTool"] = InventoryTool

        # 注册后端启用的工具
        for tool in self.available_tools:
            tool_name = tool.get("name")
            if tool_name in self.TOOL_CLASSES and tool.get("enabled", True):
                self.tools[tool_name] = self.TOOL_CLASSES[tool_name]()

        print(f"已注册工具: {list(self.tools.keys())}")

    def execute(self, tool_calls: List[Dict]) -> str:
        """执行工具调用"""
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

    def _log_call(self, tool_name: str, action: str, params: Dict, result: str, duration_ms: int):
        """记录工具调用日志"""
        try:
            requests.post(
                f"{self.backend_url}/tools/log",
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
