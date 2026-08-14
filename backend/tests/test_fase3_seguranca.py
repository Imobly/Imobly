"""
Testes de regressão da Fase 3 (A-01, A-03, A-07, A-08, A-09).

Os casos financeiros são os mais importantes: um erro de centavo aqui vira
cobrança indevida de multa e registro falso de inadimplência.
"""

from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient

from src.contracts.models import Contract
from src.core.supabase_storage_service import SupabaseStorageService
from src.payments.calculo import calcular_pagamento, dinheiro
from src.properties.models import Property
from src.tenants.models import Tenant

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64


class TestCalculoFinanceiro:
    """A-09 — o cálculo era em float; em dinheiro isso é defeito contábil."""

    def test_pagamento_exato_nao_vira_parcial(self):
        """
        Regressão direta do bug do float: 2500 * 1.02 dá 2550.0000000000005 em
        ponto flutuante, então o pagamento exato caía como 'parcial' e gerava
        cobrança indevida.
        """
        calc = calcular_pagamento(
            aluguel=Decimal("2500.00"),
            taxa_multa=Decimal("2"),
            taxa_juros=Decimal("0"),
            vencimento=date(2026, 1, 1),
            data_pagamento=date(2026, 1, 2),
            valor_pago=Decimal("2550.00"),
        )
        assert calc.total_devido == Decimal("2550.00")
        assert calc.situacao == "pago", "pagamento exato classificado como parcial"
        assert calc.restante == Decimal("0.00")

    def test_sem_atraso_nao_cobra_multa_nem_juros(self):
        calc = calcular_pagamento(
            aluguel=Decimal("1000"), taxa_multa=Decimal("10"), taxa_juros=Decimal("5"),
            vencimento=date(2026, 3, 10), data_pagamento=date(2026, 3, 10),
            valor_pago=Decimal("1000"),
        )
        assert calc.multa == Decimal("0")
        assert calc.juros == Decimal("0")
        assert calc.dias_atraso == 0
        assert calc.situacao == "pago"

    def test_pagamento_antecipado_nao_gera_atraso(self):
        calc = calcular_pagamento(
            aluguel=Decimal("1000"), taxa_multa=Decimal("10"), taxa_juros=Decimal("5"),
            vencimento=date(2026, 3, 10), data_pagamento=date(2026, 3, 1),
            valor_pago=Decimal("1000"),
        )
        assert calc.dias_atraso == 0
        assert calc.total_devido == Decimal("1000.00")

    def test_juros_proporcionais_ao_atraso(self):
        """Multa é fixa; juros crescem com os dias."""
        comum = dict(
            aluguel=Decimal("1000"), taxa_multa=Decimal("2"), taxa_juros=Decimal("3"),
            vencimento=date(2026, 1, 1), valor_pago=Decimal("0"),
        )
        um_mes = calcular_pagamento(**comum, data_pagamento=date(2026, 1, 31))
        dois_meses = calcular_pagamento(**comum, data_pagamento=date(2026, 3, 1))

        assert um_mes.multa == dois_meses.multa, "multa deve ser fixa"
        assert dois_meses.juros > um_mes.juros
        assert um_mes.juros == Decimal("30.00")  # 1000 * 3% * (30/30)

    def test_valor_pago_zero_com_atraso_fica_atrasado(self):
        """Situação 'atrasado' era inalcançável por causa do bug do A-08."""
        calc = calcular_pagamento(
            aluguel=Decimal("1000"), taxa_multa=Decimal("2"), taxa_juros=Decimal("1"),
            vencimento=date(2026, 1, 1), data_pagamento=date(2026, 2, 1),
            valor_pago=Decimal("0"),
        )
        assert calc.situacao == "atrasado"

    def test_pagamento_parcial(self):
        calc = calcular_pagamento(
            aluguel=Decimal("1000"), taxa_multa=Decimal("0"), taxa_juros=Decimal("0"),
            vencimento=date(2026, 1, 1), data_pagamento=date(2026, 1, 1),
            valor_pago=Decimal("400"),
        )
        assert calc.situacao == "parcial"
        assert calc.restante == Decimal("600.00")

    def test_arredondamento_em_centavos(self):
        assert dinheiro("10.005") == Decimal("10.01")   # meio centavo sobe
        assert dinheiro("10.004") == Decimal("10.00")
        assert dinheiro(None) == Decimal("0.00")


