package com.example.agent.model;

import lombok.Data;
import java.math.BigDecimal;

@Data
public class Order {
    private Long id;
    private String orderNo;
    private String userId;
    private String status;
    private BigDecimal totalAmount;
    private String createdAt;
}
