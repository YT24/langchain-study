package com.example.agent.model;

import lombok.Data;
import java.math.BigDecimal;

@Data
public class User {
    private Long id;
    private String userId;
    private String name;
    private String phone;
    private String level;
    private BigDecimal balance;
    private String createdAt;
}