@pytest.fixture
def cenario(db_session, make_user):
    user = make_user("fase3@imobly.com.br", "99999999-9999-4999-8999-999999999999")
    db_session.flush()

    prop = Property(
        user_id=user.id, name="Imóvel", address="Rua Z, 9", neighborhood="Centro",
        city="São Paulo", state="SP", zip_code="01000-000", type="apartment",
        area=70, bedrooms=2, bathrooms=1, parking_spaces=1, rent=2000, status="vacant",
    )
    tenant = Tenant(
        user_id=user.id, name="Inquilino", email="f3@imobly.com.br",
        phone="11999999999", cpf_cnpj="55566677788", profession="Analista",
    )
    db_session.add_all([prop, tenant])
    db_session.flush()

    contrato = Contract(
        user_id=user.id, title="Locação", property_id=prop.id, tenant_id=tenant.id,
        start_date=date.today() - timedelta(days=30),
        end_date=date.today() + timedelta(days=335),
        rent=Decimal("2000"), deposit=2000,
        interest_rate=Decimal("1"), fine_rate=Decimal("2"), status="ativo",
    )
    db_session.add(contrato)
    db_session.flush()
    return {"user": user, "prop": prop, "tenant": tenant, "contrato": contrato}


class TestRegistroDePagamento:
    """A-08 — registrar cobrança em aberto devolvia 500."""

    def test_valor_pago_zero_devolve_201_e_nao_500(self, client_as, cenario):
        client: TestClient = client_as(cenario["user"].id)
        r = client.post("/api/v1/payments/register", json={
            "contract_id": cenario["contrato"].id,
            "due_date": str(date.today() - timedelta(days=10)),
            "payment_date": str(date.today()),
            "paid_amount": 0,
        })
        assert r.status_code == 201, f"esperado 201, veio {r.status_code}: {r.text}"
        assert r.json()["status"] == "atrasado"

    def test_multa_e_juros_gravados_separadamente(self, client_as, cenario):
        """Somados num campo só, a composição da cobrança não era auditável."""
        client: TestClient = client_as(cenario["user"].id)
        r = client.post("/api/v1/payments/register", json={
            "contract_id": cenario["contrato"].id,
            "due_date": str(date.today() - timedelta(days=30)),
            "payment_date": str(date.today()),
            "paid_amount": 100,
        })
        assert r.status_code == 201, r.text
        corpo = r.json()
        assert Decimal(str(corpo["fine_amount"])) == Decimal("40.00")     # 2000 * 2%
        assert Decimal(str(corpo["interest_amount"])) == Decimal("20.00")  # 2000 * 1% * 30/30

    def test_calculate_e_register_concordam(self, client_as, cenario):
        """As duas rotas duplicavam o cálculo e já divergiam."""
        client: TestClient = client_as(cenario["user"].id)
        corpo = {
            "contract_id": cenario["contrato"].id,
            "due_date": str(date.today() - timedelta(days=15)),
            "payment_date": str(date.today()),
            "paid_amount": 500,
        }
        simulado = client.post("/api/v1/payments/calculate", json=corpo).json()
        registrado = client.post("/api/v1/payments/register", json=corpo).json()

        assert Decimal(str(simulado["fine_amount"])) == Decimal(str(registrado["fine_amount"]))
        assert Decimal(str(simulado["interest_amount"])) == Decimal(
            str(registrado["interest_amount"])
        )
        assert simulado["status"] == registrado["status"]


