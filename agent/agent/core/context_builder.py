"""
Context Builder - 上下文构建器
构建 LLM 所需的完整 prompt
"""
from typing import Dict, List, Optional


class ContextBuilder:
    """上下文构建器"""

    def __init__(self):
        self.system_prompt = """你是一个专业的业务查询助手，基于提供的数据回答用户问题。

重要规则：
1. 只回答与业务相关的问题
2. 数据必须来自工具返回，不要编造数据
3. 回答要清晰、准确，使用 Markdown 格式化
4. 如果用户问题涉及统计，使用 Markdown 表格展示
5. 如果工具返回空数据，明确告知用户"""

    def build(self, user_input: str, context: Dict) -> str:
        """
        构建完整的 prompt

        Args:
            user_input: 用户输入
            context: 包含以下键的字典
                - tools: 可用工具描述 (str)
                - knowledge: 业务知识 (str)
                - memory: 记忆上下文 (str)
                - history: 对话历史 (str)
                - tool_results: 工具执行结果 (str, optional)
        """
        parts = [self.system_prompt]

        # 添加工具描述
        if context.get("tools"):
            parts.append(f"\n{context['tools']}")

        # 添加业务知识
        if context.get("knowledge"):
            parts.append(f"\n{context['knowledge']}")

        # 添加记忆上下文
        if context.get("memory"):
            parts.append(f"\n{context['memory']}")

        # 添加对话历史
        if context.get("history"):
            parts.append(f"\n对话历史：\n{context['history']}")

        # 添加工具结果
        if context.get("tool_results"):
            parts.append(f"\n工具执行结果：\n{context['tool_results']}")
            parts.append("\n请基于上述工具返回的数据，用 Markdown 格式回答用户。")

        parts.append(f"\n用户问题：{user_input}")

        return "\n\n".join(parts)

    def build_tool_call_prompt(self, user_input: str, context: Dict) -> str:
        """
        构建工具调用 prompt

        Args:
            user_input: 用户输入
            context: 包含 tools, knowledge, memory, history
        """
        parts = ["""你是一个业务查询助手。你没有自带的数据，必须通过调用工具来获取用户需要的信息。

重要：
1. 必须严格按照工具的 action 名称返回
2. 返回 JSON 格式的工具调用请求，不要返回其他内容
3. 如果用户问题涉及统计，必须使用 query_order_statistics 工具
4. 如果用户问题涉及查看具体订单，必须使用 query_order_list 工具
5. 如果用户问题涉及用户信息，使用 query_user_info 工具
6. 如果用户问题涉及库存，使用 query_inventory 或 query_warehouse_stock 工具"""]

        if context.get("tools"):
            parts.append(f"\n{context['tools']}")

        if context.get("knowledge"):
            parts.append(f"\n{context['knowledge']}")

        if context.get("memory"):
            parts.append(f"\n{context['memory']}")

        if context.get("history"):
            parts.append(f"\n对话历史：\n{context['history']}")

        parts.append(f"\n用户问题：{user_input}")

        parts.append("""
返回格式（只返回JSON，不要其他内容）：
{"tool": "工具名称", "action": "action名称", "params": {"参数名": "参数值"}}

示例1：用户问"U001的订单"
{"tool": "OrderTool", "action": "query_order_list", "params": {"userId": "U001"}}

示例2：用户问"U001的订单总金额"
{"tool": "OrderTool", "action": "query_order_statistics", "params": {"userId": "U001"}}

示例3：用户问"U001金额大于300的订单"
{"tool": "OrderTool", "action": "query_order_statistics", "params": {"userId": "U001", "minAmount": 300}}
""")

        return "\n\n".join(parts)

    def build_response_prompt(self, user_input: str, tool_results: str, context: Dict) -> str:
        """
        构建响应生成 prompt
        """
        parts = ["""你是一个专业的业务助手。工具已经返回了查询结果。

请将工具返回的数据用 Markdown 表格格式整理后回答用户。
- 表格要有表头
- 数据要整齐对齐
- 如有汇总数据，在表格后添加汇总说明

工具返回的数据："""]

        parts.append(f"\n{tool_results}")

        if context.get("memory"):
            parts.append(f"\n用户历史：\n{context['memory']}")

        parts.append(f"\n原始问题：{user_input}")

        return "\n\n".join(parts)
