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
    public void testLoginDanielSuccess() {
        LoginRequest request = LoginRequest.builder()
                .username("Daniel")
                .password("Dm12031994@@")
                .build();

        ResponseEntity<LoginResponse> response = authController.login(request);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertTrue(response.getBody().isAuthenticated());
        assertEquals("daniel", response.getBody().getUserId());
        assertEquals("Daniel", response.getBody().getName());
        assertEquals("admin", response.getBody().getRole());
        assertNotNull(response.getBody().getToken());
    }

    @Test
    public void testLoginLariSuccess() {
        LoginRequest request = LoginRequest.builder()
                .username("Lari")
                .password("Lilalink10")
                .build();

        ResponseEntity<LoginResponse> response = authController.login(request);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertTrue(response.getBody().isAuthenticated());
        assertEquals("lari", response.getBody().getUserId());
        assertEquals("Lari", response.getBody().getName());
        assertEquals("user", response.getBody().getRole());
        assertNotNull(response.getBody().getToken());
    }

    @Test
    public void testLoginInvalidCredentials() {
        LoginRequest request = LoginRequest.builder()
                .username("Daniel")
                .password("WrongPassword")
                .build();

        ResponseEntity<LoginResponse> response = authController.login(request);

        assertEquals(HttpStatus.UNAUTHORIZED, response.getStatusCode());
        assertNotNull(response.getBody());
        assertFalse(response.getBody().isAuthenticated());
    }
}
