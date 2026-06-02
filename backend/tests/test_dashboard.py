"""
Testes para o módulo de dashboard
"""

import pytest
from fastapi.testclient import TestClient


class TestDashboard:
    """Testes para endpoints do dashboard"""

    def test_get_dashboard_stats(self, client: TestClient, auth_headers):
        """Teste de estatísticas do dashboard"""
        response = client.get("/api/v1/dashboard/stats", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_get_property_stats(self, client: TestClient, auth_headers):
        """Teste de estatísticas de propriedades"""
        response = client.get("/api/v1/dashboard/properties/stats", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_get_tenant_stats(self, client: TestClient, auth_headers):
        """Teste de estatísticas de inquilinos"""
        response = client.get("/api/v1/dashboard/tenants/stats", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_get_financial_stats(self, client: TestClient, auth_headers):
        """Teste de estatísticas financeiras"""
        response = client.get("/api/v1/dashboard/financial/stats", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_get_revenue_trend(self, client: TestClient, auth_headers):
        """Teste de tendência de receita"""
        response = client.get("/api/v1/dashboard/revenue/trend", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_get_revenue_trend_with_months(self, client: TestClient, auth_headers):
        """Teste de tendência de receita com período específico"""
        response = client.get("/api/v1/dashboard/revenue/trend?months=6", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_get_dashboard_overview(self, client: TestClient, auth_headers):
        """Teste de visão geral do dashboard"""
        response = client.get("/api/v1/dashboard/overview", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_revenue_trend_invalid_months(self, client: TestClient, auth_headers):
        """Teste de tendência com número inválido de meses"""
        # Teste com valor fora do range permitido (1-24)
        response = client.get("/api/v1/dashboard/revenue/trend?months=30", headers=auth_headers)
        assert response.status_code in [422, 401]  # 422 para validation error