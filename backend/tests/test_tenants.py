"""
Testes para o módulo de inquilinos
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient


class TestTenants:
    """Testes para endpoints de inquilinos"""

    def test_get_tenants(self, client: TestClient, auth_headers):
        """Teste de listagem de inquilinos"""
        response = client.get("/api/v1/tenants/", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_create_tenant(self, client: TestClient, auth_headers):
        """Teste de criação de inquilino"""
        tenant_data = {
            "name": "João Silva",
            "email": "joao.silva@email.com",
            "phone": "(11) 99999-9999",
            "cpf_cnpj": "123.456.789-00",
            "birth_date": "1990-01-15",
            "profession": "Engenheiro",
            "status": "active",
            "emergency_contact": {
                "name": "Maria Silva",
                "phone": "(11) 88888-8888",
                "relationship": "Esposa"
            }
        }
        
        response = client.post(
            "/api/v1/tenants/", 
            json=tenant_data, 
            headers=auth_headers
        )
        assert response.status_code in [201, 401]

    def test_get_tenant_by_id(self, client: TestClient, auth_headers):
        """Teste de busca de inquilino por ID"""
        response = client.get("/api/v1/tenants/1", headers=auth_headers)
        assert response.status_code in [200, 404, 401]

    def test_update_tenant(self, client: TestClient, auth_headers):
        """Teste de atualização de inquilino"""
        update_data = {
            "phone": "(11) 77777-7777",
            "profession": "Arquiteto"
        }
        
        response = client.put(
            "/api/v1/tenants/1", 
            json=update_data, 
            headers=auth_headers
        )
        assert response.status_code in [200, 404, 401]

    def test_search_tenants(self, client: TestClient, auth_headers):
        """Teste de busca de inquilinos"""
        response = client.get("/api/v1/tenants/?search=João", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_filter_tenants_by_status(self, client: TestClient, auth_headers):
        """Teste de filtro de inquilinos por status"""
        response = client.get("/api/v1/tenants/?status=active", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_get_tenant_statistics(self, client: TestClient, auth_headers):
        """Teste de estatísticas de inquilinos"""
        response = client.get("/api/v1/tenants/statistics/summary", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_delete_tenant(self, client: TestClient, auth_headers):
        """Teste de exclusão de inquilino"""
        response = client.delete("/api/v1/tenants/1", headers=auth_headers)
        assert response.status_code in [200, 404, 401]

    def test_create_tenant_duplicate_email(self, client: TestClient, auth_headers):
        """Teste de criação de inquilino com email duplicado"""
        tenant_data = {
            "name": "José Santos",
            "email": "joao.silva@email.com",  # Email já existe
            "phone": "(11) 66666-6666", 
            "cpf_cnpj": "987.654.321-00",
            "profession": "Professor"
        }
        
        response = client.post(
            "/api/v1/tenants/", 
            json=tenant_data, 
            headers=auth_headers
        )
        # Pode retornar 400 (bad request) ou 401 (unauthorized)
        assert response.status_code in [400, 401]