package com.example.agent.service;

import com.example.agent.model.Inventory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

@Service
public class InventoryQueryService {

    @Autowired
    private InventoryService inventoryService;

    public Object execute(String action, Map<String, Object> params) {
        return switch (action) {
            case "query_inventory" -> queryBySku(params);
            case "query_warehouse_stock" -> queryByWarehouse(params);
            default -> throw new IllegalArgumentException("未知 action: " + action);
        };
    }

    private List<Inventory> queryBySku(Map<String, Object> params) {
        String sku = (String) params.get("sku");
        return inventoryService.queryBySku(sku);
    }

    private List<Inventory> queryByWarehouse(Map<String, Object> params) {
        String warehouse = (String) params.get("warehouse");
        return inventoryService.queryByWarehouse(warehouse);
    }
}
