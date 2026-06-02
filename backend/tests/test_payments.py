"""
Testes para o módulo de pagamentos
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient


class TestPayments:
    """Testes para endpoints de pagamentos"""

    def test_get_payments(self, client: TestClient, auth_headers):
        """Teste de listagem de pagamentos"""
        response = client.get("/api/v1/payments/", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_create_payment(self, client: TestClient, auth_headers):
        """Teste de criação de pagamento"""
        payment_data = {
            "property_id": 1,
            "tenant_id": 1,
            "contract_id": 1,
            "due_date": "2024-03-01",
            "amount": 1500.00,
            "fine_amount": 0.00,
            "total_amount": 1500.00,
            "status": "pending",
            "description": "Pagamento de aluguel"
        }
        
        response = client.post(
            "/api/v1/payments/", 
            json=payment_data, 
            headers=auth_headers
        )
        assert response.status_code in [201, 401]

    def test_get_payment_by_id(self, client: TestClient, auth_headers):
        """Teste de busca de pagamento por ID"""
        response = client.get("/api/v1/payments/1", headers=auth_headers)
        assert response.status_code in [200, 404, 401]

    def test_update_payment(self, client: TestClient, auth_headers):
        """Teste de atualização de pagamento"""
        update_data = {
            "status": "paid",
            "payment_date": "2024-03-01",
            "payment_method": "pix"
        }
        
        response = client.put(
            "/api/v1/payments/1", 
            json=update_data, 
            headers=auth_headers
        )
        assert response.status_code in [200, 404, 401]

    def test_get_overdue_payments(self, client: TestClient, auth_headers):
        """Teste de listagem de pagamentos em atraso"""
        response = client.get("/api/v1/payments/overdue/list", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_filter_payments_by_property(self, client: TestClient, auth_headers):
        """Teste de filtro de pagamentos por propriedade"""
        response = client.get("/api/v1/payments/?property_id=1", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_filter_payments_by_tenant(self, client: TestClient, auth_headers):
        """Teste de filtro de pagamentos por inquilino"""
        response = client.get("/api/v1/payments/?tenant_id=1", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_filter_payments_by_status(self, client: TestClient, auth_headers):
        """Teste de filtro de pagamentos por status"""
        response = client.get("/api/v1/payments/?status=pending", headers=auth_headers)
        assert response.status_code in [200, 401]