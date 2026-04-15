# LangChain Agent 系统重构实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有 AI Agent 系统重构为基于 LangChain 0.1.x 标准组件的模块化架构

**Architecture:** 使用 LangChain 标准组件（create_react_agent、@tool、PromptTemplate、ConversationBufferMemory）重构系统，分为配置层、Chain 层、Tool 层、Memory 层，通过 Orchestrator 统一编排

**Tech Stack:** Python 3.10+, LangChain 0.1.x, Flask 3.0, DeepSeek API, ChromaDB, HuggingFace BGE

---

## 文件结构

```
agent/
├── __init__.py
├── server.py                    # Flask 入口（重写）
├── config.py                    # 配置管理（新建）
├── dependencies.py               # 依赖注入（新建）
│
├── schemas/                     # Pydantic 数据模型
│   ├── __init__.py
│   └── intent.py                # Intent 数据模型
│
├── prompts/                     # Prompt 模板
│   ├── __init__.py
│   ├── intent_prompt.py         # 意图识别 Prompt
│   ├── query_prompt.py          # 查询 Agent Prompt
│   └── chat_prompt.py          # 闲聊 Prompt
│
├── chains/                      # Chain 定义
│   ├── __init__.py
│   ├── intent_chain.py          # 意图识别链
│   ├── query_chain.py           # 工具查询链 (ReAct)
│   ├── chat_chain.py            # 闲聊链
│   └── orchestrator.py          # 编排器
│
├── tools/                       # LangChain Tools
│   ├── __init__.py
│   ├── base.py                  # 基础 Tool 装饰器
│   ├── order_tool.py            # 订单工具
│   ├── user_tool.py             # 用户工具
│   └── inventory_tool.py        # 库存工具
│
└── memory/                      # LangChain Memory
    ├── __init__.py
    └── conversation_memory.py    # 对话记忆管理
```

---

## Task 1: 创建目录结构和配置层

**Files:**
- Create: `agent/schemas/__init__.py`
- Create: `agent/schemas/intent.py`
- Create: `agent/prompts/__init__.py`
- Create: `agent/prompts/intent_prompt.py`
- Create: `agent/prompts/query_prompt.py`
- Create: `agent/prompts/chat_prompt.py`
- Create: `agent/chains/__init__.py`
- Create: `agent/tools/__init__.py`
- Create: `agent/memory/__init__.py`
- Create: `agent/utils/__init__.py`
- Create: `agent/config.py`
- Modify: `agent/requirements.txt`

- [ ] **Step 1: 创建 schemas/intent.py - Intent 数据模型**

```python
# agent/schemas/intent.py
from pydantic import BaseModel, Field
from typing import Literal


class Intent(BaseModel):
    """意图识别结果"""
    intent: Literal["query", "statistic", "chat", "unknown"] = Field(
        description="用户意图：query=查询数据, statistic=统计汇总, chat=闲聊, unknown=无法理解"
    )
    reason: str = Field(description="判断理由")
```

- [ ] **Step 2: 创建 prompts/intent_prompt.py - 意图识别 Prompt**

```python
# agent/prompts/intent_prompt.py
from langchain.prompts import PromptTemplate

INTENT_TEMPLATE = """你是一个意图分类器。用户输入后，判断用户的意图：

可选意图：
- query: 需要查询具体数据（订单、用户、库存）
- statistic: 需要统计汇总（金额、数量、平均值）
- chat: 一般对话、问候、闲聊
- unknown: 完全无法理解

用户输入：{user_input}

{format_instructions}

返回格式（只返回JSON，不要其他内容）：
{{"intent": "query|statistic|chat|unknown", "reason": "简短判断理由"}}
"""

def get_intent_prompt() -> PromptTemplate:
    return PromptTemplate.from_template(INTENT_TEMPLATE)
```

- [ ] **Step 3: 创建 prompts/query_prompt.py - 查询 Agent Prompt**

