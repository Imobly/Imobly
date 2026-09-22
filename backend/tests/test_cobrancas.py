"""
Testes da gestão de cobrança e inadimplência.

O caso que dá nome a tudo isto: aluguel de R$ 1.000, o inquilino paga R$ 600.
No modelo antigo esse saldo de R$ 400 não tinha onde existir — era calculado e
descartado — e o painel exibia os R$ 600 PAGOS como se fossem a dívida.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from src.charges.calculo import (
    Recebimento,
    calcular_posicao,
    faixa_aging,
    situacao_inquilino,
)
from src.charges.geracao import vencimento_na_competencia


VENCIMENTO = date(2026, 9, 10)


class TestPagamentoParcial:
    """O cenário central: pagou menos do que devia."""

    def test_saldo_restante_fica_registrado(self):
        posicao = calcular_posicao(
            rent_amount=1000,
            fine_rate=2,
            interest_rate=1,
            due_date=VENCIMENTO,
            recebimentos=[Recebimento(data=VENCIMENTO, valor=Decimal("600"))],
            hoje=VENCIMENTO,
        )
        assert posicao.status == "parcial"
        assert posicao.pago == Decimal("600.00")
        assert posicao.saldo == Decimal("400.00")

    def test_saldo_em_aberto_cresce_com_multa_e_juros(self):
        """
        Pagou 600 no vencimento e sumiu. Trinta dias depois a dívida NÃO é
        mais 400: multa de 2% e juros de 1% ao mês incidem sobre o aluguel.
        """
        depois = VENCIMENTO + timedelta(days=30)
        posicao = calcular_posicao(
            rent_amount=1000,
            fine_rate=2,
            interest_rate=1,
            due_date=VENCIMENTO,
            recebimentos=[Recebimento(data=VENCIMENTO, valor=Decimal("600"))],
            hoje=depois,
        )
        # 1000 + 20 (multa) + 10 (juros de 1 mês) = 1030; menos 600 recebidos
        assert posicao.multa == Decimal("20.00")
        assert posicao.juros == Decimal("10.00")
        assert posicao.saldo == Decimal("430.00")
        assert posicao.dias_atraso == 30

    def test_segundo_recebimento_quita_a_mesma_cobranca(self):
        """
        Os 400 pagos depois não podem virar uma dívida nova. No modelo antigo
        só havia duas saídas, ambas erradas: criar outra linha (que o painel
        somava como outra dívida) ou sobrescrever a primeira (perdendo a
        trilha).
        """
        segunda_data = VENCIMENTO + timedelta(days=10)
        posicao = calcular_posicao(
            rent_amount=1000,
            fine_rate=2,
            interest_rate=1,
            due_date=VENCIMENTO,
            recebimentos=[
                Recebimento(data=VENCIMENTO, valor=Decimal("600")),
                # 400 + 20 de multa + 3,33 de juros de 10 dias
                Recebimento(data=segunda_data, valor=Decimal("423.33")),
            ],
            hoje=segunda_data + timedelta(days=5),
        )
        assert posicao.status == "quitada"
        assert posicao.saldo == Decimal("0.00")
        assert posicao.data_quitacao == segunda_data

    def test_nao_paga_nada_fica_vencida_pelo_total(self):
        depois = VENCIMENTO + timedelta(days=5)
        posicao = calcular_posicao(
            rent_amount=1000,
            fine_rate=2,
            interest_rate=1,
            due_date=VENCIMENTO,
            hoje=depois,
        )
        assert posicao.status == "vencida"
        assert posicao.pago == Decimal("0.00")
        assert posicao.saldo == posicao.total_devido > Decimal("1000.00")


class TestCongelamentoDosEncargos:
    """Depois de quitar, a conta do inquilino para de correr."""

    def test_quitada_congela_encargos_na_data_do_pagamento(self):
        pagamento = VENCIMENTO + timedelta(days=5)
        # 1000 + 20 de multa + 1,67 de juros de 5 dias = 1021,67
        posicao = calcular_posicao(
            rent_amount=1000,
            fine_rate=2,
            interest_rate=1,
            due_date=VENCIMENTO,
            recebimentos=[Recebimento(data=pagamento, valor=Decimal("1021.67"))],
            hoje=VENCIMENTO + timedelta(days=200),
        )
        assert posicao.status == "quitada"
        assert posicao.referencia == pagamento
        assert posicao.dias_atraso == 5, "encargos continuaram correndo após a quitação"
        assert posicao.saldo == Decimal("0.00")

    def test_pagamento_em_dia_nao_gera_encargo(self):
        posicao = calcular_posicao(
            rent_amount=1000,
            fine_rate=2,
            interest_rate=1,
            due_date=VENCIMENTO,
            recebimentos=[Recebimento(data=VENCIMENTO - timedelta(days=2), valor=Decimal("1000"))],
            hoje=VENCIMENTO,
        )
        assert posicao.status == "quitada"
        assert posicao.multa == Decimal("0.00")
        assert posicao.juros == Decimal("0.00")


class TestStatusDerivado:
    def test_parcial_continua_parcial_depois_de_vencer(self):
        """
        O job diário antigo reescrevia `parcial` como `atrasado`, apagando a
        informação de que houve pagamento — justamente o dado que decide como
        cobrar.
        """
        posicao = calcular_posicao(
            rent_amount=1000,
            fine_rate=2,
            interest_rate=1,
            due_date=VENCIMENTO,
            recebimentos=[Recebimento(data=VENCIMENTO, valor=Decimal("600"))],
            hoje=VENCIMENTO + timedelta(days=45),
        )
        assert posicao.status == "parcial"
        assert posicao.dias_atraso == 45

    def test_aberta_antes_do_vencimento(self):
        posicao = calcular_posicao(
            rent_amount=1000, due_date=VENCIMENTO, hoje=VENCIMENTO - timedelta(days=3)
        )
        assert posicao.status == "aberta"
        assert posicao.dias_atraso == 0

    def test_cancelada_nao_e_recalculada(self):
        posicao = calcular_posicao(
            rent_amount=1000,
            fine_rate=2,
            due_date=VENCIMENTO,
            status_armazenado="cancelada",
            hoje=VENCIMENTO + timedelta(days=90),
        )
        assert posicao.status == "cancelada"
        assert posicao.saldo == Decimal("0.00")


class TestDescontoEEncargosDaCobranca:
    def test_condominio_entra_na_base_e_desconto_sai(self):
        posicao = calcular_posicao(
            rent_amount=1000,
            charges_amount=250,   # condomínio
            discount_amount=50,   # desconto de pontualidade
            due_date=VENCIMENTO,
            hoje=VENCIMENTO,
        )
        assert posicao.base == Decimal("1200.00")

    def test_multa_incide_sobre_a_base_ja_com_desconto(self):
        """Desconto de pontualidade abate o aluguel, não a penalidade."""
        posicao = calcular_posicao(
            rent_amount=1000,
            discount_amount=100,
            fine_rate=10,
            due_date=VENCIMENTO,
            hoje=VENCIMENTO + timedelta(days=1),
        )
        assert posicao.base == Decimal("900.00")
        assert posicao.multa == Decimal("90.00")


class TestAging:
    @pytest.mark.parametrize(
        "dias,esperado",
        [
            (0, "a_vencer"),
            (-5, "a_vencer"),
            (1, "d1_30"),
            (30, "d1_30"),
            (31, "d31_60"),
            (60, "d31_60"),
            (61, "d61_90"),
            (90, "d61_90"),
            (91, "d90_mais"),
            (400, "d90_mais"),
        ],
    )
    def test_faixas(self, dias, esperado):
        assert faixa_aging(dias) == esperado


class TestSituacaoDoInquilino:
    def test_em_dia_sem_saldo(self):
        assert situacao_inquilino(0, Decimal("0")) == "em_dia"

    def test_atraso_leve_ate_quinze_dias(self):
        assert situacao_inquilino(10, Decimal("400")) == "atraso_leve"

    def test_inadimplente_ate_sessenta(self):
        assert situacao_inquilino(45, Decimal("400")) == "inadimplente"

    def test_critico_acima_de_sessenta(self):
        """
        Derivado do PIOR atraso, não da média: quem deve há 90 dias e pagou os
        outros meses em dia continua sendo um problema de 90 dias.
        """
        assert situacao_inquilino(90, Decimal("3000")) == "critico"


class TestVencimentoNaCompetencia:
    def test_dia_31_em_mes_de_30_cai_no_ultimo_dia(self):
        assert vencimento_na_competencia(date(2026, 4, 1), 31) == date(2026, 4, 30)

    def test_fevereiro(self):
        """O caso que quebra na prática todo ano."""
        assert vencimento_na_competencia(date(2026, 2, 1), 30) == date(2026, 2, 28)

    def test_dia_normal(self):
        assert vencimento_na_competencia(date(2026, 9, 1), 10) == date(2026, 9, 10)


# ───────────────────────────────────────────────────────────────────────────
# Integração — o fluxo pela API, que é como o usuário vai exercitar isto
# ───────────────────────────────────────────────────────────────────────────

from fastapi.testclient import TestClient  # noqa: E402

from src.charges.models import Charge  # noqa: E402
from src.contracts.models import Contract  # noqa: E402
from src.properties.models import Property  # noqa: E402
from src.tenants.models import Tenant  # noqa: E402


@pytest.fixture
def carteira(db_session, make_user):
    """Um locador, um imóvel, um inquilino e um contrato de R$ 1.000."""
    user = make_user("cobrancas@imobly.com.br", "cccccccc-cccc-4ccc-8ccc-cccccccccccc")
    db_session.flush()

    prop = Property(
        user_id=user.id, name="Ap 101", address="Rua A, 1", neighborhood="Centro",
        city="São Paulo", state="SP", zip_code="01000-000", type="apartment",
        area=70, bedrooms=2, bathrooms=1, parking_spaces=1, rent=1000, status="occupied",
    )
    tenant = Tenant(
        user_id=user.id, name="João Inquilino", email="joao@imobly.com.br",
        phone="11999999999", cpf_cnpj="99988877766", profession="Analista",
    )
    db_session.add_all([prop, tenant])
    db_session.flush()

    contrato = Contract(
        user_id=user.id, title="Locação Ap 101", property_id=prop.id, tenant_id=tenant.id,
        start_date=date.today() - timedelta(days=365),
        end_date=date.today() + timedelta(days=365),
        rent=1000, deposit=0, interest_rate=1, fine_rate=2, due_day=10, status="ativo",
    )
    db_session.add(contrato)
    db_session.flush()
    return {"user": user, "prop": prop, "tenant": tenant, "contrato": contrato}


def _cobranca_vencida(carteira, dias: int, status: str = "aberta") -> Charge:
    vencimento = date.today() - timedelta(days=dias)
    return Charge(
        user_id=carteira["user"].id,
        property_id=carteira["prop"].id,
        tenant_id=carteira["tenant"].id,
        contract_id=carteira["contrato"].id,
        competencia=vencimento.replace(day=1),
        due_date=vencimento,
        rent_amount=1000,
        charges_amount=0,
        discount_amount=0,
        fine_rate=0,
        interest_rate=0,
        status=status,
    )


class TestFluxoDeCobrancaPelaAPI:
    def test_geracao_mensal_e_idempotente(self, client_as, carteira):
        """Clicar duas vezes no botão não pode cobrar o inquilino em dobro."""
        client: TestClient = client_as(carteira["user"].id)

        primeira = client.post("/api/v1/charges/generate", json={})
        assert primeira.status_code == 200, primeira.text
        assert primeira.json()["created"] == 1

        segunda = client.post("/api/v1/charges/generate", json={})
        assert segunda.json()["created"] == 0
        assert segunda.json()["skipped_existing"] == 1

    def test_pagamento_parcial_deixa_saldo_visivel(self, client_as, carteira):
        """O caso que motivou tudo: 1.000 devidos, 600 pagos."""
        client: TestClient = client_as(carteira["user"].id)
        charge_id = client.post("/api/v1/charges/generate", json={}).json()["charge_ids"][0]

        resposta = client.post(
            f"/api/v1/charges/{charge_id}/entries",
            json={"date": date.today().isoformat(), "amount": "600.00", "method": "pix"},
        )
        assert resposta.status_code == 201, resposta.text

        assert resposta.json()["status"] == "parcial"
        posicao = resposta.json()["position"]
        assert Decimal(posicao["paid_amount"]) == Decimal("600.00")
        assert Decimal(posicao["balance"]) > Decimal("0")

    def test_dois_recebimentos_quitam_a_mesma_cobranca(self, client_as, carteira):
        client: TestClient = client_as(carteira["user"].id)
        charge_id = client.post("/api/v1/charges/generate", json={}).json()["charge_ids"][0]

        client.post(
            f"/api/v1/charges/{charge_id}/entries",
            json={"date": date.today().isoformat(), "amount": "600.00"},
        )
        # `/settle` lança exatamente o saldo, sem a tela ter que recalcular
        # multa e juros do dia — cálculo que, feito no cliente, diverge do
        # servidor no primeiro arredondamento.
        final = client.post(f"/api/v1/charges/{charge_id}/settle")
        assert final.status_code == 200, final.text
        assert final.json()["status"] == "quitada"
        assert Decimal(final.json()["position"]["balance"]) == Decimal("0.00")
        assert len(final.json()["entries"]) == 2

    def test_extrato_do_inquilino_mostra_saldo_e_historico(self, client_as, carteira):
        client: TestClient = client_as(carteira["user"].id)
        charge_id = client.post("/api/v1/charges/generate", json={}).json()["charge_ids"][0]
        client.post(
            f"/api/v1/charges/{charge_id}/entries",
            json={"date": date.today().isoformat(), "amount": "600.00"},
        )

        tenant_id = carteira["tenant"].id
        extrato = client.get(f"/api/v1/tenants/{tenant_id}/ledger")
        assert extrato.status_code == 200, extrato.text
        dados = extrato.json()
        assert Decimal(dados["open_balance"]) > Decimal("0")
        assert dados["open_charges"] == 1
        assert len(dados["entries"]) == 1

    def test_inquilino_traz_situacao_financeira_na_listagem(self, client_as, carteira):
        """
        O card do inquilino precisava responder "está pagando?" sem que o
        operador abrisse a página de pagamentos e somasse de cabeça.
        """
        client: TestClient = client_as(carteira["user"].id)
        client.post("/api/v1/charges/generate", json={})

        inquilinos = client.get("/api/v1/tenants/").json()
        assert len(inquilinos) == 1
        assert "situacao_financeira" in inquilinos[0]
        assert "saldo_devedor" in inquilinos[0]

    def test_aging_soma_saldo_e_nao_valor_de_face(self, client_as, carteira, db_session):
        """Quem pagou 600 de 1.000 entra no relatório por 400, não por 1.000."""
        client: TestClient = client_as(carteira["user"].id)
        vencida = _cobranca_vencida(carteira, dias=45, status="vencida")
        db_session.add(vencida)
        db_session.flush()

        client.post(
            f"/api/v1/charges/{vencida.id}/entries",
            json={"date": date.today().isoformat(), "amount": "600.00"},
        )

        relatorio = client.get("/api/v1/charges/aging").json()
        faixa = next(b for b in relatorio["buckets"] if b["bucket"] == "d31_60")
        assert Decimal(faixa["amount"]) == Decimal("400.00")
        assert faixa["count"] == 1

    def test_dashboard_mostra_o_saldo_devedor_e_nao_o_valor_pago(self, client_as, carteira):
        """
        O painel lia `Payment.total_amount` como "valor devido", mas em registro
        parcial essa coluna guardava o valor PAGO — exibia 600 no lugar de 400.
        """
        client: TestClient = client_as(carteira["user"].id)
        charge_id = client.post("/api/v1/charges/generate", json={}).json()["charge_ids"][0]
        client.post(
            f"/api/v1/charges/{charge_id}/entries",
            json={"date": date.today().isoformat(), "amount": "600.00"},
        )

        posicao = client.get(f"/api/v1/charges/{charge_id}").json()["position"]
        saldo = Decimal(posicao["balance"])

        resumo = client.get("/api/v1/dashboard/summary").json()
        linhas = resumo["inadimplencia"]["atrasados"] + resumo["inadimplencia"]["parciais"]
        assert len(linhas) == 1
        # O painel exibe o SALDO (400 mais multa e juros do dia), nunca os 600
        # recebidos — que era o número que ele mostrava antes.
        assert linhas[0]["amount"] == pytest.approx(float(saldo))
        assert linhas[0]["amount"] != pytest.approx(600.0)
        assert saldo >= Decimal("400.00")
        # Receita é o dinheiro que entrou, não o valor de face da cobrança.
        assert resumo["financeiro"]["receitas_pagas"] == pytest.approx(600.0)


class TestCompatibilidadeDeRotasAntigas:
    """As rotas de /payments continuam respondendo — agora sobre `charges`."""

    def test_register_parcial_grava_o_saldo(self, client_as, carteira):
        """Antes o restante era calculado e descartado."""
        client: TestClient = client_as(carteira["user"].id)
        resposta = client.post(
            "/api/v1/payments/register",
            json={
                "contract_id": carteira["contrato"].id,
                "due_date": date.today().isoformat(),
                "payment_date": date.today().isoformat(),
                "paid_amount": 600,
                "payment_method": "pix",
            },
        )
        assert resposta.status_code == 201, resposta.text
        dados = resposta.json()
        assert dados["status"] == "parcial"
        assert Decimal(dados["paid_amount"]) == Decimal("600.00")
        assert Decimal(dados["balance_amount"]) == Decimal("400.00")

    def test_overdue_list_nao_fica_vazia_apos_o_job_diario(self, client_as, carteira, db_session):
        """
        O endpoint filtrava por `status IN (pendente, parcial)` com vencimento
        passado, mas o job das 06:00 já havia reescrito essas linhas para
        `atrasado` — a lista voltava vazia todo dia a partir das seis.
        """
        from src.scheduler import run_background_checks

        client: TestClient = client_as(carteira["user"].id)
        db_session.add(_cobranca_vencida(carteira, dias=40))
        db_session.flush()

        run_background_checks(db_session, carteira["user"].id)

        vencidos = client.get("/api/v1/payments/overdue/list")
        assert vencidos.status_code == 200
        assert len(vencidos.json()) >= 1, "a lista de vencidos voltou vazia"

    def test_job_diario_preserva_o_status_parcial(self, client_as, carteira, db_session):
        """O UPDATE em massa antigo trocava `parcial` por `atrasado`."""
        from src.scheduler import run_background_checks

        client: TestClient = client_as(carteira["user"].id)
        cobranca = _cobranca_vencida(carteira, dias=40)
        db_session.add(cobranca)
        db_session.flush()
        client.post(
            f"/api/v1/charges/{cobranca.id}/entries",
            json={"date": date.today().isoformat(), "amount": "600.00"},
        )

        run_background_checks(db_session, carteira["user"].id)
        db_session.refresh(cobranca)
        assert cobranca.status == "parcial"


class TestNotificacoesPorEvento:
    """
    Notificação é fila de trabalho, não mural.

    A versão anterior emitia um alerta por cobrança atrasada a cada 7 dias:
    numa carteira com 60 inadimplentes, 60 cartões se repetindo até o fim da
    dívida.
    """

    def test_atraso_notifica_uma_vez_por_limiar(self, client_as, carteira, db_session):
        from src.scheduler import run_background_checks

        client: TestClient = client_as(carteira["user"].id)
        cobranca = _cobranca_vencida(carteira, dias=20)
        db_session.add(cobranca)
        db_session.flush()

        def alertas_da_cobranca():
            return [
                n
                for n in client.get("/api/v1/notifications/").json()["items"]
                if n["type"] == "payment_overdue" and n["related_id"] == str(cobranca.id)
            ]

        primeira = run_background_checks(db_session, carteira["user"].id)
        assert primeira["notifications_created"] >= 1
        assert len(alertas_da_cobranca()) == 1

        # Rodar de novo não pode repetir o aviso do mesmo limiar — o defeito
        # que fazia o sino encher de cartões idênticos até a dívida acabar.
        segunda = run_background_checks(db_session, carteira["user"].id)
        assert len(alertas_da_cobranca()) == 1, "alerta repetido para a mesma cobrança"
        assert segunda["notifications_created"] == 0

    def test_inquilino_inadimplente_gera_alerta_proprio(self, client_as, carteira, db_session):
        """O alerta de carteira é por INQUILINO, não por cobrança."""
        from src.scheduler import run_background_checks

        client: TestClient = client_as(carteira["user"].id)
        db_session.add(_cobranca_vencida(carteira, dias=70))
        db_session.flush()

        run_background_checks(db_session, carteira["user"].id)

        alertas = [
            n
            for n in client.get("/api/v1/notifications/").json()["items"]
            if n["type"] == "tenant_delinquent"
        ]
        assert len(alertas) == 1
        assert alertas[0]["priority"] == "urgent"
