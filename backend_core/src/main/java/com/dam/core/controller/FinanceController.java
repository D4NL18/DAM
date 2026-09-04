package com.dam.core.controller;

import com.dam.core.dto.FinanceSummaryDTO;
import com.dam.core.service.FinanceService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/finance")
@RequiredArgsConstructor
@Tag(name = "Finance", description = "Endpoints para transações financeiras")
public class FinanceController {

    private final FinanceService financeService;

    @GetMapping("/summary")
    @Operation(summary = "Obtém um resumo agregado das finanças por usuário")
    public ResponseEntity<FinanceSummaryDTO> getSummary(
            @RequestParam(value = "userId", required = false) String userId,
            @RequestHeader(value = "X-User-Id", required = false) String headerUserId) {
        try {
            String effectiveUserId = (userId != null && !userId.isBlank()) ? userId : headerUserId;
            return ResponseEntity.ok(financeService.getFinanceSummary(effectiveUserId));
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }
}
