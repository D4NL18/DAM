package com.dam.core.controller;

import com.dam.core.dto.LoginRequest;
import com.dam.core.dto.LoginResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/auth")
@Tag(name = "Auth", description = "Endpoints de autenticação de usuários do Dashboard")
public class AuthController {

    @PostMapping("/login")
    @Operation(summary = "Autentica usuário do Dashboard com validação segura de credenciais")
    public ResponseEntity<LoginResponse> login(@Valid @RequestBody LoginRequest request) {
        String username = request.getUsername() != null ? request.getUsername().trim() : "";
        String password = request.getPassword() != null ? request.getPassword().trim() : "";

        if (username.equalsIgnoreCase("Daniel") && password.equals("Dm12031994@@")) {
            return ResponseEntity.ok(LoginResponse.builder()
                    .authenticated(true)
                    .userId("daniel")
                    .name("Daniel")
                    .role("admin")
                    .token(UUID.randomUUID().toString())
                    .build());
        } else if (username.equalsIgnoreCase("Lari") && password.equals("Lilalink10")) {
            return ResponseEntity.ok(LoginResponse.builder()
                    .authenticated(true)
                    .userId("lari")
                    .name("Lari")
                    .role("user")
                    .token(UUID.randomUUID().toString())
                    .build());
        }

        return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                .body(LoginResponse.builder()
                        .authenticated(false)
                        .build());
    }
}
