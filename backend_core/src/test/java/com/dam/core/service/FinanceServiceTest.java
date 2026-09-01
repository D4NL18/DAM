package com.dam.core.service;

import com.dam.core.dto.FinanceSummaryDTO;
import com.dam.core.model.FinanceTransaction;
import com.dam.core.repository.FinanceTransactionRepository;
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
public class FinanceServiceTest {

    @Mock
    private FinanceTransactionRepository repository;

    @InjectMocks
    private FinanceService financeService;

    @Test
    public void testGetFinanceSummary() throws Exception {
        List<FinanceTransaction> mockTransactions = Arrays.asList(
                FinanceTransaction.builder().amount(100.0).category("Food").build(),
                FinanceTransaction.builder().amount(50.0).category("Food").build(),
                FinanceTransaction.builder().amount(200.0).category("Transport").build()
        );
        
        when(repository.findAll()).thenReturn(mockTransactions);

        FinanceSummaryDTO result = financeService.getFinanceSummary();

        assertEquals(350.0, result.getTotalAmount());
        assertEquals(150.0, result.getExpensesByCategory().get("Food"));
        assertEquals(200.0, result.getExpensesByCategory().get("Transport"));
    }
}
