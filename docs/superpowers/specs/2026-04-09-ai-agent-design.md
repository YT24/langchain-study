# AI Agent 业务对象查询系统设计

## 1. 概述

- **项目名称**：AI Agent 业务对象查询系统
- **项目目标**：通过自然语言对话，AI Agent 识别用户意图，调用 Java 微服务查询订单、用户、库存等业务数据
- **技术栈**：React + Python Agent + Java Spring Boot + MySQL + MiniMax LLM
- **并发规模**：100-1000 用户

## 2. 系统架构

```
┌─────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  React  │──▶│  Python     │──▶│  Java       │──▶│  Database   │
│  前端   │◀──│  Agent      │◀──│  Spring Boot │◀──│  (MySQL)    │
└─────────┘   └──────┬──────┘   └─────────────┘   └─────────────┘
                     │
               ┌─────┴─────┐
               │  MiniMax  │
               │  LLM API  │
               └───────────┘
```

## 3. 技术选型

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | React | SPA 对话界面 |
| Agent | Python + LangChain | 意图识别 + Tool 调度 |
| 后端 | Java Spring Boot | REST API |
| 数据库 | MySQL | 业务数据存储 |
| 连接池 | HikariCP | maxPool=50 |
| LLM | MiniMax | 自然语言理解 |

## 4. 项目结构

```
langchain-study/
├── frontend/          # React 项目
│   └── src/
│       ├── components/
│       │   └── ChatInterface.jsx
│       ├── services/
│       │   └── api.js
│       └── App.jsx
│
├── agent/             # Python Agent 项目
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── order_tool.py
│   │   │   ├── user_tool.py
│   │   │   └── inventory_tool.py
│   │   └── prompts.py
│   └── requirements.txt
│
└── backend/          # Java Spring Boot 项目
    └── src/main/java/com/example/
        ├── controller/
        │   └── ToolController.java
        ├── service/
        │   ├── OrderService.java
        │   ├── UserService.java
        │   └── InventoryService.java
        └── mapper/
            ├── OrderMapper.java
            ├── UserMapper.java
            └── InventoryMapper.java
```

## 5. 接口设计

### 5.1 Agent 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `POST /api/chat` | POST | 发送对话消息 |

**请求：**
```json
{
  "message": "帮我查一下用户 U001 的所有订单"
}
```

**响应：**
```json
{
  "success": true,
  "response": "用户 U001 共有 3 个订单..."
}
```

### 5.2 Tool API (Java Spring Boot)

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/tools/order/query` | POST | 查询订单 |
| `/api/tools/user/query` | POST | 查询用户 |
| `/api/tools/inventory/query` | POST | 查询库存 |

**请求格式：**
```json
{
  "action": "query_order_list",
  "params": {
    "userId": "U001",
    "status": "pending"
  }
}
```

**响应格式：**
```json
{
  "success": true,
  "data": [...],
  "message": "查询成功"
}
```

## 6. 数据库设计

### 6.1 订单表 (orders)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| order_no | VARCHAR(32) | 订单号 |
| user_id | VARCHAR(32) | 用户ID |
| status | VARCHAR(20) | 订单状态 |
| total_amount | DECIMAL(10,2) | 订单金额 |
| created_at | DATETIME | 创建时间 |

### 6.2 用户表 (users)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| user_id | VARCHAR(32) | 用户ID |
| name | VARCHAR(64) | 姓名 |
| phone | VARCHAR(20) | 手机号 |
| level | VARCHAR(20) | 会员等级 |
| balance | DECIMAL(10,2) | 账户余额 |
| created_at | DATETIME | 创建时间 |

### 6.3 库存表 (inventory)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| sku | VARCHAR(32) | 商品SKU |
| warehouse | VARCHAR(32) | 仓库 |
| quantity | INT | 库存数量 |
| updated_at | DATETIME | 更新时间 |

## 7. Tool 定义

### 7.1 OrderTool

- **action**: query_order_list — 按用户/状态查询订单列表
- **action**: query_order_detail — 按订单号查询订单详情

### 7.2 UserTool

- **action**: query_user_info — 按用户ID查询用户信息
- **action**: query_user_balance — 查询用户余额

### 7.3 InventoryTool

- **action**: query_inventory — 按SKU查询库存
- **action**: query_warehouse_stock — 按仓库查询库存

## 8. Agent 工作流程

1. 用户输入自然语言
2. Python Agent 接收消息
3. Agent 将消息 + Tool 描述发送给 MiniMax
4. MiniMax 返回应调用的 Tool 名称和参数
5. Agent 解析结果，调用对应 Tool（HTTP 请求到 Java 服务）
6. Java 服务查询数据库返回结构化数据
7. Agent 将结构化数据转换为自然语言
8. 返回最终回复给前端

## 9. 错误处理

- Java 服务返回标准错误码（401 参数错误、500 服务异常）
- Agent 统一处理重试逻辑
- 不可恢复错误返回友好提示，支持转人工

## 10. 后续迭代

- **缓存层**：Redis/Caffeine 缓存热点查询
- **流式响应**：SSE 支持长查询实时展示
- **日志审计**：记录所有查询请求和响应
