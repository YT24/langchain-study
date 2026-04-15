CREATE TABLE IF NOT EXISTS sys_tool_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) COMMENT '会话ID',
    tool_id BIGINT COMMENT '工具ID',
    tool_name VARCHAR(100) COMMENT '工具名称',
    action VARCHAR(100) COMMENT '动作名称',
    request_params TEXT COMMENT '请求参数(JSON)',
    response_data TEXT COMMENT '响应数据(JSON)',
    duration_ms INT COMMENT '耗时(毫秒)',
    status VARCHAR(20) COMMENT '状态: SUCCESS/FAIL',
    error_message TEXT COMMENT '错误信息',
    user_id BIGINT COMMENT '用户ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (tool_id) REFERENCES sys_tool(id),
    FOREIGN KEY (user_id) REFERENCES sys_user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工具调用日志表';
