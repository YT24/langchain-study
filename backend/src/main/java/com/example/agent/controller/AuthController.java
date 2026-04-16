package com.example.agent.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.agent.dto.LoginRequest;
import com.example.agent.dto.LoginResponse;
import com.example.agent.entity.SysUser;
import com.example.agent.mapper.SysUserMapper;
import com.example.agent.util.JwtUtils;
import com.example.agent.model.ApiResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;

@RestController
@RequestMapping("/api/auth")
@CrossOrigin(origins = "*")
public class AuthController {

    @Autowired
    private SysUserMapper userMapper;

    @Autowired
    private JwtUtils jwtUtils;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Value("${jwt.expiration:86400000}")
    private Long expiration;

    @PostMapping("/login")
    public ApiResponse<LoginResponse> login(@RequestBody LoginRequest request) {
        SysUser user = userMapper.selectOne(
            new LambdaQueryWrapper<SysUser>().eq(SysUser::getUsername, request.getUsername())
        );

        /*if (user == null || !passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            return ApiResponse.error("用户名或密码错误");
        }*/

        if (user.getStatus() != 1) {
            return ApiResponse.error("账号已被禁用");
        }

        user.setLastLoginAt(LocalDateTime.now());
        userMapper.updateById(user);

        String token = jwtUtils.generateToken(user.getId(), user.getUsername(), user.getRole());
        return ApiResponse.success(new LoginResponse(user.getId(), token, user.getUsername(), user.getNickname(), user.getRole(), expiration));
    }

    @PostMapping("/register")
    public ApiResponse<LoginResponse> register(@RequestBody LoginRequest request) {
        Long count = userMapper.selectCount(
            new LambdaQueryWrapper<SysUser>().eq(SysUser::getUsername, request.getUsername())
        );
        if (count > 0) {
            return ApiResponse.error("用户名已存在");
        }

        SysUser user = new SysUser();
        user.setUsername(request.getUsername());
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        user.setNickname(request.getUsername());
        user.setRole("USER");
        user.setStatus(1);
        userMapper.insert(user);

        String token = jwtUtils.generateToken(user.getId(), user.getUsername(), user.getRole());
        return ApiResponse.success(new LoginResponse(user.getId(), token, user.getUsername(), user.getNickname(), user.getRole(), expiration));
    }

    @GetMapping("/me")
    public ApiResponse<SysUser> getCurrentUser(@RequestAttribute("userId") Long userId) {
        SysUser user = userMapper.selectById(userId);
        if (user == null) {
            return ApiResponse.error("用户不存在");
        }
        user.setPassword(null);
        return ApiResponse.success(user);
    }
}
