package com.example.agent.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("sys_chat_message")
public class SysChatMessage {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String sessionId;
    private String role;
    private String content;
    private String toolCalls;
    private String toolResults;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;
}
