package com.dam.core.service;

import com.dam.core.dto.FinanceSummaryDTO;
import com.dam.core.model.FinanceTransaction;
import com.dam.core.repository.FinanceTransactionRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class FinanceService {

    private final FinanceTransactionRepository repository;

    public FinanceSummaryDTO getFinanceSummary() throws Exception {
        return getFinanceSummary("admin");
    }

    public FinanceSummaryDTO getFinanceSummary(String userId) throws Exception {
        List<FinanceTransaction> transactions = repository.findAll(userId);
        
        double totalAmount = 0.0;
        Map<String, Double> expensesByCategory = new HashMap<>();
        
        for (FinanceTransaction transaction : transactions) {
            if (transaction.getAmount() != null) {
                totalAmount += transaction.getAmount();
                
                String category = transaction.getCategory() != null ? transaction.getCategory() : "Uncategorized";
                expensesByCategory.put(category, expensesByCategory.getOrDefault(category, 0.0) + transaction.getAmount());
            }
        }
        
        return FinanceSummaryDTO.builder()
                .totalAmount(totalAmount)
                .expensesByCategory(expensesByCategory)
                .build();
    }
}
