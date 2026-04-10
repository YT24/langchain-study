# AI Agent 业务对象查询系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现一个 AI Agent 系统，通过自然语言查询订单、用户、库存三大业务对象

**Architecture:** Python Agent 作为意图识别和调度中枢，Java Spring Boot 提供 REST API 查询 MySQL 数据库，React 前端提供对话界面

**Tech Stack:** React + Python LangChain + Java Spring Boot + MySQL + MiniMax LLM

---

## 文件结构

```
langchain-study/
├── docs/superpowers/
│   ├── specs/2026-04-09-ai-agent-design.md
│   └── plans/2026-04-09-ai-agent-implementation-plan.md
├── database/
│   └── init.sql                          # 数据库初始化脚本
├── backend/                              # Java Spring Boot 项目
│   ├── pom.xml
│   └── src/main/java/com/example/agent/
│       ├── AgentApplication.java
│       ├── controller/
│       │   └── ToolController.java
│       ├── service/
│       │   ├── OrderService.java
│       │   ├── UserService.java
│       │   └── InventoryService.java
│       ├── mapper/
│       │   ├── OrderMapper.java
│       │   ├── UserMapper.java
│       │   └── InventoryMapper.java
│       └── model/
│           ├── Order.java
│           ├── User.java
│           └── Inventory.java
├── agent/                                # Python Agent 项目
│   ├── requirements.txt
│   └── agent/
│       ├── __init__.py
│       ├── agent.py                      # 核心 Agent
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── order_tool.py
│       │   ├── user_tool.py
│       │   └── inventory_tool.py
│       └── prompts.py
└── frontend/                             # React 项目
    ├── package.json
    └── src/
        ├── App.jsx
        ├── index.jsx
        ├── components/
        │   └── ChatInterface.jsx
        └── services/
            └── api.js
```

---

## Phase 1: 数据库初始化

### Task 1: 创建数据库初始化脚本

**Files:**
- Create: `database/init.sql`

- [ ] **Step 1: 创建 SQL 脚本**

```sql
-- 数据库初始化脚本
CREATE DATABASE IF NOT EXISTS agent_db DEFAULT CHARACTER SET utf8mb4;

USE agent_db;

-- 订单表
CREATE TABLE IF NOT EXISTS orders (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_no VARCHAR(32) NOT NULL UNIQUE COMMENT '订单号',
    user_id VARCHAR(32) NOT NULL COMMENT '用户ID',
    status VARCHAR(20) NOT NULL COMMENT '订单状态: pending, paid, shipped, completed, cancelled',
    total_amount DECIMAL(10,2) NOT NULL COMMENT '订单金额',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单表';

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(32) NOT NULL UNIQUE COMMENT '用户ID',
    name VARCHAR(64) NOT NULL COMMENT '姓名',
    phone VARCHAR(20) COMMENT '手机号',
    level VARCHAR(20) NOT NULL DEFAULT 'normal' COMMENT '会员等级: normal, silver, gold, vip',
    balance DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '账户余额',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 库存表
CREATE TABLE IF NOT EXISTS inventory (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sku VARCHAR(32) NOT NULL COMMENT '商品SKU',
    warehouse VARCHAR(32) NOT NULL COMMENT '仓库',
    quantity INT NOT NULL DEFAULT 0 COMMENT '库存数量',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_sku_warehouse (sku, warehouse),
    INDEX idx_sku (sku)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='库存表';

-- 插入测试数据
INSERT INTO users (user_id, name, phone, level, balance) VALUES
('U001', '张三', '13800138000', 'gold', 1000.00),
('U002', '李四', '13900139000', 'vip', 5000.00),
('U003', '王五', '13700137000', 'normal', 100.00);

INSERT INTO orders (order_no, user_id, status, total_amount) VALUES
('ORD20260409001', 'U001', 'completed', 299.00),
('ORD20260409002', 'U001', 'pending', 599.00),
('ORD20260409003', 'U002', 'shipped', 1299.00);

INSERT INTO inventory (sku, warehouse, quantity) VALUES
('SKU001', 'WH-A', 100),
('SKU001', 'WH-B', 50),
('SKU002', 'WH-A', 200);
```

