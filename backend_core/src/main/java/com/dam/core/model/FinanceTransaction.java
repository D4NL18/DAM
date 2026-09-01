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
public class FinanceTransaction {
    private String id;
    private Double amount;
    private String category;
    private String description;
    private LocalDateTime date;
}
