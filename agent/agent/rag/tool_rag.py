"""
Tool RAG - 工具描述管理
简化版本：直接从后端加载工具描述
"""
import json
from typing import List, Dict, Optional
import requests


class ToolRAG:
    """工具检索增强（简化版）"""

    # 默认工具描述
    DEFAULT_TOOLS = """
可用工具：
OrderTool - 订单查询工具
   - query_order_list: 查询用户订单列表 (参数: userId, status, minAmount, maxAmount, startDate, endDate)
   - query_order_detail: 查询订单详情 (参数: orderNo)
   - query_order_statistics: 查询用户订单统计，返回订单数量、总金额、平均金额 (参数: userId, minAmount, maxAmount)
UserTool - 用户查询工具
   - query_user_info: 查询用户信息 (参数: userId)
InventoryTool - 库存查询工具
   - query_inventory: 按SKU查询库存 (参数: sku)
   - query_warehouse_stock: 按仓库查询库存 (参数: warehouse)
"""

    def __init__(self):
        self.tools_description = self.DEFAULT_TOOLS

    def load_from_backend(self, backend_url: str = "http://localhost:8080"):
        """从后端加载工具描述"""
        try:
            response = requests.get(f"{backend_url}/tools", timeout=10)
            response.raise_for_status()
            result = response.json()

            if result.get("success"):
                tools = result.get("data", [])
                self.tools_description = self._build_description(tools)
                print(f"已加载 {len(tools)} 个工具")
            else:
                print("从后端获取工具失败，使用默认工具描述")

        except Exception as e:
            print(f"从后端加载工具失败: {e}，使用默认工具描述")

    def _build_description(self, tools: List[Dict]) -> str:
        """构建工具描述文本"""
        lines = ["\n可用工具："]

        for tool in tools:
            tool_name = tool.get("name", "") if isinstance(tool, dict) else str(tool)
            tool_desc = tool.get("description", "") if isinstance(tool, dict) else ""

            lines.append(f"\n{tool_name} - {tool_desc}")

            # 处理 actions
            actions = tool.get("actions", []) if isinstance(tool, dict) else []
            if isinstance(actions, str):
                try:
                    actions = json.loads(actions)
                except:
                    actions = []
            if isinstance(actions, dict) and "actions" in actions:
                actions = actions["actions"]

            for action in actions:
                if not isinstance(action, dict):
                    continue
                action_name = action.get("name", "")
                action_desc = action.get("description", "")
                params = action.get("params", {})

                if isinstance(params, str):
                    try:
                        params = json.loads(params)
                    except:
                        params = {}

                params_str = ", ".join(params.keys()) if isinstance(params, dict) else ""
                lines.append(f"   - {action_name}: {action_desc} (参数: {params_str})")

        return "".join(lines)

    def get_tool_description(self) -> str:
        """获取工具描述"""
        return self.tools_description

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """保留接口，简化版直接返回全部工具"""
        return [{"content": self.tools_description, "metadata": {}}]

    def build_tool_description_from_rag(self, query: str, top_k: int = 5) -> str:
        """返回工具描述"""
        return self.tools_description


def init_tool_rag_from_backend(backend_url: str = "http://localhost:8080") -> ToolRAG:
    """初始化 ToolRAG"""
    tool_rag = ToolRAG()
    tool_rag.load_from_backend(backend_url)
    return tool_rag
