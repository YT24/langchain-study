from langchain_core.tools import StructuredTool
from typing import List, Dict, Any, Optional
import requests
import logging
import json
import types

logger = logging.getLogger(__name__)


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

        logger.info(f"【调试】_create_tool 原始 defn: name={name}, params={params}")

        if not name or not endpoint:
            logger.warning(f"【动态加载】跳过无效工具定义: {defn}")
            return None

        # 将工具名转换为有效的 Python 标识符
        safe_name = self._to_python_identifier(name)

        # 提取参数名列表
        param_names = [p.get("name") for p in params if p.get("name")]
        logger.info(f"【调试】提取的 param_names: {param_names}")

        # 构建带默认值的参数签名（必选参数在前，可选参数在后）
        required_params = []
        optional_params = []
        for p in params:
            p_name = p.get("name")
            if p_name:
                required = p.get("required", False)
                if required:
                    required_params.append(p_name)
                else:
                    optional_params.append(f"{p_name}=None")

        param_with_defaults = required_params + optional_params

        base_url = self.base_url

        # 获取 HTTP 超时配置
        from settings import get_settings
        http_timeout = get_settings().http_timeout

        # 构建参数字典字符串
        param_dict_str = "{" + ", ".join(f"'{pn}': {pn}" for pn in param_names) + "}"

        # 动态创建函数（参数带默认值）
        func_code = f"""
def {safe_name}({', '.join(param_with_defaults)}) -> str:
    '''{description}'''
    action = '{name}'
    req_params = {param_dict_str}
    req_params = {{k: v for k, v in req_params.items() if v is not None}}

    url = '{base_url}{endpoint}'
    payload = {{'action': action, 'params': req_params}}

    logger.info('【动态工具调用】' + '{name}' + ' | 参数: ' + str(req_params))

    try:
        if '{http_method}'.upper() == 'POST':
            resp = requests.post(url, json=payload, timeout={http_timeout})
        else:
            resp = requests.get(url, params=payload, timeout={http_timeout})

        resp.raise_for_status()
        result = resp.json()

        if result.get('success'):
            data = result.get('data', [])
            logger.info(f'【动态工具调用】{name} 成功 | 返回数据: {{str(data)[:200]}}')
            return json.dumps(data, ensure_ascii=False)
        else:
            msg = result.get('message', '未知错误')
            logger.error(f'【动态工具调用】{name} 失败 | 错误信息: {{msg}}')
            return '查询失败：' + msg
    except Exception as e:
        logger.error(f'【动态工具调用】{name} 异常: {{str(e)}}')
        return '调用失败: ' + str(e)
"""
        # 执行函数定义
        local_ns = {'requests': requests, 'json': json, 'logger': logger}
        exec(func_code, local_ns)
        func = local_ns[safe_name]

        # 使用 from_function 创建工具
        tool = StructuredTool.from_function(
            func=func,
            name=name,
            description=f"{display_name}：{description}",
            infer_schema=True
        )

        logger.info(f"【动态加载】创建工具: {name}, 参数: {param_names}")
        return tool

    def load_all_tools(self) -> List:
        """从后端加载所有工具"""
        tool_defs = self.fetch_tool_definitions()
        logger.info(f"【调试】load_all_tools 获取到 {len(tool_defs)} 个工具定义")
        if tool_defs:
            logger.info(f"【调试】第一个工具定义: {tool_defs[0]}")
        if not tool_defs:
            logger.warning("【动态加载】未获取到工具定义")
            return []
        return self.create_tools_from_definitions(tool_defs)
