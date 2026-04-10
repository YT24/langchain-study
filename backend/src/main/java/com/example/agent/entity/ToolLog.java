package com.example.agent.entity;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "tool_logs")
public class ToolLog {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "tool_name")
    private String toolName;

    @Column(name = "action")
    private String action;

    @Column(name = "params", columnDefinition = "JSON")
    private String params;

    @Column(name = "result", columnDefinition = "TEXT")
    private String result;

    @Column(name = "duration_ms")
    private Integer durationMs;

    @Column(name = "called_at")
    private LocalDateTime calledAt;
}
