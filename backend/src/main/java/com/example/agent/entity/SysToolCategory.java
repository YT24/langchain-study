package com.example.agent.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("sys_tool_category")
public class SysToolCategory {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String name;
    private String code;
    private String icon;
    private Integer sortOrder = 0;
    private String description;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;
}
