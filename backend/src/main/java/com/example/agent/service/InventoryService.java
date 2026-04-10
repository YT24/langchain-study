package com.example.agent.service;

import com.example.agent.mapper.InventoryMapper;
import com.example.agent.model.Inventory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class InventoryService {
    @Autowired
    private InventoryMapper inventoryMapper;

    public List<Inventory> queryBySku(String sku) {
        return inventoryMapper.selectBySku(sku);
    }

    public List<Inventory> queryByWarehouse(String warehouse) {
        return inventoryMapper.selectByWarehouse(warehouse);
    }
}
