# AI Agent 系统技术文档

## 1. 系统概述

基于 LangChain + DeepSeek 的智能业务查询 Agent，支持意图识别、工具调用、RAG 增强检索。

**技术栈：**
- Python 3.x + Flask（API 服务）
- LangChain（LCEL 链式调用）
- ChromaDB（向量数据库）
- DeepSeek API（LLM）
- BGE Embedding（中文向量模型）

---

## 2. 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                     Flask API (:5001)                             │
│     /api/chat  │  /api/tools/reload  │  /api/health            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AgentOrchestrator                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │IntentChain  │  │ QueryChain   │  │ ChatChain            │   │
│  │(意图识别)    │  │(查询/统计)   │  │(闲聊)                │   │
│  └─────────────┘  └──────────────┘  └──────────────────────┘   │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  MemoryManager (对话记忆)                                 │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌───────────────┐  ┌─────────────────────┐
│    ToolRAG      │  │KnowledgeRAG  │  │ DynamicToolLoader   │
│  (向量工具检索)  │  │(业务知识检索) │  │ (动态加载后端工具)   │
└─────────────────┘  └───────────────┘  └─────────────────────┘
         │                    │
         ▼                    ▼
┌─────────────────────────────────────────┐
│         ChromaDB (.chroma/)             │
│   tool_descriptions │ business_knowledge │
└─────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────┐
│      Backend API (localhost:8080)       │
│   /tools/order/query  │  /tools/user   │
└─────────────────────────────────────────┘
```

---

## 3. 初始化流程

### 3.1 启动入口 (`server.py`)

```python
# 1. 配置日志
logging.basicConfig(...)

# 2. 初始化依赖
orchestrator = initialize_dependencies()

# 3. 启动 Flask
app.run(host='0.0.0.0', port=settings.agent_port)
```

### 3.2 依赖初始化 (`dependencies.py`)

```
initialize_dependencies()
│
├── 1. create_chat_model()
│   └── ChatOpenAI (DeepSeek)
│
├── 2. ConversationMemoryManager
│   └── max_token_limit: 2000
│
├── 3. create_all_tools()
│   ├── DynamicToolLoader.fetch_tool_definitions()
│   └── StructuredTool.from_function() × N
│
├── 4. get_embedding_model()
│   └── BAAI/bge-small-zh-v1.5 (512维)
│
├── 5. ToolRAG.load_tools()
│   └── ChromaDB: tool_descriptions collection
│
├── 6. KnowledgeRAG.load_knowledge()
│   └── ChromaDB: business_knowledge collection
│
├── 7. create_intent_chain()
│   └── prompt | llm | JsonOutputParser
│
├── 8. create_query_chain()
│   └── prompt | llm | StrOutputParser
│
├── 9. create_chat_chain()
│   └── prompt | llm | StrOutputParser
│
└── 10. AgentOrchestrator
    ├── set_tools()
    ├── set_tool_rag()
    └── set_knowledge_rag()
```

---

## 4. 执行流程

### 4.1 用户请求处理

```
POST /api/chat
    │
    ▼
orchestrator.process(message, userId)
    │
    ├─ 1. 意图识别
    │   intent_chain.invoke({user_input})
    │   │
    │   └── 返回: Intent{intent: "query|statistic|chat|unknown"}
    │
    ├─ 2. 路由分发
    │   │
    │   ├─ [query/statistic] → QueryChain
    │   │   │
    │   │   ├─ _get_rag_context()
    │   │   │   ├── tool_rag.search() → 相关工具
    │   │   │   └── knowledge_rag.get_relevant_knowledge() → 业务知识
    │   │   │
    │   │   ├─ query_chain.invoke({input, chat_history, rag_context})
    │   │   │   └── LLM 返回 JSON: {need_tool, tool, params, answer}
    │   │   │
    │   │   ├─ _parse_llm_json()
    │   │   │
    │   │   └─ need_tool=true?
    │   │       │
    │   │       ├─ YES: _execute_tool()
    │   │       │   ├── _find_tool() (模糊匹配)
    │   │       │   ├── _normalize_params() (user_id ↔ userId)
    │   │       │   ├── tool.invoke() → 后端 API
    │   │       │   └── _polish_result() → LLM 润色
    │   │       │
    │   │       └─ NO: 返回 answer
    │   │
    │   └─ [chat] → ChatChain
    │       │
    │       └── chat_chain.invoke({input, chat_history})
    │
    └─ 3. 更新记忆
        │
        ├── memory_manager.add_user_message()
        └── memory_manager.add_ai_message()
