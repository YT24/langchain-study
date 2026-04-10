# AI Agent 工具动态管理实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将工具定义存储到 MySQL，实现动态管理、集中配置、调用日志

**Architecture:** Python Agent + Java Spring Boot 统一从数据库加载工具定义，调用时记录日志

**Tech Stack:** Java Spring Boot + MySQL + Python Flask + DeepSeek LLM

---

## 文件结构

```
langchain-study/
├── database/
│   └── init.sql                    # 新增 tools, tool_logs 表
├── backend/src/main/java/com/example/agent/
│   ├── entity/
│   │   ├── Tool.java              # 新增
│   │   └── ToolLog.java           # 新增
│   ├── repository/
│   │   ├── ToolRepository.java    # 新增
│   │   └── ToolLogRepository.java  # 新增
│   ├── service/
│   │   └── ToolService.java       # 修改：新增CRUD + 加载逻辑
│   ├── controller/
│   │   └── ToolController.java    # 修改：新增管理API
│   └── config/
│       └── ToolInitializer.java   # 新增：启动时加载工具
└── agent/agent/
    ├── tool_loader.py             # 新增：从API加载工具
    ├── agent.py                   # 修改：支持动态工具 + 日志
    └── prompts.py                 # 修改：动态构建prompt
```

---

## Phase 1: 数据库

### Task 1: 创建数据库表和初始化数据

**Files:**
- Modify: `database/init.sql`

- [ ] **Step 1: 添加 tools 表**

```sql
CREATE TABLE IF NOT EXISTS tools (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(64) NOT NULL UNIQUE COMMENT '工具名',
    description TEXT COMMENT '工具描述',
    actions JSON NOT NULL COMMENT 'action列表',
    enabled BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_enabled (enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工具定义表';
```

- [ ] **Step 2: 添加 tool_logs 表**

```sql
CREATE TABLE IF NOT EXISTS tool_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tool_name VARCHAR(64) NOT NULL COMMENT '工具名',
    action VARCHAR(64) NOT NULL COMMENT 'action名称',
    params JSON COMMENT '调用参数',
    result TEXT COMMENT '响应结果',
    duration_ms INT COMMENT '耗时（毫秒）',
    called_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tool_name (tool_name),
    INDEX idx_called_at (called_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工具调用日志表';
```

- [ ] **Step 3: 插入初始工具数据**

```sql
INSERT INTO tools (name, description, actions, enabled) VALUES
('OrderTool', '订单查询工具', '{"actions":[{"name":"query_order_list","description":"查询用户订单列表","params":{"userId":{"type":"string","required":true},"status":{"type":"string","required":false}}},{"name":"query_order_detail","description":"查询订单详情","params":{"orderNo":{"type":"string","required":true}}}]}', TRUE),
('UserTool', '用户查询工具', '{"actions":[{"name":"query_user_info","description":"查询用户信息","params":{"userId":{"type":"string","required":true}}}]}', TRUE),
('InventoryTool', '库存查询工具', '{"actions":[{"name":"query_inventory","description":"按SKU查询库存","params":{"sku":{"type":"string","required":true}}},{"name":"query_warehouse_stock","description":"按仓库查询库存","params":{"warehouse":{"type":"string","required":true}}}]}', TRUE);
```

- [ ] **Step 4: 执行 SQL**

Run: `mysql -h localhost -P 3306 -u root -proot1234 fff < database/init.sql`

- [ ] **Step 5: 验证**

Run: `mysql -h localhost -P 3306 -u root -proot1234 fff -e "SELECT COUNT(*) FROM tools; SELECT COUNT(*) FROM tool_logs;"`
Expected: tools=3, tool_logs=0

---

## Phase 2: Java 后端

### Task 2: 创建实体类

**Files:**
- Create: `backend/src/main/java/com/example/agent/entity/Tool.java`
- Create: `backend/src/main/java/com/example/agent/entity/ToolLog.java`

- [ ] **Step 1: 创建 Tool.java**

```java
package com.example.agent.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class Tool {
    private Long id;
    private String name;
    private String description;
    private String actions;  // JSON string
    private Boolean enabled;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
```

- [ ] **Step 2: 创建 ToolLog.java**

```java
package com.example.agent.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class ToolLog {
    private Long id;
    private String toolName;
    private String action;
    private String params;   // JSON string
    private String result;
    private Integer durationMs;
    private LocalDateTime calledAt;
}
```

### Task 3: 创建 Repository

**Files:**
- Create: `backend/src/main/java/com/example/agent/repository/ToolRepository.java`
- Create: `backend/src/main/java/com/example/agent/repository/ToolLogRepository.java`

- [ ] **Step 1: 创建 ToolRepository.java**

```java
package com.example.agent.repository;

import com.example.agent.entity.Tool;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface ToolRepository extends JpaRepository<Tool, Long> {
    List<Tool> findByEnabledTrue();
    Tool findByName(String name);
}
```

- [ ] **Step 2: 创建 ToolLogRepository.java**

