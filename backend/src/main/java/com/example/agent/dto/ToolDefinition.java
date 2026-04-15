package com.example.agent.dto;

import lombok.Data;
import java.util.List;
import java.util.Map;

@Data
public class ToolDefinition {
    private String name;
    private String displayName;
    private String description;
    private String endpoint;
    private String httpMethod;
    private List<ParamDefinition> params;
    private String exampleResponse;

    @Data
    public static class ParamDefinition {
        private String name;
        private String type;
        private String description;
        private boolean required;
    }
}
