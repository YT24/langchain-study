package com.example.agent.service;

import com.example.agent.entity.Tool;
import com.example.agent.entity.ToolLog;
import com.example.agent.repository.ToolRepository;
import com.example.agent.repository.ToolLogRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import jakarta.annotation.PostConstruct;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class ToolService {
    @Autowired
    private ToolRepository toolRepository;
    @Autowired
    private ToolLogRepository toolLogRepository;

    // 内存缓存：toolName -> tool config
    private final Map<String, Tool> toolCache = new ConcurrentHashMap<>();

    @PostConstruct
    public void loadTools() {
        reloadTools();
    }

    public void reloadTools() {
        toolCache.clear();
        List<Tool> tools = toolRepository.findByEnabledTrue();
        for (Tool tool : tools) {
            toolCache.put(tool.getName(), tool);
        }
    }

    public List<Tool> getAllEnabledTools() {
        return toolRepository.findByEnabledTrue();
    }

    public Tool getTool(Long id) {
        return toolRepository.findById(id).orElse(null);
    }

    public Tool createTool(Tool tool) {
        return toolRepository.save(tool);
    }

    public Tool updateTool(Long id, Tool tool) {
        tool.setId(id);
        Tool updated = toolRepository.save(tool);
        reloadTools();
        return updated;
    }

    public void deleteTool(Long id) {
        toolRepository.deleteById(id);
        reloadTools();
    }

    public Tool enableTool(Long id) {
        Tool tool = getTool(id);
        if (tool != null) {
            tool.setEnabled(true);
            tool = toolRepository.save(tool);
            reloadTools();
        }
        return tool;
    }

    public Tool disableTool(Long id) {
        Tool tool = getTool(id);
        if (tool != null) {
            tool.setEnabled(false);
            tool = toolRepository.save(tool);
            reloadTools();
        }
        return tool;
    }

    public Tool findByName(String name) {
        return toolCache.get(name);
    }

    public void logCall(String toolName, String action, String params, String result, int durationMs) {
        ToolLog log = new ToolLog();
        log.setToolName(toolName);
        log.setAction(action);
        log.setParams(params);
        log.setResult(result);
        log.setDurationMs(durationMs);
        toolLogRepository.save(log);
    }
}
