package com.example.agent.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.agent.entity.SysTool;
import com.example.agent.entity.SysToolLog;
import com.example.agent.entity.SysToolAction;
import com.example.agent.mapper.SysToolMapper;
import com.example.agent.mapper.SysToolLogMapper;
import com.example.agent.mapper.SysToolActionMapper;
import com.example.agent.dto.ToolDefinition;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import jakarta.annotation.PostConstruct;
import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class ToolService {

    @Autowired
    private SysToolMapper sysToolMapper;

    @Autowired
    private SysToolLogMapper sysToolLogMapper;

    @Autowired
    private SysToolActionMapper actionMapper;

    private final ObjectMapper objectMapper = new ObjectMapper();

    // 内存缓存：toolName -> tool config
    private final Map<String, SysTool> toolCache = new ConcurrentHashMap<>();

    @PostConstruct
    public void loadTools() {
        reloadTools();
    }

    public void reloadTools() {
        toolCache.clear();
        getAllEnabledTools().forEach(tool -> toolCache.put(tool.getName(), tool));
    }

    public List<SysTool> getAllEnabledTools() {
        return sysToolMapper.selectList(
            new LambdaQueryWrapper<SysTool>()
                .eq(SysTool::getStatus, 1)
                .orderByDesc(SysTool::getCreatedAt)
        );
    }

    public List<ToolDefinition> getAllToolDefinitions() {
        List<SysTool> tools = getAllEnabledTools();
        List<ToolDefinition> definitions = new ArrayList<>();

        for (SysTool tool : tools) {
            List<SysToolAction> actions = actionMapper.selectList(
                new LambdaQueryWrapper<SysToolAction>()
                    .eq(SysToolAction::getToolId, tool.getId())
                    .eq(SysToolAction::getStatus, 1)
                    .orderByAsc(SysToolAction::getSortOrder)
            );

            for (SysToolAction action : actions) {
                ToolDefinition def = new ToolDefinition();
                def.setName(action.getName());
                def.setDisplayName(action.getDisplayName());
                def.setDescription(action.getDescription());
                def.setEndpoint(action.getEndpoint());
                def.setHttpMethod(action.getHttpMethod());

                // 解析 requestParams JSON - 格式是 {"paramName": {...}} 而不是 [{...}]
                if (action.getRequestParams() != null && !action.getRequestParams().isEmpty()) {
                    try {
                        @SuppressWarnings("unchecked")
                        Map<String, Map<String, Object>> paramsMap = objectMapper.readValue(
                            action.getRequestParams(),
                            Map.class
                        );
                        List<ToolDefinition.ParamDefinition> paramsList = new ArrayList<>();
                        for (Map.Entry<String, Map<String, Object>> entry : paramsMap.entrySet()) {
                            ToolDefinition.ParamDefinition param = new ToolDefinition.ParamDefinition();
                            param.setName(entry.getKey());
                            Map<String, Object> paramConfig = entry.getValue();
                            param.setType((String) paramConfig.get("type"));
                            param.setDescription((String) paramConfig.get("description"));
                            param.setRequired(Boolean.TRUE.equals(paramConfig.get("required")));
                            paramsList.add(param);
                        }
                        def.setParams(paramsList);
                    } catch (Exception e) {
                        def.setParams(new ArrayList<>());
                    }
                } else {
                    def.setParams(new ArrayList<>());
                }

                def.setExampleResponse(action.getExampleResponse());
                definitions.add(def);
            }
        }

        return definitions;
    }

    public List<SysTool> getAllTools() {
        return sysToolMapper.selectList(
            new LambdaQueryWrapper<SysTool>().orderByDesc(SysTool::getCreatedAt)
        );
    }

    public SysTool getTool(Long id) {
        return sysToolMapper.selectById(id);
    }

    public SysTool createTool(SysTool tool) {
        sysToolMapper.insert(tool);
        reloadTools();
        return tool;
    }

    public SysTool updateTool(Long id, SysTool tool) {
        tool.setId(id);
        sysToolMapper.updateById(tool);
        reloadTools();
        return sysToolMapper.selectById(id);
    }

    public void deleteTool(Long id) {
        sysToolMapper.deleteById(id);
        reloadTools();
    }

    public SysTool enableTool(Long id) {
        SysTool tool = getTool(id);
        if (tool != null) {
            tool.setStatus(1);
            sysToolMapper.updateById(tool);
            reloadTools();
        }
        return tool;
    }

    public SysTool disableTool(Long id) {
        SysTool tool = getTool(id);
        if (tool != null) {
            tool.setStatus(0);
            sysToolMapper.updateById(tool);
            reloadTools();
        }
        return tool;
    }

    public SysTool findByName(String name) {
        return toolCache.get(name);
    }

    public void logCall(String toolName, String action, String params, String result, int durationMs) {
        SysToolLog log = new SysToolLog();
        log.setToolName(toolName);
        log.setAction(action);
        log.setRequestParams(params);
        log.setResponseData(result);
        log.setDurationMs(durationMs);
        log.setStatus("SUCCESS");
        sysToolLogMapper.insert(log);
    }
}
