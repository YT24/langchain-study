# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

本项目是一个基于 LangChain 的 AI Agent 系统，用于智能业务查询助手，包含三个主要模块：

- **Agent** (Python/Flask) - AI 意图识别、工具调用、RAG 检索
- **Backend** (Java/Spring Boot) - 业务 API 服务
- **Frontend** (React/Vite) - 用户界面

## 常用命令

### Agent (Python)

```bash
# 安装依赖
cd agent
pip install -r requirements.txt

# 启动服务（模块方式）
cd E:/AI_PROJECT/langchain-study
python -m agent.server

# 环境变量
DEEPSEEK_API_KEY=your-key
BACKEND_URL=http://localhost:8080
PORT=5001
```

### Backend (Java)

```bash
cd backend
mvn spring-boot:run
# 默认端口 8080
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 架构设计

### 系统架构

```
┌─────────────────────────────────────┐
│         Flask API (:5001)           │
│    /api/chat  │  /api/tools/reload │
└─────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
┌─────────┐   ┌─────────┐   ┌─────────────┐
│ ReAct   │   │ ToolRAG │   │MemoryManager│
│ Agent   │   │(工具检索)│   │  (记忆管理) │
└─────────┘   └─────────┘   └─────────────┘
                    │
                    ▼
┌─────────────────────────────────────┐
│     Spring Boot Backend (:8080)     │
│  OrderTool │ UserTool │ Inventory  │
└─────────────────────────────────────┘
```

### Agent 核心模块 (agent/agent/core/)

| 文件 | 职责 |
|------|------|
| `agent.py` | AgentCore/ReActAgent 主引擎，意图识别 → 工具调用流程 |
| `router.py` | 意图分类：QUERY/STATISTIC/CHAT/UNKNOWN |
| `context_builder.py` | 构建 LLM Prompt（工具 + 知识 + 记忆） |
| `tool_executor.py` | 动态加载后端工具、执行调用 |

### RAG 模块 (agent/agent/rag/)

| 文件 | 职责 |
|------|------|
| `tool_rag.py` | 从后端 `/tools` 加载工具描述，构建向量索引 |
| `knowledge_rag.py` | 内置业务知识（订单状态、会员等级等） |

### 记忆模块 (agent/agent/memory/)

- `MemoryManager` - 多会话短期记忆管理
- `WorkingMemory` - 当前任务工具调用状态

### 业务工具 (agent/agent/tools/)

- `OrderTool` - 订单查询、统计
- `UserTool` - 用户信息查询
- `InventoryTool` - 库存查询

## 启动配置

### PyCharm 配置（模块方式）

| 配置项 | 值 |
|--------|-----|
| Script path | `E:\Python312\python.exe` |
| Parameters | `-m agent.server` |
| Working directory | `E:\AI_PROJECT\langchain-study` |

### 目录结构注意

当前 `agent/` 目录下存在嵌套的 `agent/agent/` 结构（由历史文件移动操作导致）。所有 Python 导入使用绝对路径：

```python
from agent.core.agent import ReActAgent
from agent.rag.tool_rag import init_tool_rag_from_backend
```

## 外部依赖

- **LLM**: DeepSeek API (对话/意图分类)
- **Embedding**: HuggingFace BGE 模型 (`BAAI/bge-small-zh-v1.5`)
- **向量数据库**: ChromaDB (本地持久化)
- **后端 API**: Spring Boot (localhost:8080)

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | 必填 |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | `https://api.deepseek.com` |
| `BACKEND_URL` | 后端服务地址 | `http://localhost:8080` |
| `PORT` | Agent 服务端口 | `5001` |