```java
package com.example.agent.repository;

import com.example.agent.entity.ToolLog;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ToolLogRepository extends JpaRepository<ToolLog, Long> {
}
```

### Task 4: 创建 ToolService

**Files:**
- Create: `backend/src/main/java/com/example/agent/service/ToolService.java`

- [ ] **Step 1: 创建 ToolService.java**

```java
package com.example.agent.service;

import com.example.agent.entity.Tool;
import com.example.agent.entity.ToolLog;
import com.example.agent.repository.ToolRepository;
import com.example.agent.repository.ToolLogRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import jakarta.annotation.PostConstruct;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class ToolService {
    @Autowired
    private ToolRepository toolRepository;
    @Autowired
    private ToolLogRepository toolLogRepository;
    private ObjectMapper objectMapper = new ObjectMapper();

    // 内存缓存：toolName -> tool config
    private final Map<String, Tool> toolCache = new ConcurrentHashMap<>();

    @PostConstruct
    public void loadTools() {
        reloadTools();
    }

    public void reloadTools() {
        toolCache.clear();
        List<Tool> tools = toolRepository.findByEnabledTrue();
        for (Tool tool : tools) {
            toolCache.put(tool.getName(), tool);
        }
    }

    public List<Tool> getAllEnabledTools() {
        return toolRepository.findByEnabledTrue();
    }

    public Tool getTool(Long id) {
        return toolRepository.findById(id).orElse(null);
    }

    public Tool createTool(Tool tool) {
        return toolRepository.save(tool);
    }

    public Tool updateTool(Long id, Tool tool) {
        tool.setId(id);
        Tool updated = toolRepository.save(tool);
        reloadTools();
        return updated;
    }

    public void deleteTool(Long id) {
        toolRepository.deleteById(id);
        reloadTools();
    }

    public Tool enableTool(Long id) {
        Tool tool = getTool(id);
        if (tool != null) {
            tool.setEnabled(true);
            tool = toolRepository.save(tool);
            reloadTools();
        }
        return tool;
    }

    public Tool disableTool(Long id) {
        Tool tool = getTool(id);
        if (tool != null) {
            tool.setEnabled(false);
            tool = toolRepository.save(tool);
            reloadTools();
        }
        return tool;
    }

    public Tool findByName(String name) {
        return toolCache.get(name);
    }

    public void logCall(String toolName, String action, String params, String result, int durationMs) {
        ToolLog log = new ToolLog();
        log.setToolName(toolName);
        log.setAction(action);
        log.setParams(params);
        log.setResult(result);
        log.setDurationMs(durationMs);
        toolLogRepository.save(log);
    }
}
```

### Task 5: 修改 ToolController

**Files:**
- Modify: `backend/src/main/java/com/example/agent/controller/ToolController.java`

- [ ] **Step 1: 添加管理端点**

在现有 ToolController 中添加：

```java
@Autowired
private ToolService toolService;

// 获取所有启用的工具
@GetMapping("/api/tools")
public ApiResponse<List<Tool>> getAllTools() {
    return ApiResponse.success(toolService.getAllEnabledTools());
}

// 添加工具
@PostMapping("/api/tools")
public ApiResponse<Tool> createTool(@RequestBody Tool tool) {
    Tool created = toolService.createTool(tool);
    return ApiResponse.success(created);
}

// 更新工具
@PutMapping("/api/tools/{id}")
public ApiResponse<Tool> updateTool(@PathVariable Long id, @RequestBody Tool tool) {
    Tool updated = toolService.updateTool(id, tool);
    return ApiResponse.success(updated);
}

// 删除工具
@DeleteMapping("/api/tools/{id}")
public ApiResponse<?> deleteTool(@PathVariable Long id) {
    toolService.deleteTool(id);
    return ApiResponse.success(null);
}

// 启用工具
@PostMapping("/api/tools/{id}/enable")
public ApiResponse<Tool> enableTool(@PathVariable Long id) {
    Tool tool = toolService.enableTool(id);
    return ApiResponse.success(tool);
}

// 禁用工具
@PostMapping("/api/tools/{id}/disable")
public ApiResponse<Tool> disableTool(@PathVariable Long id) {
    Tool tool = toolService.disableTool(id);
    return ApiResponse.success(tool);
}
```

### Task 6: 修改 ToolController 的查询端点添加日志

**Files:**
- Modify: `backend/src/main/java/com/example/agent/controller/ToolController.java`

- [ ] **Step 1: 在查询方法中添加日志记录**

修改原有查询端点，添加耗时统计和日志记录：

```java
long startTime = System.currentTimeMillis();
// ... 执行查询 ...
long durationMs = System.currentTimeMillis() - startTime;
toolService.logCall(toolName, action, paramsJson, resultJson, (int) durationMs);
```

### Task 7: 验证 Java 后端

- [ ] **Step 1: 编译并重启**

Run: `cd backend && mvn compile`
Expected: BUILD SUCCESS

---

## Phase 3: Python Agent

### Task 8: 创建 ToolLoader

**Files:**
- Create: `agent/agent/tool_loader.py`

- [ ] **Step 1: 创建 tool_loader.py**