- [ ] **Step 2: 执行脚本验证**

Run: `mysql -u root -p < database/init.sql`
Expected: 创建成功，无错误

---

## Phase 2: Java Spring Boot 后端

### Task 2: 创建 Spring Boot 项目结构

**Files:**
- Create: `backend/pom.xml`
- Create: `backend/src/main/java/com/example/agent/AgentApplication.java`
- Create: `backend/src/main/resources/application.yml`

- [ ] **Step 1: 创建 pom.xml**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
    </parent>

    <groupId>com.example</groupId>
    <artifactId>agent-backend</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <properties>
        <java.version>17</java.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.mybatis.spring.boot</groupId>
            <artifactId>mybatis-spring-boot-starter</artifactId>
            <version>3.0.3</version>
        </dependency>
        <dependency>
            <groupId>com.mysql</groupId>
            <artifactId>mysql-connector-j</artifactId>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <optional>true</optional>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
```

- [ ] **Step 2: 创建 AgentApplication.java**

```java
package com.example.agent;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class AgentApplication {
    public static void main(String[] args) {
        SpringApplication.run(AgentApplication.class, args);
    }
}
```

- [ ] **Step 3: 创建 application.yml**

```yaml
server:
  port: 8080

spring:
  datasource:
    url: jdbc:mysql://localhost:3306/agent_db?useUnicode=true&characterEncoding=utf-8
    username: root
    password: your_password
    driver-class-name: com.mysql.cj.jdbc.Driver
    hikari:
      maximum-pool-size: 50
      minimum-idle: 10