```

### 4.2 详细步骤

#### 步骤 1: 意图识别
```python
intent_result = intent_chain.invoke({"user_input": user_input})
# LLM 返回: {"intent": "query", "reason": "用户查询订单数据"}
```

#### 步骤 2a: Query/Statistic 流程
```python
# RAG 检索
rag_context = _get_rag_context(user_input)
# 返回:
# 【相关工具】（按相似度排序）：
#   - query_order_list: 查询订单列表 (匹配度: 0.85)
#
# 【相关业务知识】：
#   订单状态：pending(待处理), shipped(已发货)...

# 调用 QueryChain
raw_response = query_chain.invoke({
    "input": user_input,
    "chat_history": memory,
    "rag_context": rag_context
})
# LLM 返回 JSON:
# {"need_tool": true, "tool": "query_order_list", "params": {"userId": "U001"}}
```

#### 步骤 2b: 工具执行
```python
# 执行工具
tool_result = _execute_tool("query_order_list", {"userId": "U001"})
# 1. _find_tool() - 模糊匹配工具名
# 2. _normalize_params() - 参数名规范化
# 3. tool.invoke() - 调用后端 API
# 4. _polish_result() - LLM 润色结果
```

#### 步骤 3: 更新记忆
```python
memory_manager.add_user_message(user_input)
memory_manager.add_ai_message(response)
```

---

## 5. 模块说明

### 5.1 配置 (`config/`)

| 文件 | 说明 |
|------|------|
| `settings.yml` | 主配置（LLM、Backend、Agent、Memory）|
| `rag.yml` | RAG 配置（Embedding、ChromaDB、检索阈值）|
| `tools.yml` | 工具配置（HTTP 超时）|
| `prompts.yml` | Prompt 模板 |
| `loader.py` | YAML 配置加载器 |

### 5.2 Chains (`chains/`)

| 文件 | 说明 |
|------|------|
| `orchestrator.py` | Agent 编排器，统一调度 |
| `intent_chain.py` | 意图识别链 |
| `query_chain.py` | 查询/统计链 |
| `chat_chain.py` | 闲聊链 |

### 5.3 RAG (`rag/`)

| 文件 | 说明 |
|------|------|
| `embeddings.py` | Embedding 模型管理（BGE + OpenAI fallback）|
| `tool_rag.py` | 工具向量检索 |
| `knowledge_rag.py` | 业务知识检索 |

### 5.4 工具 (`tools/`)

| 文件 | 说明 |
|------|------|
| `dynamic_loader.py` | 动态工具加载器 |
| `base.py` | 工具基类 |
| `order_tool.py` | 订单工具（备用）|
| `user_tool.py` | 用户工具（备用）|
| `inventory_tool.py` | 库存工具（备用）|

---

## 6. API 接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/chat` | POST | 处理对话请求 |
| `/api/tools/reload` | POST | 重新加载工具 |
| `/api/health` | GET | 健康检查 |

### Chat 请求格式
```json
{
  "message": "帮我查一下 U001 的订单",
  "userId": "U001"
}
```

### 响应格式
```json
{
  "success": true,
  "response": "好的，我已经为您查到..."
}
```

---

## 7. 配置项

### settings.yml
```yaml
deepseek:
  api_key: "${DEEPSEEK_API_KEY}"
  base_url: "https://api.deepseek.com"
  model: "deepseek-chat"
  temperature: 0.7

backend:
  url: "http://localhost:8080"
  timeout: 30

agent:
  port: 5001

memory:
  max_token_limit: 2000
```

### rag.yml
```yaml
embedding:
  model: "BAAI/bge-small-zh-v1.5"
  dimension: 512
  cache_dir: ".hf_cache"

chroma:
  persist_directory: ".chroma"

retrieval:
  tool_top_k: 3
  tool_similarity_threshold: 0.5
  knowledge_top_k: 3
  knowledge_similarity_threshold: 0.3
```

---

## 8. 启动方式

```bash
cd agent

# 设置环境变量
export DEEPSEEK_API_KEY="your-key"

# 启动服务
python server.py
```

服务运行在 `http://0.0.0.0:5001`