```python
# agent/prompts/query_prompt.py
from langchain.prompts import PromptTemplate

QUERY_TEMPLATE = """你是一个智能助手，可以调用工具来回答用户问题。

可用工具：
{tools}

注意：
- 只使用提供的工具
- 如果工具返回错误，说明原因并尝试其他方式
- 如果无法回答，说明原因

历史对话：
{chat_history}

当前用户：{input}
{agent_scratchpad}"""

def get_query_prompt() -> PromptTemplate:
    return PromptTemplate.from_template(QUERY_TEMPLATE)
```

- [ ] **Step 4: 创建 prompts/chat_prompt.py - 闲聊 Prompt**

```python
# agent/prompts/chat_prompt.py
from langchain.prompts import PromptTemplate

CHAT_TEMPLATE = """你是一个小助手，友善地回答用户问题。

历史对话：
{chat_history}

当前用户：{input}
助手："""

def get_chat_prompt() -> PromptTemplate:
    return PromptTemplate.from_template(CHAT_TEMPLATE)
```

- [ ] **Step 5: 创建 config.py - 配置管理**

```python
# agent/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # DeepSeek
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # Backend
    backend_url: str = "http://localhost:8080"

    # Agent
    agent_port: int = 5001

    # Memory
    max_token_limit: int = 2000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 6: 更新 requirements.txt - 添加 LangChain 依赖**

```txt
# agent/requirements.txt
langchain>=0.1.0,<0.2.0
langchain-core>=0.1.0,<0.2.0
langchain-community>=0.1.0,<0.2.0
pydantic>=2.0
pydantic-settings>=2.0
flask>=3.0.0
requests>=2.31.0
chromadb>=0.4.0
sentence-transformers>=2.0
```

- [ ] **Step 7: 创建 __init__.py 文件并提交**

```bash
# 创建所有 __init__.py 文件后
git add -A
git commit -m "feat: 添加 LangChain 重构 - 第一阶段（目录结构、配置、Schema、Prompts）"
```

---

## Task 2: 创建 LangChain Tools

**Files:**
- Create: `agent/tools/base.py`
- Create: `agent/tools/order_tool.py`
- Create: `agent/tools/user_tool.py`
- Create: `agent/tools/inventory_tool.py`

- [ ] **Step 1: 创建 tools/base.py - 基础工具装饰器和错误处理**

```python
# agent/tools/base.py
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
```

- [ ] **Step 2: 创建 tools/order_tool.py - 订单工具**

```python
# agent/tools/order_tool.py
from langchain_core.tools import tool
from typing import Optional
import requests


def create_order_tools(base_url: str):
    """创建订单相关工具"""

    @tool
    def query_order_list(
        userId: str,
        status: Optional[str] = None,
        minAmount: Optional[float] = None,
        maxAmount: Optional[float] = None,
        startDate: Optional[str] = None,
        endDate: Optional[str] = None
    ) -> str:
        """查询用户订单列表

        Args:
            userId: 用户ID
            status: 订单状态（pending/paid/shipped/completed/cancelled）
            minAmount: 最小金额
            maxAmount: 最大金额
            startDate: 开始日期 (YYYY-MM-DD)
            endDate: 结束日期 (YYYY-MM-DD)

        Returns:
            订单列表JSON字符串
        """
        params = {"userId": userId}
        if status:
            params["status"] = status
        if minAmount is not None:
            params["minAmount"] = minAmount
        if maxAmount is not None:
            params["maxAmount"] = maxAmount
        if startDate:
            params["startDate"] = startDate
        if endDate:
            params["endDate"] = endDate

        resp = requests.post(
            f"{base_url}/tools/order/query",
            json={"action": "query_order_list", "params": params},
            timeout=30
        )
        result = resp.json()
        if not result.get("success"):
            return f"查询失败：{result.get('message', '未知错误')}"
        return str(result.get("data", []))

    @tool
    def query_order_detail(orderNo: str) -> str:
        """查询订单详情

        Args:
            orderNo: 订单号

        Returns:
            订单详情JSON字符串
        """
        resp = requests.post(
            f"{base_url}/tools/order/query",
            json={"action": "query_order_detail", "params": {"orderNo": orderNo}},
            timeout=30
        )
        result = resp.json()
        if not result.get("success"):
            return f"查询失败：{result.get('message', '未知错误')}"
        return str(result.get("data", {}))

    @tool
    def query_order_statistics(
        userId: str,
        minAmount: Optional[float] = None,
        maxAmount: Optional[float] = None
    ) -> str:
        """查询用户订单统计

        Args:
            userId: 用户ID
            minAmount: 最小金额
            maxAmount: 最大金额

        Returns:
            订单统计信息（数量、总金额、平均金额）
        """
        params = {"userId": userId}
        if minAmount is not None:
            params["minAmount"] = minAmount
        if maxAmount is not None:
            params["maxAmount"] = maxAmount

        resp = requests.post(
            f"{base_url}/tools/order/query",
            json={"action": "query_order_statistics", "params": params},
            timeout=30
        )
        result = resp.json()
        if not result.get("success"):
            return f"查询失败：{result.get('message', '未知错误')}"
        return str(result.get("data", {}))

    return [query_order_list, query_order_detail, query_order_statistics]
