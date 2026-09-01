package com.dam.core.service;

import com.dam.core.dto.HealthSummaryDTO;
import com.dam.core.model.HealthMetric;
import com.dam.core.repository.HealthMetricRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class HealthService {

    private final HealthMetricRepository repository;

    public HealthSummaryDTO getHealthSummary() throws Exception {
        List<HealthMetric> metrics = repository.findAll();
        
        int totalSteps = 0;
        double totalCalories = 0.0;
        
        for (HealthMetric metric : metrics) {
            if (metric.getSteps() != null) {
                totalSteps += metric.getSteps();
            }
            if (metric.getActiveCalories() != null) {
                totalCalories += metric.getActiveCalories();
            }
        }
        
        return HealthSummaryDTO.builder()
                .totalSteps(totalSteps)
                .totalActiveCalories(totalCalories)
                .build();
    }
}
