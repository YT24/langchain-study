# LangChain Agent 系统重构设计方案

**日期**: 2026-04-15
**版本**: v1.0
**状态**: 待评审

---

## 1. 背景与目标

### 1.1 当前问题

当前 AI Agent 系统存在以下问题：

| 问题 | 现状 | 影响 |
|------|------|------|
| LLM 调用 | 直接 `requests.post` | 代码重复、错误处理不一致 |
| 工具定义 | 自定义类 + JSON 解析 | 维护困难、类型不安全 |
| Prompt 管理 | 手写字符串拼接 | 难以复用和测试 |
| Agent 实现 | 自定义 ReAct 逻辑 | 代码复杂、难以扩展 |
| 输出解析 | 字符串解析 | 脆弱、容易出错 |

### 1.2 重构目标

- **简化代码**: 利用 LangChain 抽象减少重复代码
- **增强能力**: 支持 Streaming、Callbacks、多轮对话
- **可维护性**: 模块化设计、类型安全、便于测试

---

## 2. 技术选型

### 2.1 核心框架

- **LangChain**: 0.1.x 稳定版
- **Python**: 3.10+

### 2.2 组件选型

| 组件 | 技术方案 | 说明 |
|------|---------|------|
| LLM | `langchain-deepseek` 或 `ChatDeepSeek` | DeepSeek API |
| Agent | `create_react_agent` | LangChain 标准 ReAct |
| Tools | `@tool` 装饰器 | LangChain Tools |
| Memory | `ConversationBufferMemory` | 对话记忆 |
| Prompt | `PromptTemplate` | 模板管理 |
| Output Parser | `PydanticOutputParser` | 类型安全输出 |

### 2.3 外部依赖

- **向量数据库**: ChromaDB（保留现有）
- **Embedding**: HuggingFace BGE 模型
- **后端 API**: Spring Boot（localhost:8080）

---

## 3. 系统架构

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Flask API Server                        │
│              POST /api/chat  │  POST /api/tools/reload      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent Orchestrator                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ IntentChain  │→ │ QueryChain   │  │   ChatChain       │ │
│  │ (LLM分类)    │  │ (ReAct Agent)│  │  (简单对话)      │ │
│  └──────────────┘  └──────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐  ┌───────────────┐  ┌───────────────┐
│  ToolRAG       │  │ LangChain    │  │   Memory      │
│  (工具描述检索) │  │ Tools        │  │ (BufferMemory)│
└─────────────────┘  └───────────────┘  └───────────────┘
                              │
                              ▼
          ┌───────────────────────────────────┐
          │      Backend API (:8080)           │
          │  /tools/order/query               │
          │  /tools/user/query                │
          │  /tools/inventory/query          │
          └───────────────────────────────────┘
```

### 3.2 目录结构

```
agent/
├── __init__.py
├── server.py                    # Flask 入口
├── config.py                   # 配置管理
├── dependencies.py             # 依赖注入（LLM、Tools 初始化）
│
├── chains/                     # Chain 定义
│   ├── __init__.py
│   ├── intent_chain.py         # 意图识别链
│   ├── query_chain.py          # 工具查询链 (ReAct)
│   ├── chat_chain.py           # 闲聊链
│   └── factory.py              # Chain 工厂
│
├── tools/                      # LangChain Tools
│   ├── __init__.py
│   ├── base.py                 # 基础 Tool 类
│   ├── order_tool.py           # 订单工具
│   ├── user_tool.py            # 用户工具
│   └── inventory_tool.py       # 库存工具
│
├── memory/                     # LangChain Memory
│   ├── __init__.py
│   └── conversation_memory.py   # 对话记忆管理
│
├── prompts/                    # Prompt 模板
│   ├── __init__.py
│   ├── intent_prompt.py        # 意图识别 Prompt
│   ├── query_prompt.py         # 查询 Agent Prompt
│   └── chat_prompt.py          # 闲聊 Prompt
│
├── schemas/                    # Pydantic 数据模型
│   ├── __init__.py
│   ├── intent.py               # 意图识别数据模型
│   └── tool_result.py          # 工具结果数据模型
│
└── utils/                      # 工具函数
    ├── __init__.py
    └── output_parser.py        # 输出解析器
```

---

## 4. 核心模块设计

### 4.1 配置管理 (`config.py`)

```python
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

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### 4.2 IntentChain（意图识别链）

**设计思路**: 使用 Pydantic + OutputParser 实现类型安全的意图分类