```

- [ ] **Step 3: 创建 tools/user_tool.py - 用户工具**

```python
# agent/tools/user_tool.py
from langchain_core.tools import tool
import requests


def create_user_tools(base_url: str):
    """创建用户相关工具"""

    @tool
    def query_user_info(userId: str) -> str:
        """查询用户信息

        Args:
            userId: 用户ID

        Returns:
            用户信息JSON字符串
        """
        resp = requests.post(
            f"{base_url}/tools/user/query",
            json={"action": "query_user_info", "params": {"userId": userId}},
            timeout=30
        )
        result = resp.json()
        if not result.get("success"):
            return f"查询失败：{result.get('message', '未知错误')}"
        return str(result.get("data", {}))

    return [query_user_info]
```

- [ ] **Step 4: 创建 tools/inventory_tool.py - 库存工具**

```python
# agent/tools/inventory_tool.py
from langchain_core.tools import tool
import requests


def create_inventory_tools(base_url: str):
    """创建库存相关工具"""

    @tool
    def query_inventory(sku: str) -> str:
        """按SKU查询库存

        Args:
            sku: 商品SKU

        Returns:
            库存信息JSON字符串
        """
        resp = requests.post(
            f"{base_url}/tools/inventory/query",
            json={"action": "query_inventory", "params": {"sku": sku}},
            timeout=30
        )
        result = resp.json()
        if not result.get("success"):
            return f"查询失败：{result.get('message', '未知错误')}"
        return str(result.get("data", []))

    @tool
    def query_warehouse_stock(warehouse: str) -> str:
        """按仓库查询库存

        Args:
            warehouse: 仓库名称

        Returns:
            仓库库存列表JSON字符串
        """
        resp = requests.post(
            f"{base_url}/tools/inventory/query",
            json={"action": "query_warehouse_stock", "params": {"warehouse": warehouse}},
            timeout=30
        )
        result = resp.json()
        if not result.get("success"):
            return f"查询失败：{result.get('message', '未知错误')}"
        return str(result.get("data", []))

    return [query_inventory, query_warehouse_stock]
```

- [ ] **Step 5: 创建 tools/__init__.py - 工具工厂函数**

```python
# agent/tools/__init__.py
from typing import List
from langchain_core.tools import Tool


def create_all_tools(base_url: str) -> List[Tool]:
    """创建所有工具实例"""
    from .order_tool import create_order_tools
    from .user_tool import create_user_tools
    from .inventory_tool import create_inventory_tools

    tools = []
    tools.extend(create_order_tools(base_url))
    tools.extend(create_user_tools(base_url))
    tools.extend(create_inventory_tools(base_url))
    return tools


