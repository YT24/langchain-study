# AI Agent 系统总结文档

## 1. 项目概述

本项目是一个基于 Langchain 框架的 AI Agent 系统，用于实现智能业务查询助手。系统通过意图识别、工具调用和 RAG（检索增强生成）技术，为用户提供订单、用户、库存等业务数据的智能查询服务。

**技术栈：**
- Python 3.x
- Flask 3.0.0（API 服务）
- LangChain >= 0.1.0（核心框架）
- ChromaDB >= 0.4.0（向量数据库）
- DeepSeek API（LLM 支持）

---

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Flask API Server                        │
│  /api/chat  │  /api/tools/reload  │  /api/health            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    ReActAgent / AgentCore                    │
│  ┌─────────┐  ┌─────────────┐  ┌──────────────┐            │
│  │ Router  │  │ContextBuilder│  │ToolExecutor  │            │
│  └─────────┘  └─────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐  ┌───────────────┐  ┌───────────────┐
│  ToolRAG        │  │KnowledgeRAG  │  │MemoryManager  │
│  (工具描述管理)  │  │(业务知识管理) │  │(记忆管理)     │
└─────────────────┘  └───────────────┘  └───────────────┘
                              │
                              ▼
          ┌───────────────────────────────────┐
          │      Backend API (localhost:8080) │
          │  OrderTool │ UserTool │ InventoryTool │
          └───────────────────────────────────┘
```

---

## 3. 核心模块

### 3.1 Agent 核心 (`agent/core/agent.py`)

| 类 | 说明 |
|---|---|
| `AgentCore` | 标准 Agent 引擎，处理用户对话、意图识别、工具调用 |
| `ReActAgent` | 基于 ReAct 模式的 Agent，支持多轮推理迭代（默认3轮） |

**核心流程：**
1. 意图识别（Router.classify）
2. 构建上下文（Tools + Knowledge + Memory + History）
3. 路由分发（Chat / Tool Call）
4. 更新记忆

### 3.2 意图路由 (`agent/core/router.py`)

| 意图类型 | 说明 | 触发场景 |
|---|---|---|
| `QUERY` | 查询具体数据 | 查询订单、用户、库存 |
| `STATISTIC` | 统计汇总 | 计算总金额、数量、平均值 |
| `CHAT` | 一般对话 | 问候、闲聊 |
| `UNKNOWN` | 无法理解 | - |

**路由策略：**
- 有 DeepSeek API Key：使用 LLM 进行意图分类
- 无 API Key：基于规则的关键词匹配

### 3.3 上下文构建 (`agent/core/context_builder.py`)

负责构建 LLM 所需的完整 Prompt，包含：
- 系统提示词
- 可用工具描述
- 业务知识
- 记忆上下文
- 对话历史

### 3.4 工具执行器 (`agent/core/tool_executor.py`)

`SyncToolExecutor` 类负责：
- 从后端动态加载可用工具列表
- 注册 Python 工具类（OrderTool、UserTool、InventoryTool）
- 执行工具调用并记录日志
- 异常处理与结果封装

---

## 4. RAG 模块

### 4.1 ToolRAG (`agent/rag/tool_rag.py`)

工具描述管理，提供：
- 从后端 `/tools` 接口加载工具描述
- 解析 actions、params 等工具元数据
- 构建可供 LLM 理解的工具说明文本

### 4.2 KnowledgeRAG (`agent/rag/knowledge_rag.py`)

业务知识管理，内置知识包括：
- 订单状态：`pending`、`paid`、`shipped`、`completed`、`cancelled`
- 会员等级：`normal`、`silver`、`gold`、`vip`
- 查询参数说明：金额范围、日期范围等

---

## 5. 记忆管理 (`agent/memory/memory_manager.py`)

| 类 | 说明 |
|---|---|
| `MemoryManager` | 短期记忆管理器，基于 `deque` 实现，支持设置最大容量 |
| `WorkingMemory` | 工作记忆，存储当前任务的工具调用状态 |
| `Turn` | 对话轮次，记录用户输入、助手响应、工具调用 |

---

## 6. 业务工具 (`agent/tools/`)

### 6.1 OrderTool (`order_tool.py`)

| Action | 说明 | 参数 |
|---|---|---|
| `query_order_list` | 查询订单列表 | `userId`, `status`, `minAmount`, `maxAmount`, `startDate`, `endDate` |
| `query_order_detail` | 查询订单详情 | `orderNo` |
| `query_order_statistics` | 查询订单统计 | `userId`, `minAmount`, `maxAmount` |

### 6.2 UserTool (`user_tool.py`)

| Action | 说明 | 参数 |
|---|---|---|
| `query_user_info` | 查询用户信息 | `userId` |

### 6.3 InventoryTool (`inventory_tool.py`)

| Action | 说明 | 参数 |
|---|---|---|
| `query_inventory` | 按 SKU 查询库存 | `sku` |
| `query_warehouse_stock` | 按仓库查询库存 | `warehouse` |

---

## 7. API 接口 (`agent/server.py`)

| 端点 | 方法 | 说明 |
|---|---|---|
| `/api/chat` | POST | 处理用户对话请求 |
| `/api/tools/reload` | POST | 重新加载工具 |
| `/api/health` | GET | 健康检查 |

**Chat 接口请求格式：**
```json
{
  "message": "用户问题",
  "userId": "U001",
  "sessionId": "session_123"
}
```

**响应格式：**
```json
{
  "success": true,
  "response": "Agent 回复内容"
}
```

---

## 8. 配置与依赖

### 8.1 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | - |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | `https://api.deepseek.com` |
| `BACKEND_URL` | 后端服务地址 | `http://localhost:8080` |
| `PORT` | Flask 服务端口 | `5001` |

### 8.2 依赖 (`requirements.txt`)

```
requests==2.31.0
flask==3.0.0
langchain>=0.1.0
chromadb>=0.4.0
```

---

## 9. 关键设计

### 9.1 ReAct 模式

ReActAgent 在 `_handle_tool_call` 中实现多轮推理：
- 迭代次数：默认 3 次
- 每轮包含：分析 → 工具调用 → 结果处理
- 若 LLM 返回 `tool: null`，表示已有足够信息，直接返回分析结果

### 9.2 工具动态加载

ToolExecutor 在初始化时：
1. 调用后端 `/tools` 接口获取可用工具列表
2. 根据 `enabled` 标志动态注册对应的 Python 工具类
3. 支持运行时通过 `/api/tools/reload` 刷新工具列表

### 9.3 会话管理

MemoryManager 以 `session_id` 为键管理多会话：
- 短期记忆：基于 `deque`，默认最多 20 轮
- 支持 `user_id` 关联
- `get_recent_context(k)` 获取最近 k 轮对话

---

## 10. Git 提交历史

| Commit | 说明 |
|---|---|
| `5cf1df8` | 配置文件修改 |
| `dab7a25` | fix: 完善 ReAct Agent 推理流程与动态工具加载 |
| `2ffaaf7` | feat: 完成 AI Agent 系统架构 |

---

## 11. 启动方式

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export DEEPSEEK_API_KEY="your-api-key"
export BACKEND_URL="http://localhost:8080"

# 启动服务
python -m agent.server
```

服务默认运行在 `http://0.0.0.0:5001`