```python
# schemas/intent.py
from pydantic import BaseModel, Field
from typing import Literal

class Intent(BaseModel):
    intent: Literal["query", "statistic", "chat", "unknown"] = Field(
        description="用户意图：query=查询数据, statistic=统计汇总, chat=闲聊, unknown=无法理解"
    )
    reason: str = Field(description="判断理由")

# chains/intent_chain.py
from langchain_deepseek import ChatDeepSeek
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.chains import LLMChain

def create_intent_chain(llm: ChatDeepSeek):
    parser = PydanticOutputParser(pydantic_object=Intent)

    prompt = PromptTemplate.from_template(
        """你是一个意图分类器。用户输入后，判断用户的意图：

可选意图：
- query: 需要查询具体数据（订单、用户、库存）
- statistic: 需要统计汇总（金额、数量、平均值）
- chat: 一般对话、问候、闲聊
- unknown: 完全无法理解

用户输入：{user_input}

{format_instructions}

返回格式（只返回JSON，不要其他内容）："""
    ).partial(format_instructions="{format_instructions}")

    chain = LLMChain(llm=llm, prompt=prompt, output_parser=parser)
    return chain
```

### 4.3 QueryChain（ReAct 查询链）

**设计思路**: 使用 LangChain 标准 `create_react_agent`，工具作为 Tool 实例传入

```python
# chains/query_chain.py
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.agents import AgentExecutor
from langchain_core.tools import Tool
from typing import List

def create_query_chain(llm, tools: List[Tool], memory):
    prompt = PromptTemplate.from_template(
        """你是一个智能助手，可以调用工具来回答用户问题。

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
    )

    agent = create_react_agent(llm, tools, prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        max_iterations=5,
        early_stopping_method="generate"
    )
    return executor
```

### 4.4 ChatChain（闲聊链）

**设计思路**: 使用简单 LLMChain，结合历史记忆

```python
# chains/chat_chain.py
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

CHAT_TEMPLATE = """你是一个小助手，友善地回答用户问题。

历史对话：
{chat_history}

当前用户：{input}
助手："""

def create_chat_chain(llm):
    prompt = PromptTemplate.from_template(CHAT_TEMPLATE)
    return LLMChain(llm=llm, prompt=prompt)
```

### 4.5 Tool 定义（使用 @tool 装饰器）

```python
# tools/order_tool.py
from langchain_core.tools import tool
from typing import Optional, List, Dict
import requests

def create_order_tool(base_url: str) -> tool:
    @tool
    def query_order_list(
        userId: str,
        status: Optional[str] = None,
        minAmount: Optional[float] = None,
        maxAmount: Optional[float] = None
    ) -> str:
        """查询用户订单列表

        Args:
            userId: 用户ID
            status: 订单状态（pending/paid/shipped/completed/cancelled）
            minAmount: 最小金额
            maxAmount: 最大金额

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

    return query_order_list  # 返回单个 Tool 实例
```

### 4.6 Memory 管理

```python
# memory/conversation_memory.py
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage

class ConversationMemoryManager:
    def __init__(self, max_token_limit: int = 2000):
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output",
            input_key="input",
            max_token_limit=max_token_limit
        )

    def add_user_message(self, message: str):
        self.memory.chat_memory.add_user_message(HumanMessage(content=message))

    def add_ai_message(self, message: str):
        self.memory.chat_memory.add_ai_message(AIMessage(content=message))

    def get_history(self) -> str:
        return self.memory.load_memory_variables({})["chat_history"]

    def clear(self):
        self.memory.clear()
```

### 4.7 Orchestrator（编排器）

```python
# chains/orchestrator.py
from typing import Tuple

class AgentOrchestrator:
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
        self.memory = memory_manager

    def process(self, user_input: str, user_id: str = None) -> str:
        # 1. 意图识别
        intent_result = self.intent_chain.invoke({"user_input": user_input})
        intent = intent_result["intent"] if isinstance(intent_result, dict) else intent_result

        # 2. 路由分发
        if intent.intent in ("query", "statistic"):
            response = self.query_chain.invoke({
                "input": user_input,
                "chat_history": self.memory.get_history()
            })
        elif intent.intent == "chat":
            response = self.chat_chain.invoke({
                "input": user_input,
                "chat_history": self.memory.get_history()
            })
        else:
            response = "抱歉，我无法理解您的问题，请尝试重新描述。"

        # 3. 更新记忆
        self.memory.add_user_message(user_input)
        self.memory.add_ai_message(str(response))

        return response
```

---

## 5. 服务入口设计

### 5.1 Server (`server.py`)

```python
from flask import Flask, request, jsonify
from dependencies import initialize_dependencies

app = Flask(__name__)

# 初始化依赖
orchestrator = initialize_dependencies()

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    user_id = data.get('userId', None)

    if not message:
        return jsonify({'success': False, 'message': '消息不能为空'}), 400

    try:
        response = orchestrator.process(message, user_id=user_id)
        return jsonify({'success': True, 'response': response})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/tools/reload', methods=['POST'])
def reload_tools():
    """重新加载工具"""
    # 实现工具热加载逻辑
    return jsonify({'success': True, 'message': '工具已重新加载'})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    from config import get_settings
    settings = get_settings()
    app.run(host='0.0.0.0', port=settings.agent_port, debug=True)
```

