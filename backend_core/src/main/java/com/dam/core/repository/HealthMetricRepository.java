package com.dam.core.repository;

import com.dam.core.model.HealthMetric;
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
public class HealthMetricRepository {

    private final Firestore firestore;
    private static final String COLLECTION_NAME = "health_metrics";

    public List<HealthMetric> findAll() throws ExecutionException, InterruptedException {
        ApiFuture<QuerySnapshot> future = firestore.collection(COLLECTION_NAME).get();
        List<QueryDocumentSnapshot> documents = future.get().getDocuments();
        
        List<HealthMetric> metrics = new ArrayList<>();
        for (QueryDocumentSnapshot document : documents) {
            metrics.add(document.toObject(HealthMetric.class));
        }
        return metrics;
    }
}
