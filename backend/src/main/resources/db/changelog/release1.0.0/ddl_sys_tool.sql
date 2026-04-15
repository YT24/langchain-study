CREATE TABLE IF NOT EXISTS sys_tool (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE COMMENT '工具名称: OrderTool',
    display_name VARCHAR(100) COMMENT '显示名称',
    description VARCHAR(500) COMMENT '工具描述',
    icon VARCHAR(50) COMMENT '图标',
    category_id BIGINT COMMENT '分类ID',
    version VARCHAR(20) DEFAULT '1.0' COMMENT '版本号',
    status TINYINT DEFAULT 1 COMMENT '状态: 1启用 0禁用',
    is_builtin TINYINT DEFAULT 1 COMMENT '是否内置: 1是 0否',
    config JSON COMMENT '扩展配置',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (category_id) REFERENCES sys_tool_category(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工具表';
