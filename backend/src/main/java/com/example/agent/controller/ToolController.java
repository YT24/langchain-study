package com.example.agent.controller;

import com.example.agent.dto.ToolDefinition;
import com.example.agent.dto.ToolRequest;
import com.example.agent.entity.SysTool;
import com.example.agent.model.ApiResponse;
import com.example.agent.model.Order;
import com.example.agent.model.OrderStatistics;
import com.example.agent.model.User;
import com.example.agent.model.Inventory;
import com.example.agent.service.OrderService;
import com.example.agent.service.UserService;
import com.example.agent.service.InventoryService;
import com.example.agent.service.ToolService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.math.BigDecimal;
import java.util.List;

@RestController
@CrossOrigin(origins = "*")
@RequestMapping("/tools")
public class ToolController {
    @Autowired
    private OrderService orderService;
    @Autowired
    private UserService userService;
    @Autowired
    private InventoryService inventoryService;
    @Autowired
    private ToolService toolService;

    private final ObjectMapper objectMapper = new ObjectMapper();

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
        long startTime = System.currentTimeMillis();
        try {
            String action = request.getAction();
            var params = request.getParams();
            List<Order> result;
            Object amountObj = null;

            if ("query_order_list".equals(action)) {
                String userId = (String) params.get("userId");
                String status = (String) params.get("status");
                BigDecimal minAmount = null;
                BigDecimal maxAmount = null;
                String startDate = null;
                String endDate = null;

                amountObj = params.get("minAmount");
                if (amountObj != null) minAmount = new BigDecimal(amountObj.toString());

                amountObj = params.get("maxAmount");
                if (amountObj != null) maxAmount = new BigDecimal(amountObj.toString());

                startDate = (String) params.get("startDate");
                endDate = (String) params.get("endDate");

                if ((minAmount != null || maxAmount != null || startDate != null || endDate != null) && status != null) {
                    result = orderService.queryByConditions(userId, status, minAmount, maxAmount, startDate, endDate);
                } else if (minAmount != null || maxAmount != null) {
                    result = orderService.queryByAmountRange(userId, minAmount, maxAmount);
                } else if (startDate != null || endDate != null) {
                    result = orderService.queryByDateRange(userId, startDate, endDate);
                } else if (status != null) {
                    result = orderService.queryByUserIdAndStatus(userId, status);
                } else {
                    result = orderService.queryByUserId(userId);
                }
                long durationMs = System.currentTimeMillis() - startTime;
                toolService.logCall("OrderTool", action, objectMapper.writeValueAsString(params), objectMapper.writeValueAsString(result), (int) durationMs);
                return ApiResponse.success(result);
            } else if ("query_order_detail".equals(action)) {
                String orderNo = (String) params.get("orderNo");
                Order order = orderService.queryByOrderNo(orderNo);
                long durationMs = System.currentTimeMillis() - startTime;
                toolService.logCall("OrderTool", action, objectMapper.writeValueAsString(params), objectMapper.writeValueAsString(order), (int) durationMs);
                return ApiResponse.success(order);
            } else if ("query_order_statistics".equals(action)) {
                String userId = (String) params.get("userId");
                BigDecimal minAmount = null;
                BigDecimal maxAmount = null;
                amountObj = params.get("minAmount");
                if (amountObj != null) minAmount = new BigDecimal(amountObj.toString());
                amountObj = params.get("maxAmount");
                if (amountObj != null) maxAmount = new BigDecimal(amountObj.toString());

                Long count;
                BigDecimal sum;
                if (minAmount != null || maxAmount != null) {
                    count = orderService.countByUserIdAndAmountRange(userId, minAmount, maxAmount);
                    sum = orderService.sumAmountByUserIdAndAmountRange(userId, minAmount, maxAmount);
                } else {
                    count = orderService.countByUserId(userId);
                    sum = orderService.sumAmountByUserId(userId);
                }
                BigDecimal avg = count > 0 ? sum.divide(BigDecimal.valueOf(count), 2, java.math.RoundingMode.HALF_UP) : BigDecimal.ZERO;
                OrderStatistics stats = new OrderStatistics(userId, count, sum, avg);
                long durationMs = System.currentTimeMillis() - startTime;
                toolService.logCall("OrderTool", action, objectMapper.writeValueAsString(params), objectMapper.writeValueAsString(stats), (int) durationMs);
                return ApiResponse.success(stats);
            }
            return ApiResponse.error("未知 action: " + action);
        } catch (Exception e) {
            long durationMs = System.currentTimeMillis() - startTime;
            try {
                toolService.logCall("OrderTool", request.getAction(), objectMapper.writeValueAsString(request.getParams()), e.getMessage(), (int) durationMs);
            } catch (Exception ignored) {}
            return ApiResponse.error("查询失败: " + e.getMessage());
        }
    }

    @PostMapping("/user/query")
    public ApiResponse<?> queryUser(@RequestBody ToolRequest request) {
        long startTime = System.currentTimeMillis();
        try {
            String action = request.getAction();
            var params = request.getParams();
            if ("query_user_info".equals(action)) {
                String userId = (String) params.get("userId");
                User user = userService.queryByUserId(userId);
                long durationMs = System.currentTimeMillis() - startTime;
                toolService.logCall("UserTool", action, objectMapper.writeValueAsString(params), objectMapper.writeValueAsString(user), (int) durationMs);
                return ApiResponse.success(user);
            }
            return ApiResponse.error("未知 action: " + action);
        } catch (Exception e) {
            long durationMs = System.currentTimeMillis() - startTime;
            try {
                toolService.logCall("UserTool", request.getAction(), objectMapper.writeValueAsString(request.getParams()), e.getMessage(), (int) durationMs);
            } catch (Exception ignored) {}
            return ApiResponse.error("查询失败: " + e.getMessage());
        }
    }

    @PostMapping("/inventory/query")
    public ApiResponse<?> queryInventory(@RequestBody ToolRequest request) {
        long startTime = System.currentTimeMillis();
        try {
            String action = request.getAction();
            var params = request.getParams();
            List<Inventory> result;
            if ("query_inventory".equals(action)) {
                String sku = (String) params.get("sku");
                result = inventoryService.queryBySku(sku);
                long durationMs = System.currentTimeMillis() - startTime;
                toolService.logCall("InventoryTool", action, objectMapper.writeValueAsString(params), objectMapper.writeValueAsString(result), (int) durationMs);
                return ApiResponse.success(result);
            } else if ("query_warehouse_stock".equals(action)) {
                String warehouse = (String) params.get("warehouse");
                result = inventoryService.queryByWarehouse(warehouse);
                long durationMs = System.currentTimeMillis() - startTime;
                toolService.logCall("InventoryTool", action, objectMapper.writeValueAsString(params), objectMapper.writeValueAsString(result), (int) durationMs);
                return ApiResponse.success(result);
            }
            return ApiResponse.error("未知 action: " + action);
        } catch (Exception e) {
            long durationMs = System.currentTimeMillis() - startTime;
            try {
                toolService.logCall("InventoryTool", request.getAction(), objectMapper.writeValueAsString(request.getParams()), e.getMessage(), (int) durationMs);
            } catch (Exception ignored) {}
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
