package com.dam.core.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class HealthSummaryDTO {
    private Integer totalSteps;
    private Double totalActiveCalories;
}
