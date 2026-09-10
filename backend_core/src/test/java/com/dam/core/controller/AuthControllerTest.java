package com.dam.core.controller;

import com.dam.core.dto.LoginRequest;
import com.dam.core.dto.LoginResponse;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import static org.junit.jupiter.api.Assertions.*;

public class AuthControllerTest {

    private final AuthController authController = new AuthController();

    @Test
    public void testLoginAdminSuccess() {
        LoginRequest request = LoginRequest.builder()
                .username("admin")
                .password("Admin@123")
                .build();

        ResponseEntity<LoginResponse> response = authController.login(request);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertTrue(response.getBody().isAuthenticated());
        assertEquals("admin", response.getBody().getUserId());
        assertEquals("Admin", response.getBody().getName());
        assertEquals("admin", response.getBody().getRole());
        assertNotNull(response.getBody().getToken());
    }

    @Test
    public void testLoginUserSuccess() {
        LoginRequest request = LoginRequest.builder()
                .username("user")
                .password("User@123")
                .build();

        ResponseEntity<LoginResponse> response = authController.login(request);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertTrue(response.getBody().isAuthenticated());
        assertEquals("user", response.getBody().getUserId());
        assertEquals("User", response.getBody().getName());
        assertEquals("user", response.getBody().getRole());
        assertNotNull(response.getBody().getToken());
    }

    @Test
    public void testLoginInvalidCredentials() {
        LoginRequest request = LoginRequest.builder()
                .username("admin")
                .password("WrongPassword")
                .build();

        ResponseEntity<LoginResponse> response = authController.login(request);

        assertEquals(HttpStatus.UNAUTHORIZED, response.getStatusCode());
        assertNotNull(response.getBody());
        assertFalse(response.getBody().isAuthenticated());
    }
}
