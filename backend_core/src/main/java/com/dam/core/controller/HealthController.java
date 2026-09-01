package com.dam.core.controller;

import com.dam.core.dto.HealthSummaryDTO;
import com.dam.core.service.HealthService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/health")
@RequiredArgsConstructor
@Tag(name = "Health", description = "Endpoints para métricas de saúde")
public class HealthController {

    private final HealthService healthService;

    @GetMapping("/summary")
    @Operation(summary = "Obtém um resumo agregado das métricas de saúde")
    public ResponseEntity<HealthSummaryDTO> getSummary() {
        try {
            return ResponseEntity.ok(healthService.getHealthSummary());
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }
}
