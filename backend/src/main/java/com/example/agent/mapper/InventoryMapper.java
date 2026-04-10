package com.example.agent.mapper;

import com.example.agent.model.Inventory;
import org.apache.ibatis.annotations.Mapper;
import java.util.List;

@Mapper
public interface InventoryMapper {
    List<Inventory> selectBySku(String sku);
    List<Inventory> selectByWarehouse(String warehouse);
}
