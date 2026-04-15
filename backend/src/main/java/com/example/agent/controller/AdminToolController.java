package com.example.agent.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.agent.entity.SysTool;
import com.example.agent.entity.SysToolAction;
import com.example.agent.entity.SysToolCategory;
import com.example.agent.mapper.SysToolCategoryMapper;
import com.example.agent.mapper.SysToolActionMapper;
import com.example.agent.service.ToolService;
import com.example.agent.model.ApiResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/admin/tools")
@CrossOrigin(origins = "*")
public class AdminToolController {

    @Autowired
    private ToolService toolService;

    @Autowired
    private SysToolCategoryMapper categoryMapper;

    @Autowired
    private SysToolActionMapper actionMapper;

    // ========== 工具管理 ==========

    @GetMapping
    public ApiResponse<List<SysTool>> getAllTools() {
        return ApiResponse.success(toolService.getAllTools());
    }

    @GetMapping("/{id}")
    public ApiResponse<SysTool> getToolById(@PathVariable Long id) {
        return ApiResponse.success(toolService.getTool(id));
    }

    @PostMapping
    public ApiResponse<SysTool> createTool(@RequestBody SysTool tool) {
        tool.setId(null);
        return ApiResponse.success(toolService.createTool(tool));
    }

    @PutMapping("/{id}")
    public ApiResponse<SysTool> updateTool(@PathVariable Long id, @RequestBody SysTool tool) {
        return ApiResponse.success(toolService.updateTool(id, tool));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<?> deleteTool(@PathVariable Long id) {
        toolService.deleteTool(id);
        return ApiResponse.success(null);
    }

    @PostMapping("/{id}/enable")
    public ApiResponse<SysTool> enableTool(@PathVariable Long id) {
        return ApiResponse.success(toolService.enableTool(id));
    }

    @PostMapping("/{id}/disable")
    public ApiResponse<SysTool> disableTool(@PathVariable Long id) {
        return ApiResponse.success(toolService.disableTool(id));
    }

    // ========== 工具动作管理 ==========

    @GetMapping("/{toolId}/actions")
    public ApiResponse<List<SysToolAction>> getActionsByToolId(@PathVariable Long toolId) {
        return ApiResponse.success(actionMapper.selectList(
            new LambdaQueryWrapper<SysToolAction>()
                .eq(SysToolAction::getToolId, toolId)
                .orderByAsc(SysToolAction::getSortOrder)
        ));
    }

    @PostMapping("/actions")
    public ApiResponse<SysToolAction> createAction(@RequestBody SysToolAction action) {
        action.setId(null);
        actionMapper.insert(action);
        return ApiResponse.success(action);
    }

    @PutMapping("/actions/{id}")
    public ApiResponse<SysToolAction> updateAction(@PathVariable Long id, @RequestBody SysToolAction action) {
        action.setId(id);
        actionMapper.updateById(action);
        return ApiResponse.success(actionMapper.selectById(id));
    }

    @DeleteMapping("/actions/{id}")
    public ApiResponse<?> deleteAction(@PathVariable Long id) {
        actionMapper.deleteById(id);
        return ApiResponse.success(null);
    }

    // ========== 分类管理 ==========

    @GetMapping("/categories")
    public ApiResponse<List<SysToolCategory>> getAllCategories() {
        return ApiResponse.success(categoryMapper.selectList(null));
    }

    @PostMapping("/categories")
    public ApiResponse<SysToolCategory> createCategory(@RequestBody SysToolCategory category) {
        category.setId(null);
        categoryMapper.insert(category);
        return ApiResponse.success(category);
    }

    @PutMapping("/categories/{id}")
    public ApiResponse<SysToolCategory> updateCategory(@PathVariable Long id, @RequestBody SysToolCategory category) {
        category.setId(id);
        categoryMapper.updateById(category);
        return ApiResponse.success(categoryMapper.selectById(id));
    }

    @DeleteMapping("/categories/{id}")
    public ApiResponse<?> deleteCategory(@PathVariable Long id) {
        categoryMapper.deleteById(id);
        return ApiResponse.success(null);
    }
}
