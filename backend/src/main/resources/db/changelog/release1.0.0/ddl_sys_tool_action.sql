CREATE TABLE IF NOT EXISTS sys_tool_action (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tool_id BIGINT NOT NULL COMMENT '工具ID',
    name VARCHAR(100) NOT NULL COMMENT '动作名称: query_order_list',
    display_name VARCHAR(100) COMMENT '显示名称',
    description VARCHAR(500) COMMENT '动作描述',
    base_url VARCHAR(255) DEFAULT 'http://localhost:8080' COMMENT '后端服务地址',
    http_method VARCHAR(10) DEFAULT 'POST' COMMENT 'HTTP方法',
    endpoint VARCHAR(255) COMMENT '后端接口路径',
    request_params JSON COMMENT '请求参数定义',
    response_params JSON COMMENT '响应参数定义',
    example_request JSON COMMENT '请求示例',
    example_response JSON COMMENT '响应示例',
    sort_order INT DEFAULT 0 COMMENT '排序',
    status TINYINT DEFAULT 1 COMMENT '状态: 1启用 0禁用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (tool_id) REFERENCES sys_tool(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工具动作表';
