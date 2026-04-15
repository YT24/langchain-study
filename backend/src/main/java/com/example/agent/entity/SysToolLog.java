package com.example.agent.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("sys_tool_log")
public class SysToolLog {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String sessionId;
    private Long toolId;
    private String toolName;
    private String action;
    private String requestParams;
    private String responseData;
    private Integer durationMs;
    private String status;
    private String errorMessage;
    private Long userId;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;
}
