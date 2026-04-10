"""
Router - 意图路由
判断用户意图，决定如何处理
"""
import os
import json
import requests
from typing import Dict, Tuple


class Intent:
    QUERY = "query"           # 需要查询数据
    STATISTIC = "statistic"   # 需要统计
    CHAT = "chat"             # 一般对话
    UNKNOWN = "unknown"       # 无法理解


class Router:
    """意图路由器"""

    def __init__(self, deepseek_api_key: str = None, deepseek_base_url: str = "https://api.deepseek.com"):
        self.api_key = deepseek_api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = deepseek_base_url

    def classify(self, user_input: str) -> Tuple[str, str]:
        """
        分类用户意图

        Returns:
            (intent, reason)
        """
        if not self.api_key:
            return self._rule_based_classify(user_input)

        prompt = f"""你是一个意图分类器。用户输入后，判断用户的意图：

可选意图：
1. query - 需要查询具体数据的场景（如查询订单、查询用户、查询库存）
2. statistic - 需要统计汇总的场景（如计算总金额、统计数量、平均值）
3. chat - 一般对话、问候、闲聊、或无法归类的问题
4. unknown - 完全无法理解的输入

用户输入：{user_input}

返回格式（只返回JSON，不要其他内容）：
{{"intent": "query|statistic|chat|unknown", "reason": "简短判断理由"}}
"""

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1
            }
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()

            # 解析 JSON
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('{') and line.endswith('}'):
                    parsed = json.loads(line)
                    return parsed.get("intent", Intent.UNKNOWN), parsed.get("reason", "")

        except Exception as e:
            print(f"Router LLM 调用失败: {e}")

        return self._rule_based_classify(user_input)

    def _rule_based_classify(self, user_input: str) -> Tuple[str, str]:
        """基于规则的分类"""

        # 统计关键词
        statistic_keywords = ["统计", "汇总", "一共", "总金额", "总订单", "平均", "有多少", "多少笔", "总计"]
        for kw in statistic_keywords:
            if kw in user_input:
                return Intent.STATISTIC, f"包含统计关键词：{kw}"

        # 查询关键词
        query_keywords = ["查询", "查一下", "看看", "显示", "获取", "找一下"]
        for kw in query_keywords:
            if kw in user_input:
                return Intent.QUERY, f"包含查询关键词：{kw}"

        # 闲聊关键词
        chat_keywords = ["你好", "hi", "hello", "谢谢", "再见", "帮帮我"]
        for kw in chat_keywords:
            if kw in user_input:
                return Intent.CHAT, f"包含闲聊关键词：{kw}"

        return Intent.QUERY, "默认按查询处理"
