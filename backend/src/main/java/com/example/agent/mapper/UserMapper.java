package com.example.agent.mapper;

import com.example.agent.model.User;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface UserMapper {
    User selectByUserId(String userId);
}
