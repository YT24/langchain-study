package com.example.agent.model;

import lombok.Data;
import java.math.BigDecimal;

@Data
public class OrderStatistics {
    private Long orderCount;
    private BigDecimal totalAmount;
    private BigDecimal averageAmount;
    private String userId;

    public OrderStatistics(String userId, Long orderCount, BigDecimal totalAmount, BigDecimal averageAmount) {
        this.userId = userId;
        this.orderCount = orderCount;
        this.totalAmount = totalAmount;
        this.averageAmount = averageAmount;
    }
}
