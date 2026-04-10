package com.example.agent.dto;

import lombok.Data;
import java.util.Map;

@Data
public class ToolRequest {
    private String action;
    private Map<String, Object> params;
}