```python
import requests
import json
from typing import Dict, List, Optional

class ToolLoader:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.tools: Dict[str, dict] = {}
        self._load_tools()

    def _load_tools(self):
        try:
            response = requests.get(f"{self.base_url}/api/tools", timeout=30)
            response.raise_for_status()
            result = response.json()
            if result.get("success"):
                self.tools = {}
                for tool in result.get("data", []):
                    self.tools[tool["name"]] = tool
        except Exception as e:
            print(f"加载工具失败: {e}")
            # 使用默认工具
            self._load_default_tools()

    def _load_default_tools(self):
        # 默认工具配置
        self.tools = {
            "OrderTool": {
                "name": "OrderTool",
                "description": "订单查询工具",
                "actions": [
                    {"name": "query_order_list", "description": "查询用户订单列表", "params": {"userId": {"type": "string", "required": True}, "status": {"type": "string", "required": False}}},
                    {"name": "query_order_detail", "description": "查询订单详情", "params": {"orderNo": {"type": "string", "required": True}}}
                ]
            },
            "UserTool": {
                "name": "UserTool",
                "description": "用户查询工具",
                "actions": [
                    {"name": "query_user_info", "description": "查询用户信息", "params": {"userId": {"type": "string", "required": True}}}
                ]
            },
            "InventoryTool": {
                "name": "InventoryTool",
                "description": "库存查询工具",
                "actions": [
                    {"name": "query_inventory", "description": "按SKU查询库存", "params": {"sku": {"type": "string", "required": True}}},
                    {"name": "query_warehouse_stock", "description": "按仓库查询库存", "params": {"warehouse": {"type": "string", "required": True}}}
                ]
            }
        }

    def reload(self):
        self._load_tools()

    def get_tool(self, name: str) -> Optional[dict]:
        return self.tools.get(name)

    def get_all_tools(self) -> Dict[str, dict]:
        return self.tools
```

### Task 9: 修改 Agent 类支持动态工具和日志

**Files:**
- Modify: `agent/agent/agent.py`

- [ ] **Step 1: 修改 Agent 类**

主要修改：
1. 初始化时加载工具
2. 构建 prompt 时使用动态工具描述
3. 调用工具时记录日志

```python
# 在 __init__ 中添加
self.tool_loader = ToolLoader(base_url="http://localhost:8080")

# 添加日志记录方法
def _log_call(self, tool_name: str, action: str, params: dict, result: str, duration_ms: int):
    try:
        requests.post(
            f"http://localhost:8080}/api/tools/log",
            json={
                "toolName": tool_name,
                "action": action,
                "params": params,
                "result": result,
                "durationMs": duration_ms
            },
            timeout=10
        )
    except:
        pass  # 日志记录失败不影响主流程
```

### Task 10: 修改 prompts.py 动态构建

**Files:**
- Modify: `agent/agent/prompts.py`

- [ ] **Step 1: 修改 build_agent_prompt**

```python
def build_agent_prompt(user_message: str, tool_loader=None, tool_results: str = None) -> str:
    tool_desc = ""
    if tool_loader:
        tools = tool_loader.get_all_tools()
        tool_lines = []
        for name, tool in tools.items():
            tool_lines.append(f"\n{tool['name']} - {tool['description']}")
            for action in tool.get("actions", []):
                params_str = ", ".join([f"{k}" for k in action.get("params", {}).keys()])
                tool_lines.append(f"   - {action['name']}: {action['description']} (参数: {params_str})")
        tool_desc = "\n".join(tool_lines)
    else:
        # 默认描述
        tool_desc = "OrderTool, UserTool, InventoryTool"

    tool_section = f"""
可用工具：
{tool_desc}
"""

    if tool_results:
        return f"""{TOOL_DESCRIPTIONS}
{tool_section}

用户问题: {user_message}

工具调用结果:
{tool_results}

请根据工具调用结果，用自然语言回答用户问题。
"""
    return f"""{TOOL_DESCRIPTIONS}
{tool_section}

用户问题: {user_message}

请选择合适的工具来回答用户问题，并以以下JSON格式返回:
{{
    "tool": "工具名称",
    "action": "操作名称",
    "params": {{"参数名": "参数值"}}
}}

如果没有合适的工具，请直接回答用户问题。
"""
```

### Task 11: 验证 Python Agent

- [ ] **Step 1: 测试导入**

Run: `cd /Users/yangte/PycharmProjects/langchain-study && python -c "from agent.agent import Agent; print('OK')"`
Expected: OK

- [ ] **Step 2: 测试工具加载**

Run: `cd /Users/yangte/PycharmProjects/langchain-study && python -c "from agent.agent.tool_loader import ToolLoader; loader = ToolLoader(); print(loader.get_all_tools().keys())"`
Expected: dict_keys(['OrderTool', 'UserTool', 'InventoryTool'])

---

## 执行方式

**两种执行方式：**

**1. Subagent-Driven (推荐)** — 我调度子任务代理逐个执行

**2. Inline Execution** — 在当前会话批量执行

选择哪种？