__all__ = ["create_all_tools"]
```

- [ ] **Step 6: 提交代码**

```bash
git add -A
git commit -m "feat: 添加 LangChain Tools - 使用 @tool 装饰器"
```

---

## Task 3: 创建 Memory 管理

**Files:**
- Create: `agent/memory/conversation_memory.py`

- [ ] **Step 1: 创建 memory/conversation_memory.py - 对话记忆管理**

```python
# agent/memory/conversation_memory.py
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage
from typing import Optional


class ConversationMemoryManager:
    """对话记忆管理器"""

    def __init__(self, max_token_limit: int = 2000):
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output",
            input_key="input",
            max_token_limit=max_token_limit
        )

    def add_user_message(self, message: str) -> None:
        """添加用户消息"""
        self.memory.chat_memory.add_user_message(HumanMessage(content=message))

    def add_ai_message(self, message: str) -> None:
        """添加 AI 消息"""
        self.memory.chat_memory.add_ai_message(AIMessage(content=message))

    def get_history(self) -> str:
        """获取格式化后的历史记录"""
        variables = self.memory.load_memory_variables({})
        messages = variables.get("chat_history", [])
        if not messages:
            return "无"
        return "\n".join([
            f"用户: {m.content if hasattr(m, 'content') else str(m)}"
            if isinstance(m, HumanMessage) else
            f"助手: {m.content if hasattr(m, 'content') else str(m)}"
            for m in messages
        ])

    def clear(self) -> None:
        """清空记忆"""
        self.memory.clear()

    def save_context(self, input_str: str, output_str: str) -> None:
        """保存对话上下文"""
        self.memory.save_context(
            {"input": input_str},
            {"output": output_str}
        )
```

- [ ] **Step 2: 提交代码**

```bash
git add -A
git commit -m "feat: 添加 ConversationMemoryManager"
```

---

## Task 4: 创建 Chains

**Files:**
- Create: `agent/chains/intent_chain.py`
- Create: `agent/chains/query_chain.py`
- Create: `agent/chains/chat_chain.py`
- Create: `agent/chains/orchestrator.py`

- [ ] **Step 1: 创建 chains/intent_chain.py - 意图识别链**

```python
# agent/chains/intent_chain.py
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from langchain_core.outputs import Generation
from schemas.intent import Intent
from prompts.intent_prompt import get_intent_prompt
from typing import Union


def create_intent_chain(llm):
    """创建意图识别链"""
    parser = PydanticOutputParser(pydantic_object=Intent)
    prompt = get_intent_prompt().partial(format_instructions=parser.get_format_instructions())

    chain = LLMChain(llm=llm, prompt=prompt, output_parser=parser)
    return chain


def parse_intent_result(result: Union[str, Generation, dict]) -> Intent:
    """解析意图识别结果"""
    if isinstance(result, dict):
        return result.get("intent", result.get("text", None))
    elif isinstance(result, Generation):
        return parser.parse(result.text)
    else:
        return result
```

- [ ] **Step 2: 创建 chains/query_chain.py - ReAct 查询链**

```python
# agent/chains/query_chain.py
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.tools import Tool
from typing import List
from prompts.query_prompt import get_query_prompt


def create_query_chain(llm, tools: List[Tool], memory):
    """创建 ReAct 查询链"""
    prompt = get_query_prompt()

    agent = create_react_agent(llm, tools, prompt)

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        max_iterations=5,
        early_stopping_method="generate",
        verbose=True
    )
    return executor
```

- [ ] **Step 3: 创建 chains/chat_chain.py - 闲聊链**

```python
# agent/chains/chat_chain.py
from langchain.chains import LLMChain
from prompts.chat_prompt import get_chat_prompt


def create_chat_chain(llm):
    """创建闲聊链"""
    prompt = get_chat_prompt()
    return LLMChain(llm=llm, prompt=prompt)
