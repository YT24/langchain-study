package com.example.agent.controller;

import com.example.agent.dto.ToolDefinition;
import com.example.agent.dto.ToolRequest;
import com.example.agent.entity.SysTool;
import com.example.agent.model.ApiResponse;
import com.example.agent.service.ToolService;
import com.example.agent.service.OrderQueryService;
import com.example.agent.service.UserQueryService;
import com.example.agent.service.InventoryQueryService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@CrossOrigin(origins = "*")
@RequestMapping("/tools")
public class ToolController {
    @Autowired
    private ToolService toolService;
    @Autowired
    private OrderQueryService orderQueryService;
    @Autowired
    private UserQueryService userQueryService;
    @Autowired
    private InventoryQueryService inventoryQueryService;

    @GetMapping
    public ApiResponse<List<SysTool>> getAllTools() {
        return ApiResponse.success(toolService.getAllEnabledTools());
    }

    @GetMapping("/actions")
    public ApiResponse<List<ToolDefinition>> getAllToolActions() {
        return ApiResponse.success(toolService.getAllToolDefinitions());
    }

    @PostMapping
    public ApiResponse<SysTool> createTool(@RequestBody SysTool tool) {
        SysTool created = toolService.createTool(tool);
        return ApiResponse.success(created);
    }

    @PutMapping("/{id}")
    public ApiResponse<SysTool> updateTool(@PathVariable Long id, @RequestBody SysTool tool) {
        SysTool updated = toolService.updateTool(id, tool);
        return ApiResponse.success(updated);
    }

    @DeleteMapping("/{id}")
    public ApiResponse<?> deleteTool(@PathVariable Long id) {
        toolService.deleteTool(id);
        return ApiResponse.success(null);
    }

    @PostMapping("/{id}/enable")
    public ApiResponse<SysTool> enableTool(@PathVariable Long id) {
        SysTool tool = toolService.enableTool(id);
        return ApiResponse.success(tool);
    }

    @PostMapping("/{id}/disable")
    public ApiResponse<SysTool> disableTool(@PathVariable Long id) {
        SysTool tool = toolService.disableTool(id);
        return ApiResponse.success(tool);
    }

    @PostMapping("/log")
    public ApiResponse<?> logToolCall(@RequestBody LogRequest request) {
        toolService.logCall(
            request.getToolName(),
            request.getAction(),
            request.getParams(),
            request.getResult(),
            request.getDurationMs()
        );
        return ApiResponse.success(null);
    }

    @PostMapping("/order/query")
    public ApiResponse<?> queryOrder(@RequestBody ToolRequest request) {
        try {
            Object result = orderQueryService.execute(request.getAction(), request.getParams());
            return ApiResponse.success(result);
        } catch (IllegalArgumentException e) {
            return ApiResponse.error(e.getMessage());
        } catch (Exception e) {
            return ApiResponse.error("查询失败: " + e.getMessage());
        }
    }

    @PostMapping("/user/query")
    public ApiResponse<?> queryUser(@RequestBody ToolRequest request) {
        try {
            Object result = userQueryService.execute(request.getAction(), request.getParams());
            return ApiResponse.success(result);
        } catch (IllegalArgumentException e) {
            return ApiResponse.error(e.getMessage());
        } catch (Exception e) {
            return ApiResponse.error("查询失败: " + e.getMessage());
        }
    }

    @PostMapping("/inventory/query")
    public ApiResponse<?> queryInventory(@RequestBody ToolRequest request) {
        try {
            Object result = inventoryQueryService.execute(request.getAction(), request.getParams());
            return ApiResponse.success(result);
        } catch (IllegalArgumentException e) {
            return ApiResponse.error(e.getMessage());
        } catch (Exception e) {
            return ApiResponse.error("查询失败: " + e.getMessage());
        }
    }

    @lombok.Data
    public static class LogRequest {
        private String toolName;
        private String action;
        private String params;
        private String result;
        private Integer durationMs;
    }
}
