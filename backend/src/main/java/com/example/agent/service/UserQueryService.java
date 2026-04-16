package com.example.agent.service;

import com.example.agent.model.User;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Map;

@Service
public class UserQueryService {

    @Autowired
    private UserService userService;

    public Object execute(String action, Map<String, Object> params) {
        return switch (action) {
            case "query_user_info" -> queryUserInfo(params);
            default -> throw new IllegalArgumentException("未知 action: " + action);
        };
    }

    private User queryUserInfo(Map<String, Object> params) {
        String userId = (String) params.get("userId");
        return userService.queryByUserId(userId);
    }
}
