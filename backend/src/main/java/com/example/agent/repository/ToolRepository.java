package com.example.agent.repository;

import com.example.agent.entity.Tool;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface ToolRepository extends JpaRepository<Tool, Long> {
    List<Tool> findByEnabledTrue();
    Tool findByName(String name);
}