mybatis:
  mapper-locations: classpath:mapper/*.xml
  type-aliases-package: com.example.agent.model
```

- [ ] **Step 4: 验证项目编译**

Run: `cd backend && mvn compile`
Expected: BUILD SUCCESS

---

### Task 3: 创建数据模型

**Files:**
- Create: `backend/src/main/java/com/example/agent/model/Order.java`
- Create: `backend/src/main/java/com/example/agent/model/User.java`
- Create: `backend/src/main/java/com/example/agent/model/Inventory.java`
- Create: `backend/src/main/java/com/example/agent/model/ApiResponse.java`

- [ ] **Step 1: 创建 Order.java**

```java
package com.example.agent.model;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class Order {
    private Long id;
    private String orderNo;
    private String userId;
    private String status;
    private BigDecimal totalAmount;
    private LocalDateTime createdAt;
}
```

- [ ] **Step 2: 创建 User.java**

```java
package com.example.agent.model;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class User {
    private Long id;
    private String userId;
    private String name;
    private String phone;
    private String level;
    private BigDecimal balance;
    private LocalDateTime createdAt;
}
```

- [ ] **Step 3: 创建 Inventory.java**

```java
package com.example.agent.model;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class Inventory {
    private Long id;
    private String sku;
    private String warehouse;
    private Integer quantity;
    private LocalDateTime updatedAt;
}
```

- [ ] **Step 4: 创建 ApiResponse.java**

```java
package com.example.agent.model;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class ApiResponse<T> {
    private boolean success;
    private T data;
    private String message;

    public static <T> ApiResponse<T> success(T data) {
        return new ApiResponse<>(true, data, "查询成功");
    }

    public static <T> ApiResponse<T> error(String message) {
        return new ApiResponse<>(false, null, message);
    }
}
```

---

### Task 4: 创建 Mapper 接口和 XML

**Files:**
- Create: `backend/src/main/java/com/example/agent/mapper/OrderMapper.java`
- Create: `backend/src/main/java/com/example/agent/mapper/UserMapper.java`
- Create: `backend/src/main/java/com/example/agent/mapper/InventoryMapper.java`
- Create: `backend/src/main/resources/mapper/OrderMapper.xml`
- Create: `backend/src/main/resources/mapper/UserMapper.xml`
- Create: `backend/src/main/resources/mapper/InventoryMapper.xml`

- [ ] **Step 1: 创建 OrderMapper.java**

```java
package com.example.agent.mapper;

import com.example.agent.model.Order;
import org.apache.ibatis.annotations.Mapper;
import java.util.List;

@Mapper
public interface OrderMapper {
    List<Order> selectByUserId(String userId);
    List<Order> selectByUserIdAndStatus(String userId, String status);
    Order selectByOrderNo(String orderNo);
}
```

- [ ] **Step 2: 创建 UserMapper.java**

```java
package com.example.agent.mapper;

import com.example.agent.model.User;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface UserMapper {
    User selectByUserId(String userId);
}
```

- [ ] **Step 3: 创建 InventoryMapper.java**

```java
package com.example.agent.mapper;

import com.example.agent.model.Inventory;
import org.apache.ibatis.annotations.Mapper;
import java.util.List;

@Mapper
public interface InventoryMapper {
    List<Inventory> selectBySku(String sku);
    List<Inventory> selectByWarehouse(String warehouse);
}
```

- [ ] **Step 4: 创建 OrderMapper.xml**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN" "http://mybatis.org/dtd/mybatis-3-mapper.dtd">
<mapper namespace="com.example.agent.mapper.OrderMapper">
    <select id="selectByUserId" resultType="com.example.agent.model.Order">
        SELECT id, order_no as orderNo, user_id as userId, status, total_amount as totalAmount, created_at as createdAt
        FROM orders WHERE user_id = #{userId} ORDER BY created_at DESC
    </select>
    <select id="selectByUserIdAndStatus" resultType="com.example.agent.model.Order">
        SELECT id, order_no as orderNo, user_id as userId, status, total_amount as totalAmount, created_at as createdAt
        FROM orders WHERE user_id = #{userId} AND status = #{status} ORDER BY created_at DESC
    </select>
    <select id="selectByOrderNo" resultType="com.example.agent.model.Order">
        SELECT id, order_no as orderNo, user_id as userId, status, total_amount as totalAmount, created_at as createdAt
        FROM orders WHERE order_no = #{orderNo}
    </select>
</mapper>
```

- [ ] **Step 5: 创建 UserMapper.xml**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN" "http://mybatis.org/dtd/mybatis-3-mapper.dtd">
<mapper namespace="com.example.agent.mapper.UserMapper">
    <select id="selectByUserId" resultType="com.example.agent.model.User">
        SELECT id, user_id as userId, name, phone, level, balance, created_at as createdAt
        FROM users WHERE user_id = #{userId}
    </select>
</mapper>
```

- [ ] **Step 6: 创建 InventoryMapper.xml**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN" "http://mybatis.org/dtd/mybatis-3-mapper.dtd">
<mapper namespace="com.example.agent.mapper.InventoryMapper">
    <select id="selectBySku" resultType="com.example.agent.model.Inventory">
        SELECT id, sku, warehouse, quantity, updated_at as updatedAt
        FROM inventory WHERE sku = #{sku}
    </select>
    <select id="selectByWarehouse" resultType="com.example.agent.model.Inventory">
        SELECT id, sku, warehouse, quantity, updated_at as updatedAt
        FROM inventory WHERE warehouse = #{warehouse}
    </select>
</mapper>
```

---

### Task 5: 创建 Service 层

**Files:**
- Create: `backend/src/main/java/com/example/agent/service/OrderService.java`
- Create: `backend/src/main/java/com/example/agent/service/UserService.java`
- Create: `backend/src/main/java/com/example/agent/service/InventoryService.java`

- [ ] **Step 1: 创建 OrderService.java**

```java
package com.example.agent.service;

import com.example.agent.mapper.OrderMapper;
import com.example.agent.model.Order;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class OrderService {
    @Autowired
    private OrderMapper orderMapper;

    public List<Order> queryByUserId(String userId) {
        return orderMapper.selectByUserId(userId);
    }

    public List<Order> queryByUserIdAndStatus(String userId, String status) {
        return orderMapper.selectByUserIdAndStatus(userId, status);
    }

    public Order queryByOrderNo(String orderNo) {
        return orderMapper.selectByOrderNo(orderNo);
    }
}
```

- [ ] **Step 2: 创建 UserService.java**

```java
package com.example.agent.service;

import com.example.agent.mapper.UserMapper;
import com.example.agent.model.User;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class UserService {
    @Autowired
    private UserMapper userMapper;

    public User queryByUserId(String userId) {
        return userMapper.selectByUserId(userId);
    }
}
```

- [ ] **Step 3: 创建 InventoryService.java**

```java
package com.example.agent.service;

import com.example.agent.mapper.InventoryMapper;
import com.example.agent.model.Inventory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class InventoryService {
    @Autowired
    private InventoryMapper inventoryMapper;

    public List<Inventory> queryBySku(String sku) {
        return inventoryMapper.selectBySku(sku);
    }

    public List<Inventory> queryByWarehouse(String warehouse) {
        return inventoryMapper.selectByWarehouse(warehouse);
    }
}
```

---

### Task 6: 创建 Controller 层

**Files:**
- Create: `backend/src/main/java/com/example/agent/controller/ToolController.java`
- Create: `backend/src/main/java/com/example/agent/dto/ToolRequest.java`

- [ ] **Step 1: 创建 ToolRequest.java**

```java
package com.example.agent.dto;

import lombok.Data;
import java.util.Map;

@Data
public class ToolRequest {
    private String action;
    private Map<String, Object> params;
}
```

- [ ] **Step 2: 创建 ToolController.java**

```java
package com.example.agent.controller;

import com.example.agent.dto.ToolRequest;
import com.example.agent.model.ApiResponse;
import com.example.agent.model.Order;
import com.example.agent.model.User;
import com.example.agent.model.Inventory;
import com.example.agent.service.OrderService;
import com.example.agent.service.UserService;
import com.example.agent.service.InventoryService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/tools")
public class ToolController {
    @Autowired
    private OrderService orderService;
    @Autowired
    private UserService userService;
    @Autowired
    private InventoryService inventoryService;

    @PostMapping("/order/query")
    public ApiResponse<?> queryOrder(@RequestBody ToolRequest request) {
        try {
            String action = request.getAction();
            var params = request.getParams();
            List<Order> result;
            if ("query_order_list".equals(action)) {
                String userId = (String) params.get("userId");
                String status = (String) params.get("status");
                if (status != null) {
                    result = orderService.queryByUserIdAndStatus(userId, status);
                } else {
                    result = orderService.queryByUserId(userId);
                }
                return ApiResponse.success(result);
            } else if ("query_order_detail".equals(action)) {
                String orderNo = (String) params.get("orderNo");
                Order order = orderService.queryByOrderNo(orderNo);
                return ApiResponse.success(order);
            }
            return ApiResponse.error("未知 action: " + action);
        } catch (Exception e) {
            return ApiResponse.error("查询失败: " + e.getMessage());
        }
    }

    @PostMapping("/user/query")
    public ApiResponse<?> queryUser(@RequestBody ToolRequest request) {
        try {
            String action = request.getAction();
            var params = request.getParams();
            if ("query_user_info".equals(action)) {
                String userId = (String) params.get("userId");
                User user = userService.queryByUserId(userId);
                return ApiResponse.success(user);
            }
            return ApiResponse.error("未知 action: " + action);
        } catch (Exception e) {
            return ApiResponse.error("查询失败: " + e.getMessage());
        }
    }

    @PostMapping("/inventory/query")
    public ApiResponse<?> queryInventory(@RequestBody ToolRequest request) {
        try {
            String action = request.getAction();
            var params = request.getParams();
            List<Inventory> result;
            if ("query_inventory".equals(action)) {
                String sku = (String) params.get("sku");
                result = inventoryService.queryBySku(sku);
                return ApiResponse.success(result);
            } else if ("query_warehouse_stock".equals(action)) {
                String warehouse = (String) params.get("warehouse");
                result = inventoryService.queryByWarehouse(warehouse);
                return ApiResponse.success(result);
            }
            return ApiResponse.error("未知 action: " + action);
        } catch (Exception e) {
            return ApiResponse.error("查询失败: " + e.getMessage());
        }
    }
}
```

- [ ] **Step 3: 验证后端编译**

Run: `cd backend && mvn compile`
Expected: BUILD SUCCESS

---

## Phase 3: Python Agent

### Task 7: 创建 Python Agent 项目结构

**Files:**
- Create: `agent/requirements.txt`
- Create: `agent/agent/__init__.py`
- Create: `agent/agent/agent.py`
- Create: `agent/agent/tools/__init__.py`
- Create: `agent/agent/tools/order_tool.py`
- Create: `agent/agent/tools/user_tool.py`
- Create: `agent/agent/tools/inventory_tool.py`
- Create: `agent/agent/prompts.py`

- [ ] **Step 1: 创建 requirements.txt**

```
langchain==0.3.0
langchain-community==0.2.0
requests==2.31.0
```

- [ ] **Step 2: 创建 agent/__init__.py**

```python
# Agent package
```

- [ ] **Step 3: 创建 tools/__init__.py**

```python
from .order_tool import OrderTool
from .user_tool import UserTool
from .inventory_tool import InventoryTool

__all__ = ["OrderTool", "UserTool", "InventoryTool"]
```

- [ ] **Step 4: 创建 prompts.py**

```python
TOOL_DESCRIPTIONS = """
你是一个业务查询助手，可以帮助用户查询订单、用户和库存信息。

可用工具：

1. OrderTool - 订单查询
   - query_order_list: 查询用户订单列表
     参数: userId (必需), status (可选)
   - query_order_detail: 查询订单详情
     参数: orderNo (必需)

2. UserTool - 用户查询
   - query_user_info: 查询用户信息
     参数: userId (必需)

3. InventoryTool - 库存查询
   - query_inventory: 按SKU查询库存
     参数: sku (必需)
   - query_warehouse_stock: 按仓库查询库存
     参数: warehouse (必需)

请根据用户的问题，选择合适的工具调用。
"""

def build_agent_prompt(user_message: str, tool_results: str = None) -> str:
    if tool_results:
        return f"""{TOOL_DESCRIPTIONS}

用户问题: {user_message}

工具调用结果:
{tool_results}

请根据工具调用结果，用自然语言回答用户问题。
"""
    return f"""{TOOL_DESCRIPTIONS}

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

- [ ] **Step 5: 创建 BaseTool 类和 OrderTool**

```python
# agent/tools/order_tool.py
import requests
from typing import Dict, Any, Optional, List

class BaseTool:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url

    def call_api(self, endpoint: str, action: str, params: Dict[str, Any]) -> Dict:
        url = f"{self.base_url}{endpoint}"
        payload = {"action": action, "params": params}
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()


class OrderTool(BaseTool):
    def __init__(self):
        super().__init__()

    def query_order_list(self, userId: str, status: Optional[str] = None) -> List[Dict]:
        params = {"userId": userId}
        if status:
            params["status"] = status
        result = self.call_api("/api/tools/order/query", "query_order_list", params)
        if not result.get("success"):
            raise Exception(result.get("message", "查询失败"))
        return result.get("data", [])

    def query_order_detail(self, orderNo: str) -> Optional[Dict]:
        result = self.call_api("/api/tools/order/query", "query_order_detail", {"orderNo": orderNo})
        if not result.get("success"):
            raise Exception(result.get("message", "查询失败"))
        return result.get("data")
```

- [ ] **Step 6: 创建 UserTool**

```python
# agent/tools/user_tool.py
from .order_tool import BaseTool

class UserTool(BaseTool):
    def __init__(self):
        super().__init__()

    def query_user_info(self, userId: str) -> Dict:
        result = self.call_api("/api/tools/user/query", "query_user_info", {"userId": userId})
        if not result.get("success"):
            raise Exception(result.get("message", "查询失败"))
        return result.get("data")
```

- [ ] **Step 7: 创建 InventoryTool**

```python
# agent/tools/inventory_tool.py
from .order_tool import BaseTool

class InventoryTool(BaseTool):
    def __init__(self):
        super().__init__()

    def query_inventory(self, sku: str) -> list:
        result = self.call_api("/api/tools/inventory/query", "query_inventory", {"sku": sku})
        if not result.get("success"):
            raise Exception(result.get("message", "查询失败"))
        return result.get("data", [])

    def query_warehouse_stock(self, warehouse: str) -> list:
        result = self.call_api("/api/tools/inventory/query", "query_warehouse_stock", {"warehouse": warehouse})
        if not result.get("success"):
            raise Exception(result.get("message", "查询失败"))
        return result.get("data", [])
```

- [ ] **Step 8: 创建核心 Agent**

```python
# agent/agent.py
import json
import os
import requests
from typing import Optional
from .tools.order_tool import OrderTool
from .tools.user_tool import UserTool
from .tools.inventory_tool import InventoryTool
from .prompts import build_agent_prompt

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
MINIMAX_BASE_URL = "https://api.minimax.chat/v1"

class Agent:
    def __init__(self):
        self.order_tool = OrderTool()
        self.user_tool = UserTool()
        self.inventory_tool = InventoryTool()

    def _call_minimax(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {MINIMAX_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "MiniMax-Text-01",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        response = requests.post(
            f"{MINIMAX_BASE_URL}/text/chatcompletion_v2",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]

    def _parse_tool_call(self, llm_response: str) -> Optional[dict]:
        try:
            for line in llm_response.split('\n'):
                line = line.strip()
                if line.startswith('{') and line.endswith('}'):
                    return json.loads(line)
            start = llm_response.find('{')
            end = llm_response.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(llm_response[start:end])
        except json.JSONDecodeError:
            pass
        return None

    def _execute_tool(self, tool: str, action: str, params: dict) -> str:
        try:
            if tool == "OrderTool":
                if action == "query_order_list":
                    data = self.order_tool.query_order_list(**params)
                    return json.dumps(data, ensure_ascii=False)
                elif action == "query_order_detail":
                    data = self.order_tool.query_order_detail(**params)
                    return json.dumps(data, ensure_ascii=False)
            elif tool == "UserTool":
                if action == "query_user_info":
                    data = self.user_tool.query_user_info(**params)
                    return json.dumps(data, ensure_ascii=False)
            elif tool == "InventoryTool":
                if action == "query_inventory":
                    data = self.inventory_tool.query_inventory(**params)
                    return json.dumps(data, ensure_ascii=False)
                elif action == "query_warehouse_stock":
                    data = self.inventory_tool.query_warehouse_stock(**params)
                    return json.dumps(data, ensure_ascii=False)
            return f"未知工具: {tool}"
        except Exception as e:
            return f"工具执行失败: {str(e)}"

    def chat(self, message: str) -> str:
        prompt = build_agent_prompt(message)
        llm_response = self._call_minimax(prompt)

        tool_call = self._parse_tool_call(llm_response)
        if not tool_call:
            return llm_response

        tool = tool_call.get("tool")
        action = tool_call.get("action")
        params = tool_call.get("params", {})

        if not tool or not action:
            return llm_response

        tool_result = self._execute_tool(tool, action, params)
        final_prompt = build_agent_prompt(message, tool_result)
        final_response = self._call_minimax(final_prompt)
        return final_response


if __name__ == "__main__":
    agent = Agent()
    while True:
        user_input = input("用户: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        response = agent.chat(user_input)
        print(f"助手: {response}")
```

- [ ] **Step 9: 验证 Python 环境**

Run: `cd agent && pip install -r requirements.txt`
Run: `python -c "from agent import Agent; print('OK')"`
Expected: 无错误输出

---

## Phase 4: React 前端

### Task 8: 创建 React 项目结构

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/src/index.jsx`
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/components/ChatInterface.jsx`
- Create: `frontend/src/services/api.js`
- Create: `frontend/index.html`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "agent-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0"
  }
}
```

- [ ] **Step 2: 创建 vite.config.js**

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})
```

- [ ] **Step 3: 创建 index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>AI Agent 查询系统</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/index.jsx"></script>
</body>
</html>
```

- [ ] **Step 4: 创建 index.jsx**

```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

- [ ] **Step 5: 创建 api.js**

```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000
})

export const sendMessage = async (message) => {
  const response = await api.post('/chat', { message })
  return response.data
}
```

- [ ] **Step 6: 创建 ChatInterface.jsx**

```jsx
import React, { useState } from 'react'
import { sendMessage } from '../services/api'

export default function ChatInterface() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const result = await sendMessage(userMessage)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: result.success ? result.response : result.message || '抱歉，出了点问题'
      }])
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '网络错误，请稍后重试'
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '20px' }}>AI Agent 业务查询</h1>

      <div style={{ flex: 1, overflowY: 'auto', border: '1px solid #ddd', borderRadius: '8px', padding: '16px', marginBottom: '16px' }}>
        {messages.length === 0 && (
          <p style={{ textAlign: 'center', color: '#999' }}>请输入您的问题，例如："帮我查一下用户 U001 的订单"</p>
        )}
        {messages.map((msg, idx) => (
          <div key={idx} style={{
            display: 'flex',
            justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
            marginBottom: '12px'
          }}>
            <div style={{
              maxWidth: '70%',
              padding: '12px 16px',
              borderRadius: '12px',
              backgroundColor: msg.role === 'user' ? '#007AFF' : '#f1f1f1',
              color: msg.role === 'user' ? '#fff' : '#333'
            }}>
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ textAlign: 'center', color: '#999' }}>思考中...</div>
        )}
      </div>

      <div style={{ display: 'flex', gap: '12px' }}>
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="输入您的问题..."
          rows={2}
          style={{ flex: 1, padding: '12px', borderRadius: '8px', border: '1px solid #ddd', resize: 'none' }}
        />
        <button
          onClick={handleSend}
          disabled={loading}
          style={{ padding: '12px 24px', borderRadius: '8px', border: 'none', backgroundColor: '#007AFF', color: '#fff', cursor: loading ? 'not-allowed' : 'pointer' }}
        >
          发送
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 7: 创建 App.jsx**

```jsx
import React from 'react'
import ChatInterface from './components/ChatInterface'

export default function App() {
  return <ChatInterface />
}
```

- [ ] **Step 8: 验证前端构建**

Run: `cd frontend && npm install && npm run build`
Expected: 无错误，生成 dist 目录

---

## Phase 5: 集成与运行

### Task 9: 启动与验证

- [ ] **Step 1: 启动 MySQL 并执行初始化脚本**

Run: `mysql -u root -p < database/init.sql`

- [ ] **Step 2: 启动 Java 后端**

Run: `cd backend && mvn spring-boot:run`
Expected: 后端启动在 8080 端口

- [ ] **Step 3: 测试后端 API**

Run: `curl -X POST http://localhost:8080/api/tools/user/query -H "Content-Type: application/json" -d '{"action":"query_user_info","params":{"userId":"U001"}}'`
Expected: 返回用户 U001 的信息

- [ ] **Step 4: 启动 Python Agent 服务**

Run: `cd agent && python -m uvicorn agent.server:app --host 0.0.0.0 --port 5000`
Expected: Agent 服务启动在 5000 端口

需要创建 `agent/server.py`:
```python
# agent/server.py
from flask import Flask, request, jsonify
from agent import Agent

app = Flask(__name__)
agent = Agent()

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    response = agent.chat(message)
    return jsonify({'success': True, 'response': response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

- [ ] **Step 5: 启动前端**

Run: `cd frontend && npm run dev`
Expected: 前端启动在 3000 端口

- [ ] **Step 6: 完整流程测试**

在浏览器打开 http://localhost:3000，输入："帮我查一下用户 U001 的订单"
Expected: 返回自然语言回答，包含 U001 的订单信息