class TestAtomicidade:
    """A-03 — operações multi-etapa eram dois commits separados."""

    def test_contrato_e_imovel_na_mesma_transacao(self, client_as, cenario, db_session):
        client: TestClient = client_as(cenario["user"].id)
        # O cenário já tem contrato ativo indo até hoje+335; este começa depois,
        # para não esbarrar na constraint anti-dupla-locação (revisão 0010).
        inicio = date.today() + timedelta(days=400)
        r = client.post("/api/v1/contracts/", json={
            "title": "Novo", "property_id": cenario["prop"].id,
            "tenant_id": cenario["tenant"].id,
            "start_date": str(inicio),
            "end_date": str(inicio + timedelta(days=365)),
            "rent": 1500, "deposit": 0, "interest_rate": 0, "fine_rate": 0,
            "status": "ativo",
        })
        assert r.status_code == 201, r.text

        db_session.refresh(cenario["prop"])
        assert cenario["prop"].status == "occupied"
        assert cenario["prop"].tenant_id == cenario["tenant"].id

    def test_bulk_confirm_e_tudo_ou_nada(self, client_as, cenario, db_session):
        """
        Antes era um commit por item: ids inválidos eram ignorados em silêncio
        e a resposta era 200 com o lote parcialmente aplicado.
        """
        client: TestClient = client_as(cenario["user"].id)
        criado = client.post("/api/v1/payments/register", json={
            "contract_id": cenario["contrato"].id,
            "due_date": str(date.today()),
            "payment_date": str(date.today()),
            "paid_amount": 0,
        })
        assert criado.status_code == 201
        pagamento_id = criado.json()["id"]

        r = client.post("/api/v1/payments/bulk-confirm/", json={
            "payment_ids": [pagamento_id, 999999],  # segundo não existe
        })
        assert r.status_code == 404, "id inexistente foi ignorado silenciosamente"

        # E o primeiro NÃO pode ter sido confirmado (tudo ou nada)
        atual = client.get(f"/api/v1/payments/{pagamento_id}").json()
        assert atual["status"] != "pago", "lote foi parcialmente aplicado"


class TestValidacaoDeUpload:
    """A-07 — validação só por extensão, SVG público e path traversal."""

    @pytest.fixture
    def servico(self):
        return SupabaseStorageService.__new__(SupabaseStorageService)

    def _upload(self, nome: str, conteudo: bytes) -> UploadFile:
        return UploadFile(filename=nome, file=BytesIO(conteudo))

    def test_svg_nao_e_mais_aceito_como_imagem(self, servico):
        """SVG é XML executável; servido em bucket público vira XSS armazenado."""
        assert ".svg" not in SupabaseStorageService.ALLOWED_EXTENSIONS["images"]
        assert ".svg" not in SupabaseStorageService.ALLOWED_EXTENSIONS["all"]

    def test_conteudo_incompativel_com_extensao_e_rejeitado(self, servico):
        """Executável renomeado para .png passava direto."""
        arquivo = self._upload("malicioso.png", b"MZ\x90\x00" + b"\x00" * 64)
        with pytest.raises(HTTPException) as exc:
            servico._validate_file(arquivo, "images")
        assert exc.value.status_code == 400
        assert "não corresponde" in exc.value.detail

    def test_png_valido_passa(self, servico):
        servico._validate_file(self._upload("foto.png", PNG), "images")

    def test_jpeg_valido_passa(self, servico):
        servico._validate_file(self._upload("foto.jpg", JPEG), "images")

    def test_arquivo_vazio_e_rejeitado(self, servico):
        with pytest.raises(HTTPException) as exc:
            servico._validate_file(self._upload("vazio.png", b""), "images")
        assert exc.value.status_code == 400

    @pytest.mark.parametrize("nome_malicioso", [
        "../../../etc/passwd.png",
        "..\\..\\windows\\system32\\config.png",
        "/absoluto/caminho.png",
        "....//....//escape.png",
    ])
    def test_path_traversal_e_neutralizado(self, servico, nome_malicioso):
        """
        O nome só trocava espaço por underscore, então dava para escrever fora
        do prefixo {user_id}/ — cruzando a fronteira entre clientes.
        """
        caminho = servico._generate_file_path(42, "properties", nome_malicioso)
        assert caminho.startswith("42/properties/"), f"escapou do prefixo: {caminho}"
        assert ".." not in caminho
        assert "/" not in caminho[len("42/properties/"):]

    def test_nomes_diferentes_nao_colidem_no_mesmo_segundo(self, servico):
        """upsert=true + timestamp fazia uploads simultâneos se sobrescreverem."""
        a = servico._generate_file_path(1, "properties", "foto.png")
        b = servico._generate_file_path(1, "properties", "foto.png")
        assert a != b


