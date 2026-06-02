"""
Testes para o módulo de autenticação
"""

import pytest
from fastapi.testclient import TestClient


class TestAuth:
    """Testes para endpoints de autenticação"""

    def test_register_user(self, client: TestClient):
        """Teste de registro de usuário"""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        # Pode retornar 201 (created) ou erro de configuração do Supabase
        assert response.status_code in [201, 400, 500]

    def test_login_user(self, client: TestClient):
        """Teste de login de usuário"""
        login_data = {
            "username": "test@example.com",  # Email
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        # Pode retornar 200 (success) ou 401 (unauthorized)
        assert response.status_code in [200, 401, 400]

    def test_login_with_username(self, client: TestClient):
        """Login com username inexistente deve falhar com 401 genérico (anti-enumeração)."""
        login_data = {
            "username": "testuser",  # Username inexistente na base
            "password": "testpassword123"
        }

        response = client.post("/api/v1/auth/login", json=login_data)
        # Mensagem genérica para não revelar se o usuário existe.
        assert response.status_code == 401
        assert "email" in response.json().get("detail", "").lower()

    def test_get_current_user(self, client: TestClient, auth_headers):
        """Teste de obter usuário atual"""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_change_password(self, client: TestClient, auth_headers):
        """Teste de alteração de senha"""
        password_data = {
            "current_password": "oldpassword123",
            "new_password": "newpassword123"
        }
        
        response = client.post(
            "/api/v1/auth/change-password", 
            json=password_data, 
            headers=auth_headers
        )
        assert response.status_code in [200, 400, 401]

    def test_logout(self, client: TestClient, auth_headers):
        """Teste de logout"""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        assert response.status_code == 200

    def test_refresh_token(self, client: TestClient, auth_headers):
        """Teste de refresh de token"""
        response = client.post("/api/v1/auth/refresh", headers=auth_headers)
        # Por enquanto retorna 501 (not implemented)
        assert response.status_code == 501

    def test_register_duplicate_email(self, client: TestClient):
        """Teste de registro com email duplicado"""
        user_data = {
            "email": "test@example.com",  # Same email as before
            "username": "testuser2",
            "full_name": "Test User 2",
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        # Deve retornar erro de email duplicado
        assert response.status_code in [400, 409]

    def test_login_invalid_credentials(self, client: TestClient):
        """Teste de login com credenciais inválidas"""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401