```

- [ ] **Step 4: 创建 chains/orchestrator.py - 编排器**

```python
# agent/chains/orchestrator.py
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Agent 编排器 - 统一调度各 Chain"""

    def __init__(
        self,
        intent_chain,
        query_chain,
        chat_chain,
        memory_manager
    ):
        self.intent_chain = intent_chain
        self.query_chain = query_chain
        self.chat_chain = chat_chain
        self.memory_manager = memory_manager

    def process(self, user_input: str, user_id: Optional[str] = None) -> str:
        """处理用户输入"""
        try:
            # 1. 意图识别
            intent_result = self.intent_chain.invoke({"user_input": user_input})

            # 提取 Intent 对象
            intent_obj = intent_result if hasattr(intent_result, 'intent') else None

            if intent_obj:
                intent_type = intent_obj.intent
                logger.info(f"识别意图: {intent_type}, 原因: {intent_obj.reason}")
            else:
                # 降级处理：默认按查询处理
                intent_type = "query"
                logger.warning(f"意图识别降级，默认按 query 处理")

            # 2. 路由分发
            if intent_type in ("query", "statistic"):
                response = self.query_chain.invoke({
                    "input": user_input,
                    "chat_history": self.memory_manager.get_history()
                })
                if isinstance(response, dict):
                    response = response.get("output", str(response))
            elif intent_type == "chat":
                response = self.chat_chain.invoke({
                    "input": user_input,
                    "chat_history": self.memory_manager.get_history()
                })
                if isinstance(response, dict):
                    response = response.get("text", str(response))
            else:
                response = "抱歉，我无法理解您的问题，请尝试重新描述。"

            # 3. 更新记忆
            self.memory_manager.add_user_message(user_input)
            self.memory_manager.add_ai_message(str(response))

            return str(response)

        except Exception as e:
            logger.error(f"处理用户输入失败: {e}")
            raise
```

- [ ] **Step 5: 提交代码**

```bash
git add -A
git commit -m "feat: 添加 Chains - IntentChain, QueryChain, ChatChain, Orchestrator"
```

---

## Task 5: 创建依赖注入和服务入口

**Files:**
- Create: `agent/dependencies.py`
- Modify: `agent/server.py`

- [ ] **Step 1: 创建 dependencies.py - 依赖注入**

```python
# agent/dependencies.py
from langchain_community.chat_models import ChatOpenAI
from config import get_settings
from chains.intent_chain import create_intent_chain
from chains.query_chain import create_query_chain
from chains.chat_chain import create_chat_chain
from chains.orchestrator import AgentOrchestrator
from memory.conversation_memory import ConversationMemoryManager
from tools import create_all_tools


def create_chat_model():
    """创建 Chat 模型（支持 DeepSeek 或 OpenAI 兼容接口）"""
    settings = get_settings()

    # 优先使用 langchain-deepseek
    try:
        from langchain_deepseek import ChatDeepSeek
        return ChatDeepSeek(
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            temperature=0.7
        )
    except ImportError:
        # 降级到 ChatOpenAI（兼容 DeepSeek API）
        return ChatOpenAI(
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            base_url=f"{settings.deepseek_base_url}/v1",
            temperature=0.7
        )


def initialize_dependencies():
    """初始化所有依赖并返回编排器"""
    settings = get_settings()

    # 1. 初始化 LLM
    llm = create_chat_model()

    # 2. 初始化 Memory
    memory_manager = ConversationMemoryManager(max_token_limit=settings.max_token_limit)

    # 3. 初始化 Tools
    tools = create_all_tools(settings.backend_url)

    # 4. 初始化 Chains
    intent_chain = create_intent_chain(llm)
    query_chain = create_query_chain(llm, tools, memory_manager.memory)
    chat_chain = create_chat_chain(llm)

    # 5. 创建 Orchestrator
    orchestrator = AgentOrchestrator(
        intent_chain=intent_chain,
        query_chain=query_chain,
        chat_chain=chat_chain,
        memory_manager=memory_manager
    )

    return orchestrator
```

- [ ] **Step 2: 重写 server.py - Flask 服务入口**

```python
# agent/server.py
import os
import logging
from flask import Flask, request, jsonify
from dependencies import initialize_dependencies

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 初始化全局编排器
logger.info("正在初始化 Agent...")
orchestrator = initialize_dependencies()
logger.info("Agent 初始化完成")


@app.route('/api/chat', methods=['POST'])
def chat():
    """处理用户对话请求"""
    data = request.json
    message = data.get('message', '')
    user_id = data.get('userId', None)

    if not message:
        return jsonify({'success': False, 'message': '消息不能为空'}), 400

    try:
        logger.info(f"收到请求: userId={user_id}, message={message[:50]}...")
        response = orchestrator.process(message, user_id=user_id)
        logger.info(f"返回响应: {str(response)[:50]}...")
        return jsonify({'success': True, 'response': response})
    except Exception as e:
        logger.error(f"处理失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/tools/reload', methods=['POST'])
def reload_tools():
    """重新加载工具"""
    try:
        # TODO: 实现工具热加载
        return jsonify({'success': True, 'message': '工具已重新加载'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'type': 'LangChain Agent'
    })


if __name__ == '__main__':
    from config import get_settings
    settings = get_settings()
    app.run(
        host='0.0.0.0',
        port=settings.agent_port,
        debug=True
    )
```

- [ ] **Step 3: 提交代码**

```bash
git add -A
git commit -m "feat: 添加 dependencies.py 和重写 server.py"
```

---

## Task 6: 端到端测试

**Files:**
- Test: 手动测试

- [ ] **Step 1: 安装依赖**

```bash
cd agent
pip install -r requirements.txt
# 额外安装 langchain-deepseek（如需要）
pip install langchain-deepseek
```

- [ ] **Step 2: 配置环境变量**

创建 `agent/.env` 文件：
```bash
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
BACKEND_URL=http://localhost:8080
PORT=5001
```

- [ ] **Step 3: 启动后端服务**

```bash
cd backend
mvn spring-boot:run
```

- [ ] **Step 4: 启动 Agent 服务**

```bash
cd agent
python -m agent.server
# 或直接运行
python server.py
```

- [ ] **Step 5: 测试 API**

```bash
# 健康检查
curl http://localhost:5001/api/health

# 测试闲聊
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好", "userId": "U001"}'

# 测试查询
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "查询U001的订单", "userId": "U001"}'
```

- [ ] **Step 6: 提交测试结果**

```bash
git add -A
git commit -m "test: 完成端到端测试"
```

---

## 依赖关系图

```
Task 1 (基础设施)
    ├── schemas/intent.py
    ├── prompts/*.py
    └── config.py
          │
          ▼
Task 2 (Tools) ─────────────────────────────────────┐
    ├── tools/order_tool.py                         │
    ├── tools/user_tool.py                          │
    └── tools/inventory_tool.py                     │
          │                                          │
          ▼                                          │
Task 3 (Memory) ◄───────────────────────────────────┤
    └── memory/conversation_memory.py               │
          │                                          │
          ▼                                          │
Task 4 (Chains) ────────────────────────────────────┤
    ├── chains/intent_chain.py                      │
    ├── chains/query_chain.py                       │
    ├── chains/chat_chain.py                        │
    └── chains/orchestrator.py                      │
          │                                          │
          ▼                                          │
Task 5 (服务入口) ◄──────────────────────────────────┘
    ├── dependencies.py
    └── server.py
          │
          ▼
Task 6 (端到端测试)
```

---

## 验证清单

- [ ] `python -c "from agent.config import get_settings; print('config OK')"`
- [ ] `python -c "from agent.schemas.intent import Intent; print('schema OK')"`
- [ ] `python -c "from agent.tools import create_all_tools; print('tools OK')"`
- [ ] `python -c "from agent.memory import ConversationMemoryManager; print('memory OK')"`
- [ ] `python -c "from agent.chains import create_intent_chain; print('chains OK')"`
- [ ] `curl http://localhost:5001/api/health` 返回 `{"status": "ok"}`
- [ ] POST `/api/chat` with `{"message": "你好"}` 返回成功响应
- [ ] POST `/api/chat` with `{"message": "查询U001的订单"}` 能正确调用工具

---

**Plan complete.** 实施建议分 6 个 Task 顺序执行，每个 Task 完成后验证通过再进行下一个。