### 5.2 依赖注入 (`dependencies.py`)

```python
from langchain_deepseek import ChatDeepSeek
from config import get_settings
from chains.intent_chain import create_intent_chain
from chains.query_chain import create_query_chain
from chains.chat_chain import create_chat_chain
from chains.orchestrator import AgentOrchestrator
from memory.conversation_memory import ConversationMemoryManager
from tools import create_all_tools

def initialize_dependencies():
    settings = get_settings()

    # 1. 初始化 LLM
    llm = ChatDeepSeek(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0.7
    )

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

---

## 6. 数据流

```
用户输入: "查询U001的订单"
         │
         ▼
┌─────────────────┐
│  IntentChain    │
│  LLM + Parser   │
└────────┬────────┘
         │
         ▼ "query"
┌─────────────────┐
│  QueryChain     │
│  (ReAct Agent) │
│                 │
│  ┌───────────┐  │
│  │ Tool Call │  │
│  │ OrderTool │  │
│  └───────────┘  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Memory       │
│  更新对话历史   │
└────────┬────────┘
         │
         ▼
      最终响应
```

---

## 7. 错误处理

### 7.1 分层错误处理

| 层次 | 错误类型 | 处理方式 |
|------|---------|---------|
| LLM | API 超时/限流 | 重试 + 降级 |
| Tool | 后端服务不可用 | 返回友好错误 |
| Chain | 执行异常 | 捕获 + 日志 + 用户提示 |
| Server | 请求异常 | HTTP 500 + 错误信息 |

### 7.2 Tool 错误处理

```python
@tool
def safe_tool_wrapper(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.Timeout:
            return "请求超时，请稍后重试"
        except requests.exceptions.ConnectionError:
            return "后端服务不可用"
        except Exception as e:
            return f"执行错误：{str(e)}"
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper
```

---

## 8. 扩展点

### 8.1 Streaming 支持

```python
# 在 AgentExecutor 中添加 streaming
query_chain = AgentExecutor(
    agent=agent,
    tools=tools,
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()]
)
```

### 8.2 回调机制

```python
from langchain_core.callbacks import BaseCallbackHandler

class CustomCallbackHandler(BaseCallbackHandler):
    def on_tool_start(self, serialized, inputs, **kwargs):
        print(f"开始执行工具: {serialized}")

    def on_tool_end(self, output, **kwargs):
        print(f"工具执行完成: {output}")
```

### 8.3 多租户支持

```python
# 每个用户独立的 Memory
def get_user_memory(user_id: str) -> ConversationBufferMemory:
    # 可使用 Redis 或数据库持久化
    return user_memories[user_id]
```

---

## 9. 迁移策略

### 9.1 阶段一：基础设施（1-2天）

- [ ] 创建新目录结构
- [ ] 实现 `config.py` 和 `dependencies.py`
- [ ] 实现 Pydantic Schemas
- [ ] 编写 Prompt 模板

### 9.2 阶段二：核心组件（2-3天）

- [ ] 重写 Tools（@tool 装饰器）
- [ ] 实现 IntentChain
- [ ] 实现 QueryChain (ReAct)
- [ ] 实现 ChatChain

### 9.3 阶段三：集成测试（1-2天）

- [ ] 实现 Memory 管理
- [ ] 实现 Orchestrator
- [ ] 迁移 Server 入口
- [ ] 端到端测试

### 9.4 阶段四：优化（1天）

- [ ] 添加 Streaming 支持
- [ ] 添加 Callbacks
- [ ] 性能优化

---

## 10. 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| LangChain 版本变更 | API 不兼容 | 使用 0.1.x 稳定版，锁定依赖 |
| LLM 输出不稳定 | 意图识别错误 | 增加重试 + 规则兜底 |
| 工具返回格式不一致 | 解析失败 | 统一 Tool 返回字符串格式 |
| 多轮对话记忆丢失 | 上下文不连贯 | 持久化 Memory |

---

## 11. 附录

### 11.1 依赖列表

```
langchain>=0.1.0,<0.2.0
langchain-core>=0.1.0,<0.2.0
langchain-community>=0.1.0,<0.2.0
langchain-deepseek>=0.1.0
pydantic>=2.0
pydantic-settings>=2.0
flask>=3.0.0
requests>=2.31.0
chromadb>=0.4.0
sentence-transformers>=2.0
```

### 11.2 环境变量

```bash
DEEPSEEK_API_KEY=sk-xxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
BACKEND_URL=http://localhost:8080
PORT=5001
```
