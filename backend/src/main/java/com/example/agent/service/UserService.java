package com.example.agent.service;

import com.example.agent.mapper.UserMapper;
import com.example.agent.model.User;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class UserService {
    @Autowired
    private UserMapper userMapper;

    public User queryByUserId(String userId) {
        return userMapper.selectByUserId(userId);
    }
}
