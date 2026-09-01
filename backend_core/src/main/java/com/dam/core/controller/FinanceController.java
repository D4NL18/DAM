package com.dam.core.controller;

import com.dam.core.dto.FinanceSummaryDTO;
import com.dam.core.service.FinanceService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/finance")
@RequiredArgsConstructor
@Tag(name = "Finance", description = "Endpoints para transações financeiras")
public class FinanceController {

    private final FinanceService financeService;

    @GetMapping("/summary")
    @Operation(summary = "Obtém um resumo agregado das finanças")
    public ResponseEntity<FinanceSummaryDTO> getSummary() {
        try {
            return ResponseEntity.ok(financeService.getFinanceSummary());
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }
}
