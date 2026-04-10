package com.example.agent.service;

import com.example.agent.mapper.OrderMapper;
import com.example.agent.model.Order;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.math.BigDecimal;
import java.util.List;

@Service
public class OrderService {
    @Autowired
    private OrderMapper orderMapper;

    public List<Order> queryByUserId(String userId) {
        return orderMapper.selectByUserId(userId);
    }

    public List<Order> queryByUserIdAndStatus(String userId, String status) {
        return orderMapper.selectByUserIdAndStatus(userId, status);
    }

    public Order queryByOrderNo(String orderNo) {
        return orderMapper.selectByOrderNo(orderNo);
    }

    // 按金额范围查询
    public List<Order> queryByAmountRange(String userId, BigDecimal minAmount, BigDecimal maxAmount) {
        return orderMapper.selectByAmountRange(userId, minAmount, maxAmount);
    }

    // 按日期范围查询
    public List<Order> queryByDateRange(String userId, String startDate, String endDate) {
        return orderMapper.selectByDateRange(userId, startDate, endDate);
    }

    // 多条件组合查询
    public List<Order> queryByConditions(String userId, String status, BigDecimal minAmount,
                                         BigDecimal maxAmount, String startDate, String endDate) {
        return orderMapper.selectByConditions(userId, status, minAmount, maxAmount, startDate, endDate);
    }

    // 聚合统计
    public Long countByUserId(String userId) {
        return orderMapper.countByUserId(userId);
    }

    public BigDecimal sumAmountByUserId(String userId) {
        return orderMapper.sumAmountByUserId(userId);
    }

    public BigDecimal avgAmountByUserId(String userId) {
        return orderMapper.avgAmountByUserId(userId);
    }

    // 带金额过滤的聚合统计
    public Long countByUserIdAndAmountRange(String userId, BigDecimal minAmount, BigDecimal maxAmount) {
        return orderMapper.countByUserIdAndAmountRange(userId, minAmount, maxAmount);
    }

    public BigDecimal sumAmountByUserIdAndAmountRange(String userId, BigDecimal minAmount, BigDecimal maxAmount) {
        return orderMapper.sumAmountByUserIdAndAmountRange(userId, minAmount, maxAmount);
    }
}
