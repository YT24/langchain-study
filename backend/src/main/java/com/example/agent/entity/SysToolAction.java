package com.example.agent.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("sys_tool_action")
public class SysToolAction {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long toolId;
    private String name;
    private String displayName;
    private String description;
    private String baseUrl;
    private String httpMethod;
    private String endpoint;
    private String requestParams;
    private String responseParams;
    private String exampleRequest;
    private String exampleResponse;
    private Integer sortOrder = 0;
    private Integer status = 1;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;
}
