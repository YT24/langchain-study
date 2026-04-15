package com.example.agent.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.agent.entity.SysTool;
import com.example.agent.entity.SysToolLog;
import com.example.agent.mapper.SysToolMapper;
import com.example.agent.mapper.SysToolLogMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import jakarta.annotation.PostConstruct;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class ToolService {

    @Autowired
    private SysToolMapper sysToolMapper;

    @Autowired
    private SysToolLogMapper sysToolLogMapper;

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
