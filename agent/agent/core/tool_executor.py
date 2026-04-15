"""
Tool Executor - 工具执行器
内置工具默认全部可用，后端状态仅用于禁用工具
"""
import json
import time
from typing import Dict, List, Any, Optional
import requests


class SyncToolExecutor:
    """同步工具执行器"""

    def __init__(self, backend_url: str = "http://localhost:8080"):
        self.backend_url = backend_url
        self.tools: Dict[str, Any] = {}  # {tool_name: instance}

    def load_tools_from_backend(self):
        """加载工具：先注册全部内置工具，再从后端获取禁用状态"""
        self._register_builtin_tools()

        try:
            response = requests.get(f"{self.backend_url}/tools", timeout=10)
            response.raise_for_status()
            result = response.json()
            if result.get("success"):
                backend_tools = result.get("data", [])
                self._apply_backend_status(backend_tools)
                print(f"已从后端加载 {len(backend_tools)} 个工具配置")
            else:
                print("从后端获取工具配置失败，使用全部内置工具")
        except Exception as e:
            print(f"从后端加载工具配置失败: {e}，使用全部内置工具")

        print(f"已注册工具: {list(self.tools.keys())}")

    def _register_builtin_tools(self):
        """注册所有内置工具（不依赖后端）"""
        from ..tools.order_tool import OrderTool
        from ..tools.user_tool import UserTool
        from ..tools.inventory_tool import InventoryTool

        self.tools = {
            "OrderTool": OrderTool(),
            "UserTool": UserTool(),
            "InventoryTool": InventoryTool(),
        }

    def _apply_backend_status(self, backend_tools: List[Dict]):
        """根据后端 status 字段禁用工具（status=0 则移除）"""
        for tool in backend_tools:
            tool_name = tool.get("name")
            if tool_name and tool.get("status", 1) == 0:
                if tool_name in self.tools:
                    del self.tools[tool_name]
                    print(f"工具 {tool_name} 已被禁用（后端 status=0）")

    def reload(self):
        """重新加载工具状态"""
        self.load_tools_from_backend()

    def execute(self, tool_calls: List[Dict]) -> str:
        """执行工具调用"""
        results = []

        for call in tool_calls:
            tool_name = call.get("tool")
            action = call.get("action")
            params = call.get("params") or {}

            if tool_name not in self.tools:
                available = list(self.tools.keys())
                results.append(f"错误：未知工具 {tool_name}，可用工具：{available}")
                continue

            tool = self.tools[tool_name]

            if not hasattr(tool, action):
                results.append(f"错误：工具 {tool_name} 不支持 action: {action}")
                continue

            try:
                method = getattr(tool, action)
                start_time = time.time()
                result = method(**params)
                duration = int((time.time() - start_time) * 1000)

                self._log_call(tool_name, action, params, str(result)[:500], duration)

                if isinstance(result, (list, dict)):
                    results.append(json.dumps(result, ensure_ascii=False))
                else:
                    results.append(str(result))

            except Exception as e:
                results.append(f"执行错误（{tool_name}.{action}）：{str(e)}")

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
