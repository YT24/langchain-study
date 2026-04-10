# AI Agent 工具动态管理设计

## 1. 概述

- **目标**：将工具定义存储到 MySQL，实现动态管理、集中配置、调用日志
- **范围**：Python Agent + Java Spring Boot 统一从数据库加载工具

## 2. 架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Python     │────▶│   MySQL     │◀────│  Java       │
│  Agent      │     │  (tools +   │     │  Spring Boot│
│             │◀────│   logs)     │◀────│  (reload)   │
└─────────────┘     └─────────────┘     └─────────────┘
```

## 3. 数据库设计

### 3.1 tools 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| name | VARCHAR(64) | 工具名（如 OrderTool） |
| description | TEXT | 工具描述 |
| actions | JSON | action 列表（包含参数定义） |
| enabled | BOOLEAN | 是否启用 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 3.2 tool_logs 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| tool_name | VARCHAR(64) | 工具名 |
| action | VARCHAR(64) | action 名称 |
| params | JSON | 调用参数 |
| result | TEXT | 响应结果 |
| duration_ms | INT | 耗时（毫秒） |
| called_at | DATETIME | 调用时间 |

## 4. API 设计

| 端点 | 方法 | 功能 |
|------|------|------|
| `GET /api/tools` | GET | 获取所有启用的工具 |
| `POST /api/tools` | POST | 添加工具 |
| `PUT /api/tools/{id}` | PUT | 更新工具 |
| `DELETE /api/tools/{id}` | DELETE | 删除工具 |
| `POST /api/tools/{id}/enable` | POST | 启用工具 |
| `POST /api/tools/{id}/disable` | POST | 禁用工具 |

## 5. 工具定义 JSON 格式

```json
{
  "name": "OrderTool",
  "description": "订单查询工具",
  "actions": [
    {
      "name": "query_order_list",
      "description": "查询用户订单列表",
      "params": {
        "userId": {"type": "string", "required": true},
        "status": {"type": "string", "required": false}
      }
    }
  ]
}
```

## 6. 工作流程

1. **服务启动** → Java/Python 从 `/api/tools` 加载 enabled=true 的工具
2. **动态启用/禁用** → 调用 `/api/tools/{id}/enable|disable`，下次加载生效
3. **调用时** → 自动记录日志到 `tool_logs` 表

## 7. 实现计划

### Phase 1: 数据库
- 创建 tools 表、tool_logs 表
- 初始化现有工具数据（OrderTool, UserTool, InventoryTool）

### Phase 2: Java 后端
- 创建 Tool entity, ToolLog entity
- 创建 ToolRepository, ToolLogRepository
- 创建 ToolService（含加载/启用/禁用逻辑）
- 创建 ToolController
- 启动时加载工具到内存

### Phase 3: Python Agent
- 创建 ToolLoader 从 API 加载工具
- 修改 Agent 类支持动态工具
- 添加工具调用日志记录
