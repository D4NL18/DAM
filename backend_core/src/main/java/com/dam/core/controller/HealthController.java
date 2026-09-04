package com.dam.core.controller;

import com.dam.core.dto.HealthSummaryDTO;
import com.dam.core.service.HealthService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/health")
@RequiredArgsConstructor
@Tag(name = "Health", description = "Endpoints para métricas de saúde")
public class HealthController {

    private final HealthService healthService;

    @GetMapping("/summary")
    @Operation(summary = "Obtém um resumo agregado das métricas de saúde por usuário")
    public ResponseEntity<HealthSummaryDTO> getSummary(
            @RequestParam(value = "userId", required = false) String userId,
            @RequestHeader(value = "X-User-Id", required = false) String headerUserId) {
        try {
            String effectiveUserId = (userId != null && !userId.isBlank()) ? userId : headerUserId;
            return ResponseEntity.ok(healthService.getHealthSummary(effectiveUserId));
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }
}
