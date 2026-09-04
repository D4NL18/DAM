package com.dam.core.service;

import com.dam.core.dto.HealthSummaryDTO;
import com.dam.core.model.HealthMetric;
import com.dam.core.repository.HealthMetricRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
public class HealthServiceTest {

    @Mock
    private HealthMetricRepository repository;

    @InjectMocks
    private HealthService healthService;

    @Test
    public void testGetHealthSummary() throws Exception {
        List<HealthMetric> mockMetrics = Arrays.asList(
                HealthMetric.builder().steps(5000).activeCalories(300.0).userId("daniel").build(),
                HealthMetric.builder().steps(3000).activeCalories(150.0).userId("daniel").build()
        );
        
        when(repository.findAll("daniel")).thenReturn(mockMetrics);

        HealthSummaryDTO result = healthService.getHealthSummary("daniel");

        assertEquals(8000, result.getTotalSteps());
        assertEquals(450.0, result.getTotalActiveCalories());
    }

    @Test
    public void testGetHealthSummaryLari() throws Exception {
        List<HealthMetric> mockMetrics = Arrays.asList(
                HealthMetric.builder().steps(7000).activeCalories(400.0).userId("lari").build()
        );
        
        when(repository.findAll("lari")).thenReturn(mockMetrics);

        HealthSummaryDTO result = healthService.getHealthSummary("lari");

        assertEquals(7000, result.getTotalSteps());
        assertEquals(400.0, result.getTotalActiveCalories());
    }
}
