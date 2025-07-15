"""Tests for authentication API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    def test_login_success(self, client: TestClient, test_user):
        """Test successful login."""
        login_data = {
            "username": test_user.email,
            "password": "testpassword123"
        }
        response = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client: TestClient, test_user):
        """Test login with invalid credentials."""
        login_data = {
            "username": test_user.email,
            "password": "wrongpassword"
        }
        response = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)
        
        assert response.status_code == 400
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "password123"
        }
        response = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)
        
        assert response.status_code == 400
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_test_token_valid(self, client: TestClient, auth_headers):
        """Test token validation with valid token."""
        response = client.post(
            f"{settings.API_V1_STR}/auth/login/test-token",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert data["email"] == "test@example.com"
    
    def test_test_token_invalid(self, client: TestClient):
        """Test token validation with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post(
            f"{settings.API_V1_STR}/auth/login/test-token",
            headers=headers
        )
        
        assert response.status_code == 403
        assert "Could not validate credentials" in response.json()["detail"]
    
    def test_test_token_missing(self, client: TestClient):
        """Test token validation without token."""
        response = client.post(f"{settings.API_V1_STR}/auth/login/test-token")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    def test_password_recovery(self, client: TestClient, test_user):
        """Test password recovery request."""
        response = client.post(
            f"{settings.API_V1_STR}/auth/password-recovery/{test_user.email}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Password recovery email sent" in data["msg"]
    
    def test_password_recovery_nonexistent_user(self, client: TestClient):
        """Test password recovery for non-existent user."""
        response = client.post(
            f"{settings.API_V1_STR}/auth/password-recovery/nonexistent@example.com"
        )
        
        # Should still return success to avoid user enumeration
        assert response.status_code == 200
        data = response.json()
        assert "If this email is registered" in data["msg"]
    
    def test_reset_password_invalid_token(self, client: TestClient):
        """Test password reset with invalid token."""
        reset_data = {
            "token": "invalid_token",
            "new_password": "newpassword123"
        }
        response = client.post(
            f"{settings.API_V1_STR}/auth/reset-password/",
            json=reset_data
        )
        
        assert response.status_code == 400
        assert "Invalid token" in response.json()["detail"]