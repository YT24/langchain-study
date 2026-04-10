package com.example.agent.model;

import lombok.Data;

@Data
public class Inventory {
    private Long id;
    private String sku;
    private String warehouse;
    private Integer quantity;
    private String updatedAt;
}
