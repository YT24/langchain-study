package com.example.agent.mapper;

import com.example.agent.model.Order;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.math.BigDecimal;
import java.util.List;

@Mapper
public interface OrderMapper {
    List<Order> selectByUserId(String userId);
    List<Order> selectByUserIdAndStatus(String userId, String status);
    Order selectByOrderNo(String orderNo);

    // 统计查询
    List<Order> selectByAmountRange(@Param("userId") String userId,
                                    @Param("minAmount") BigDecimal minAmount,
                                    @Param("maxAmount") BigDecimal maxAmount);

    List<Order> selectByDateRange(@Param("userId") String userId,
                                  @Param("startDate") String startDate,
                                  @Param("endDate") String endDate);

    List<Order> selectByConditions(@Param("userId") String userId,
                                  @Param("status") String status,
                                  @Param("minAmount") BigDecimal minAmount,
                                  @Param("maxAmount") BigDecimal maxAmount,
                                  @Param("startDate") String startDate,
                                  @Param("endDate") String endDate);

    // 聚合统计
    Long countByUserId(String userId);
    BigDecimal sumAmountByUserId(String userId);
    BigDecimal avgAmountByUserId(String userId);

    // 带金额过滤的聚合统计
    Long countByUserIdAndAmountRange(String userId, BigDecimal minAmount, BigDecimal maxAmount);
    BigDecimal sumAmountByUserIdAndAmountRange(String userId, BigDecimal minAmount, BigDecimal maxAmount);
}
