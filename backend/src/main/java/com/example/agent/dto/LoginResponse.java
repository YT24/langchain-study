package com.example.agent.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class LoginResponse {
    private Long userId;
    private String token;
    private String username;
    private String nickname;
    private String role;
    private Long expiresIn;
}
