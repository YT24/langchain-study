-- AI Agent 业务对象查询系统数据库初始化脚本

CREATE DATABASE IF NOT EXISTS fff DEFAULT CHARACTER SET utf8mb4;

USE fff;

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

-- 插入测试数据 (忽略已存在的)
INSERT IGNORE INTO users (user_id, name, phone, level, balance) VALUES
('U001', '张三', '13800138000', 'gold', 1000.00),
('U002', '李四', '13900139000', 'vip', 5000.00),
('U003', '王五', '13700137000', 'normal', 100.00);

INSERT IGNORE INTO orders (order_no, user_id, status, total_amount) VALUES
('ORD20260409001', 'U001', 'completed', 299.00),
('ORD20260409002', 'U001', 'pending', 599.00),
('ORD20260409003', 'U002', 'shipped', 1299.00);

INSERT IGNORE INTO inventory (sku, warehouse, quantity) VALUES
('SKU001', 'WH-A', 100),
('SKU001', 'WH-B', 50),
('SKU002', 'WH-A', 200);

-- 工具定义表
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

-- 工具调用日志表
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

-- 插入初始工具数据 (忽略已存在的)
INSERT IGNORE INTO tools (name, description, actions, enabled) VALUES
('OrderTool', '订单查询工具', '{"actions":[{"name":"query_order_list","description":"查询用户订单列表","params":{"userId":{"type":"string","required":true},"status":{"type":"string","required":false},"minAmount":{"type":"number","required":false},"maxAmount":{"type":"number","required":false},"startDate":{"type":"string","required":false},"endDate":{"type":"string","required":false}}},{"name":"query_order_detail","description":"查询订单详情","params":{"orderNo":{"type":"string","required":true}}},{"name":"query_order_statistics","description":"查询用户订单统计，返回订单数量、总金额、平均金额","params":{"userId":{"type":"string","required":true},"minAmount":{"type":"number","required":false},"maxAmount":{"type":"number","required":false}}}]}', TRUE),
('UserTool', '用户查询工具', '{"actions":[{"name":"query_user_info","description":"查询用户信息","params":{"userId":{"type":"string","required":true}}}]}', TRUE),
('InventoryTool', '库存查询工具', '{"actions":[{"name":"query_inventory","description":"按SKU查询库存","params":{"sku":{"type":"string","required":true}}},{"name":"query_warehouse_stock","description":"按仓库查询库存","params":{"warehouse":{"type":"string","required":true}}}]}', TRUE);
