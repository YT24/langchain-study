package com.example.agent.repository;

import com.example.agent.entity.ToolLog;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ToolLogRepository extends JpaRepository<ToolLog, Long> {
}
