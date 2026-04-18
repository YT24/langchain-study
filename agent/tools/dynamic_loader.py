import json
import logging
from typing import Any, Dict, List, Optional

import requests
from langchain_core.tools import StructuredTool
from pydantic import create_model

logger = logging.getLogger(__name__)


SAFE_LOG_LENGTH = 200


def summarize_for_log(value: Any, max_length: int = SAFE_LOG_LENGTH) -> str:
    text = str(value)
    return text[:max_length] + "..." if len(text) > max_length else text


def _build_field_definition(required: bool):
    default = ... if required else None
    return (Optional[str], default)


def _make_tool_func(base_url: str, endpoint: str, http_method: str, http_timeout: int, tool_name: str, allowed_params: List[str]):
    def _tool(**kwargs) -> str:
        req_params = {k: v for k, v in kwargs.items() if v is not None and k in allowed_params}
        url = f"{base_url}{endpoint}"
        payload = {"action": tool_name, "params": req_params}

        logger.info(f"【动态工具调用】{tool_name} | 参数: {summarize_for_log(req_params)}")

        try:
            if http_method.upper() == "POST":
                resp = requests.post(url, json=payload, timeout=http_timeout)
            else:
                resp = requests.get(url, params=payload, timeout=http_timeout)

            resp.raise_for_status()
            result = resp.json()

            if result.get("success"):
                data = result.get("data", [])
                logger.info(f"【动态工具调用】{tool_name} 成功 | 返回摘要: {summarize_for_log(data)}")
                return json.dumps(data, ensure_ascii=False)

            msg = result.get("message", "未知错误")
            logger.error(f"【动态工具调用】{tool_name} 失败 | 错误信息: {msg}")
            return "查询失败：" + msg
        except Exception as e:
            logger.error(f"【动态工具调用】{tool_name} 异常: {str(e)}")
            return "调用失败: " + str(e)

    return _tool


def _build_args_schema(schema_name: str, params: List[Dict[str, Any]]):
    fields = {}
    for param in params:
        p_name = param.get("name")
        if not p_name:
            continue
        fields[p_name] = _build_field_definition(param.get("required", False))
    return create_model(schema_name, **fields)



def redact_tool_definition(defn: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": defn.get("name"),
        "endpoint": defn.get("endpoint"),
        "param_names": [p.get("name") for p in defn.get("params", []) if p.get("name")],
    }


class DynamicToolLoader:
    """从后端动态加载工具"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    @staticmethod
    def _to_python_identifier(name: str) -> str:
        """将任意字符串转换为有效的 Python 标识符

        test-auth -> test_auth
        TestAuth -> test_auth
        123abc -> _123abc
        """
        import re
        # 替换非字母数字下划线字符为下划线
        s1 = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        # 如果以数字开头，加前缀
        if s1[0].isdigit():
            s1 = '_' + s1
        return s1

    def fetch_tool_definitions(self) -> List[Dict[str, Any]]:
        """从后端获取所有工具定义"""
        try:
            resp = requests.get(f"{self.base_url}/tools/actions", timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if data.get("success"):
                tools = data.get("data", [])
                logger.info(f"【动态加载】获取到 {len(tools)} 个工具定义")
                return tools
            else:
                logger.error(f"【动态加载】失败: {data.get('message')}")
                return []
        except Exception as e:
            logger.error(f"【动态加载】请求失败: {e}")
            return []

    def create_tools_from_definitions(self, tool_defs: List[Dict[str, Any]]) -> List:
        """根据工具定义创建 LangChain Tools"""
        tools = []
        for defn in tool_defs:
            tool_obj = self._create_tool(defn)
            if tool_obj:
                tools.append(tool_obj)
        return tools

    def _create_tool(self, defn: Dict[str, Any]) -> Optional[StructuredTool]:
        """为单个工具定义创建 StructuredTool"""
        name = defn.get("name")
        display_name = defn.get("displayName", name)
        description = defn.get("description", "")
        endpoint = defn.get("endpoint", "")
        http_method = defn.get("httpMethod", "POST")
        params = defn.get("params", [])

        logger.info(f"【调试】_create_tool defn: {redact_tool_definition(defn)}")

        if not name or not endpoint:
            logger.warning(f"【动态加载】跳过无效工具定义: {redact_tool_definition(defn)}")
            return None

        param_names = [p.get("name") for p in params if p.get("name")]

        from agent.settings import get_settings
        http_timeout = get_settings().http_timeout

        func = _make_tool_func(
            base_url=self.base_url,
            endpoint=endpoint,
            http_method=http_method,
            http_timeout=http_timeout,
            tool_name=name,
            allowed_params=param_names,
        )
        func.__name__ = self._to_python_identifier(name)
        func.__doc__ = description

        args_schema = _build_args_schema(f"{func.__name__}_args", params)

        tool = StructuredTool.from_function(
            func=func,
            name=name,
            description=f"{display_name}：{description}",
            infer_schema=False,
            args_schema=args_schema,
        )

        logger.info(f"【动态加载】创建工具: {name}, 参数: {param_names}")
        return tool

    def load_all_tools(self) -> List:
        """从后端加载所有工具"""
        tool_defs = self.fetch_tool_definitions()
        logger.info(f"【调试】load_all_tools 获取到 {len(tool_defs)} 个工具定义")
        if tool_defs:
            logger.info(f"【调试】第一个工具定义: {redact_tool_definition(tool_defs[0])}")
        if not tool_defs:
            logger.warning("【动态加载】未获取到工具定义")
            return []
        return self.create_tools_from_definitions(tool_defs)
