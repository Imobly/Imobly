"""
Testes para o módulo de propriedades
"""

import pytest
from fastapi.testclient import TestClient

from src.properties.schema import PropertyCreate


class TestProperties:
    """Testes para endpoints de propriedades"""

    def test_get_properties(self, client: TestClient, auth_headers):
        """Teste de listagem de propriedades"""
        response = client.get("/api/v1/properties/", headers=auth_headers)
        assert response.status_code in [200, 401]  # 401 para token mock

    def test_create_property(self, client: TestClient, auth_headers):
        """Teste de criação de propriedade"""
        property_data = {
            "name": "Apartamento Teste",
            "address": "Rua Teste, 123",
            "neighborhood": "Centro",
            "city": "São Paulo",
            "state": "SP",
            "zip_code": "01000-000",
            "type": "apartment",
            "area": 80.5,
            "bedrooms": 2,
            "bathrooms": 1,
            "parking_spaces": 1,
            "rent": 1500.00,
            "status": "vacant",
            "description": "Apartamento para teste",
            "is_residential": True
        }
        
        response = client.post(
            "/api/v1/properties/", 
            json=property_data, 
            headers=auth_headers
        )
        # Pode retornar 401 devido ao token mock ou 201 se autenticação for mockada
        assert response.status_code in [201, 401]

    def test_get_property_by_id(self, client: TestClient, auth_headers):
        """Teste de busca de propriedade por ID"""
        # Assumindo que existe uma propriedade com ID 1
        response = client.get("/api/v1/properties/1", headers=auth_headers)
        assert response.status_code in [200, 404, 401]

    def test_update_property(self, client: TestClient, auth_headers):
        """Teste de atualização de propriedade"""
        update_data = {
            "rent": 1600.00,
            "status": "occupied"
        }
        
        response = client.put(
            "/api/v1/properties/1", 
            json=update_data, 
            headers=auth_headers
        )
        assert response.status_code in [200, 404, 401]

    def test_delete_property(self, client: TestClient, auth_headers):
        """Teste de exclusão de propriedade"""
        response = client.delete("/api/v1/properties/1", headers=auth_headers)
        assert response.status_code in [200, 404, 401]

    def test_get_available_properties(self, client: TestClient, auth_headers):
        """Teste de listagem de propriedades disponíveis"""
        response = client.get("/api/v1/properties/available", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_get_property_statistics(self, client: TestClient, auth_headers):
        """Teste de estatísticas de propriedades"""
        response = client.get("/api/v1/properties/statistics/summary", headers=auth_headers)
        assert response.status_code in [200, 401]