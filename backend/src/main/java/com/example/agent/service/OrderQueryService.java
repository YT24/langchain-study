package com.example.agent.service;

import com.example.agent.model.Order;
import com.example.agent.model.OrderStatistics;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

@Service
public class OrderQueryService {

    @Autowired
    private OrderService orderService;

    public Object execute(String action, Map<String, Object> params) {
        return switch (action) {
            case "query_order_list" -> queryOrderList(params);
            case "query_order_detail" -> queryOrderDetail(params);
            case "query_order_statistics" -> queryOrderStatistics(params);
            default -> throw new IllegalArgumentException("未知 action: " + action);
        };
    }

    private List<Order> queryOrderList(Map<String, Object> params) {
        String userId = (String) params.get("userId");
        String status = (String) params.get("status");
        BigDecimal minAmount = parseAmount(params.get("minAmount"));
        BigDecimal maxAmount = parseAmount(params.get("maxAmount"));
        String startDate = (String) params.get("startDate");
        String endDate = (String) params.get("endDate");

        List<Order> result;
        if ((minAmount != null || maxAmount != null || startDate != null || endDate != null) && status != null) {
            result = orderService.queryByConditions(userId, status, minAmount, maxAmount, startDate, endDate);
        } else if (minAmount != null || maxAmount != null) {
            result = orderService.queryByAmountRange(userId, minAmount, maxAmount);
        } else if (startDate != null || endDate != null) {
            result = orderService.queryByDateRange(userId, startDate, endDate);
        } else if (status != null) {
            result = orderService.queryByUserIdAndStatus(userId, status);
        } else {
            result = orderService.queryByUserId(userId);
        }
        return result;
    }

    private Order queryOrderDetail(Map<String, Object> params) {
        String orderNo = (String) params.get("orderNo");
        return orderService.queryByOrderNo(orderNo);
    }

    private OrderStatistics queryOrderStatistics(Map<String, Object> params) {
        String userId = (String) params.get("userId");
        BigDecimal minAmount = parseAmount(params.get("minAmount"));
        BigDecimal maxAmount = parseAmount(params.get("maxAmount"));

        Long count;
        BigDecimal sum;
        if (minAmount != null || maxAmount != null) {
            count = orderService.countByUserIdAndAmountRange(userId, minAmount, maxAmount);
            sum = orderService.sumAmountByUserIdAndAmountRange(userId, minAmount, maxAmount);
        } else {
            count = orderService.countByUserId(userId);
            sum = orderService.sumAmountByUserId(userId);
        }
        BigDecimal avg = count > 0 ? sum.divide(BigDecimal.valueOf(count), 2, java.math.RoundingMode.HALF_UP) : BigDecimal.ZERO;
        return new OrderStatistics(userId, count, sum, avg);
    }

    private BigDecimal parseAmount(Object amountObj) {
        if (amountObj == null) return null;
        return new BigDecimal(amountObj.toString());
    }
}
