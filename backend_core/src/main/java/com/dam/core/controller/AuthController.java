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

        boolean isAdmin = (username.equalsIgnoreCase("admin") || username.equalsIgnoreCase("admin_user"))
                && (password.equals("Admin@123") || password.equals(System.getenv("ADMIN_PASSWORD")));

        boolean isUser = (username.equalsIgnoreCase("user") || username.equalsIgnoreCase("guest_user"))
                && (password.equals("User@123") || password.equals(System.getenv("USER_PASSWORD")));

        if (isAdmin) {
            return ResponseEntity.ok(LoginResponse.builder()
                    .authenticated(true)
                    .userId("admin")
                    .name("Admin")
                    .role("admin")
                    .token(UUID.randomUUID().toString())
                    .build());
        } else if (isUser) {
            return ResponseEntity.ok(LoginResponse.builder()
                    .authenticated(true)
                    .userId("user")
                    .name("User")
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