class TestRateLimitAtivo:
    """
    A-01 — exercita as rotas com o rate limiting LIGADO.

    A suíte roda com `RATE_LIMIT_ENABLED=false` para não esbarrar nos limites,
    e isso escondeu um defeito: com `headers_enabled`, o slowapi exige um
    parâmetro `response: Response` no endpoint decorado, e sem ele TODA
    chamada a /auth/login respondia 500. O caminho só apareceu ao subir a
    aplicação de verdade.
    """

    @pytest.fixture
    def app_com_rate_limit(self, monkeypatch):
        """
        Reconstrói a app com o limiter ativo.

        A ordem dos reloads importa: os decoradores `@limiter.limit` são
        aplicados quando o ROUTER é importado, então recarregar só o módulo do
        limiter deixa as rotas presas à instância antiga (desativada).
        """
        import importlib
        import sys

        # `import src.auth.router as ar` devolveria o objeto APIRouter, não o
        # módulo: `src/auth/__init__.py` reexporta o nome `router`. Buscar em
        # `sys.modules` garante que estamos recarregando o módulo certo.
        nomes = ("src.core.rate_limit", "src.auth.router", "src.main")

        def _recarregar():
            for nome in nomes:
                importlib.reload(sys.modules[nome])
            return sys.modules["src.main"].app

        monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
        yield _recarregar()

        monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
        _recarregar()

    def test_login_bem_sucedido_nao_quebra_com_rate_limit_ligado(
        self, app_com_rate_limit
    ):
        """
        Este é o teste que pega o defeito.

        O slowapi injeta os cabeçalhos X-RateLimit-* SÓ no caminho de sucesso —
        quando o endpoint retorna normalmente. Um login que falha levanta
        HTTPException antes disso, então testar apenas credencial inválida
        passa mesmo com a rota quebrada. Foi assim que o defeito escapou: sem
        o parâmetro `response: Response`, todo login VÁLIDO respondia 500.
        """
        from src.auth.router import get_auth_repository

        class _RepoFalso:
            async def authenticate_user(self, email, senha):
                return {
                    "access_token": "token-de-teste",
                    "refresh_token": "refresh-de-teste",
                    "token_type": "Bearer",
                }

        app_com_rate_limit.dependency_overrides[get_auth_repository] = _RepoFalso
        try:
            cliente = TestClient(app_com_rate_limit)
            r = cliente.post(
                "/api/v1/auth/login",
                json={"username": "valido@imobly.com.br", "password": "correta"},
            )
            assert r.status_code == 200, f"login válido quebrou: {r.status_code} {r.text}"
            assert r.json()["access_token"] == "token-de-teste"
            # Os cabeçalhos são justamente o que exige `response: Response`.
            assert any(h.lower().startswith("x-ratelimit") for h in r.headers), (
                "cabeçalhos de rate limit ausentes"
            )
        finally:
            app_com_rate_limit.dependency_overrides.clear()

    def test_credencial_invalida_devolve_401(self, app_com_rate_limit):
        cliente = TestClient(app_com_rate_limit)
        r = cliente.post(
            "/api/v1/auth/login",
            json={"username": "ninguem@imobly.com.br", "password": "errada"},
        )
        assert r.status_code != 500, f"rate limiting quebrou a rota: {r.text}"
        assert r.status_code in (401, 429)

    def test_refresh_nao_quebra_com_rate_limit_ligado(self, app_com_rate_limit):
        cliente = TestClient(app_com_rate_limit)
        r = cliente.post("/api/v1/auth/refresh", json={"refresh_token": "invalido"})
        assert r.status_code != 500, f"rate limiting quebrou a rota: {r.text}"
        assert r.status_code in (401, 429)

    def test_excesso_de_tentativas_devolve_429(self, app_com_rate_limit):
        cliente = TestClient(app_com_rate_limit)
        codigos = [
            cliente.post(
                "/api/v1/auth/login",
                json={"username": "alvo@imobly.com.br", "password": "errada"},
            ).status_code
            for _ in range(8)
        ]
        assert 429 in codigos, f"força bruta não foi bloqueada: {codigos}"
        assert 500 not in codigos
