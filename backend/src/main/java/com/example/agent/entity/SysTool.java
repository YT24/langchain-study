package com.example.agent.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("sys_tool")
public class SysTool {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String name;
    private String displayName;
    private String description;
    private String icon;
    private Long categoryId;
    private String version = "1.0";
    private Integer status = 1;
    private Integer isBuiltin = 1;
    private String config;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;
}
