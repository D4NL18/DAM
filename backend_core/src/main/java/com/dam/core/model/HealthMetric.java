package com.dam.core.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class HealthMetric {
    private String id;
    private Integer steps;
    private Double activeCalories;
    private LocalDateTime date;
    private String userId;
}
