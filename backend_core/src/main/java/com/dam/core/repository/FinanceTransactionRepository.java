package com.dam.core.repository;

import com.dam.core.model.FinanceTransaction;
import com.google.api.core.ApiFuture;
import com.google.cloud.firestore.Firestore;
import com.google.cloud.firestore.QueryDocumentSnapshot;
import com.google.cloud.firestore.QuerySnapshot;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutionException;

@Repository
@RequiredArgsConstructor
public class FinanceTransactionRepository {

    private final Firestore firestore;
    private static final String COLLECTION_NAME = "finances";

    public List<FinanceTransaction> findAll() throws ExecutionException, InterruptedException {
        return findAll("admin");
    }

    public List<FinanceTransaction> findAll(String targetUserId) throws ExecutionException, InterruptedException {
        ApiFuture<QuerySnapshot> future = firestore.collection(COLLECTION_NAME).get();
        List<QueryDocumentSnapshot> documents = future.get().getDocuments();
        
        List<FinanceTransaction> transactions = new ArrayList<>();
        String normalizedTarget = (targetUserId == null || targetUserId.isBlank()) ? "admin" : targetUserId.trim().toLowerCase();
        if ("daniel".equals(normalizedTarget)) {
            normalizedTarget = "admin";
        } else if ("lari".equals(normalizedTarget)) {
            normalizedTarget = "user";
        }

        for (QueryDocumentSnapshot document : documents) {
            FinanceTransaction transaction = document.toObject(FinanceTransaction.class);
            String docUserId = document.getString("userId");
            if (docUserId == null || docUserId.isBlank()) {
                docUserId = document.getString("user_id");
            }
            if (docUserId == null || docUserId.isBlank() || "daniel".equalsIgnoreCase(docUserId)) {
                docUserId = "admin";
            } else if ("lari".equalsIgnoreCase(docUserId)) {
                docUserId = "user";
            }
            if (docUserId.equalsIgnoreCase(normalizedTarget)) {
                transaction.setUserId(docUserId);
                transactions.add(transaction);
            }
        }
        return transactions;
    }
}
