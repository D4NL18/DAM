package com.dam.core.config;

import com.google.cloud.firestore.Firestore;
import com.google.firebase.cloud.FirestoreClient;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.DependsOn;

@Configuration
@DependsOn("firebaseConfig")
public class FirestoreConfig {

    @Bean
    public Firestore firestore() {
        return FirestoreClient.getFirestore();
    }
}
