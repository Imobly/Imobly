"""
Serviço para cálculo automático de valores de pagamento
com multas, juros e gerenciamento de status
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.src.contracts.models import Contract


class PaymentCalculationService:
    """Serviço para calcular valores de pagamento automaticamente"""

    @staticmethod
    def calculate_due_date(contract: Contract, month_offset: int = 0) -> date:
        """
        Calcula a data de vencimento baseada no dia do início do contrato

        Args:
            contract: Contrato do inquilino
            month_offset: Número de meses para adicionar (0 = mês atual)

        Returns:
            Data de vencimento calculada
        """
        start_day = contract.start_date.day

        # Calcular o mês alvo
        current_date = datetime.now().date()
        target_month = current_date.month + month_offset
        target_year = current_date.year

        # Ajustar ano se necessário
        while target_month > 12:
            target_month -= 12
            target_year += 1
        while target_month < 1:
            target_month += 12
            target_year -= 1

        # Ajustar dia se o mês não tiver o dia (ex: 31 em fevereiro)
        try:
            due_date = date(target_year, target_month, start_day)
        except ValueError:
            # Se o dia não existe no mês, usar o último dia do mês
            if target_month == 12:
                next_month = date(target_year + 1, 1, 1)
            else:
                next_month = date(target_year, target_month + 1, 1)
            due_date = next_month - timedelta(days=1)

        return due_date

    @staticmethod
    def calculate_days_overdue(due_date: date, payment_date: Optional[date] = None) -> int:
        """
        Calcula o número de dias em atraso

        Args:
            due_date: Data de vencimento
            payment_date: Data do pagamento (None = hoje)

        Returns:
            Número de dias em atraso (0 se não atrasado)
        """
        reference_date = payment_date if payment_date else datetime.now().date()

        if reference_date <= due_date:
            return 0

        return (reference_date - due_date).days

    @staticmethod
    def calculate_fine_and_interest(
        base_amount: Decimal, fine_rate: Decimal, interest_rate: Decimal, days_overdue: int
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Calcula multa e juros baseados nos dias de atraso

        Args:
            base_amount: Valor base do aluguel
            fine_rate: Taxa de multa (%) - aplicada uma vez
            interest_rate: Taxa de juros mensal (%) - proporcional aos dias
            days_overdue: Dias em atraso

        Returns:
            Tupla (multa, juros, total_acrescimo)
        """
        if days_overdue <= 0:
            return Decimal("0"), Decimal("0"), Decimal("0")

        # Multa (aplicada uma única vez)
        fine = (base_amount * fine_rate) / Decimal("100")

        # Juros (proporcional aos dias - juros mensal / 30 dias)
        daily_interest_rate = interest_rate / Decimal("30")
        interest = (base_amount * daily_interest_rate * Decimal(str(days_overdue))) / Decimal("100")

        # Total de acréscimo
        total_addition = fine + interest

        return fine, interest, total_addition

    @classmethod
    def calculate_payment_values(
        cls,
        contract: Contract,
        due_date: date,
        payment_date: Optional[date] = None,
        paid_amount: Optional[Decimal] = None,
    ) -> dict:
        """
        Calcula todos os valores de um pagamento automaticamente

        Args:
            contract: Contrato relacionado
            due_date: Data de vencimento
            payment_date: Data do pagamento (None = a pagar)
            paid_amount: Valor pago (None = ainda não pago)

        Returns:
            Dict com todos os valores calculados
        """
        base_amount = Decimal(str(contract.rent))
        days_overdue = cls.calculate_days_overdue(due_date, payment_date)

        # Calcular multa e juros
        fine, interest, total_addition = cls.calculate_fine_and_interest(
            base_amount,
            Decimal(str(contract.fine_rate)),
            Decimal(str(contract.interest_rate)),
            days_overdue,
        )

        # Valor total esperado
        total_expected = base_amount + total_addition

        # Determinar status
        status = cls.determine_payment_status(
            due_date, payment_date, paid_amount, Decimal(str(total_expected))
        )

        return {
            "base_amount": base_amount,
            "fine_amount": fine,
            "interest_amount": interest,
            "total_addition": total_addition,
            "total_expected": total_expected,
            "days_overdue": days_overdue,
            "status": status,
            "paid_amount": paid_amount if paid_amount else Decimal("0"),
            "remaining_amount": max(
                Decimal("0"),
                Decimal(str(total_expected)) - (paid_amount if paid_amount else Decimal("0")),
            ),
        }

    @staticmethod
    def determine_payment_status(
        due_date: date,
        payment_date: Optional[date],
        paid_amount: Optional[Decimal],
        total_expected: Decimal,
    ) -> str:
        """
        Determina o status do pagamento

        Args:
            due_date: Data de vencimento
            payment_date: Data do pagamento
            paid_amount: Valor pago
            total_expected: Valor total esperado

        Returns:
            Status: 'pending', 'paid', 'overdue', 'partial'
        """
        current_date = datetime.now().date()

        # Se não foi pago ainda
        if not paid_amount or paid_amount == Decimal("0"):
            if current_date > due_date:
                return "overdue"  # Atrasado
            else:
                return "pending"  # Pendente

        # Se foi pago
        if paid_amount >= total_expected:
            return "paid"  # Pago completamente
        else:
            return "partial"  # Pagamento parcial

    @staticmethod
    def get_contract_duration_months(contract: Contract) -> int:
        """
        Calcula a duração do contrato em meses

        Args:
            contract: Contrato

        Returns:
            Número de meses de duração
        """
        delta_years = contract.end_date.year - contract.start_date.year
        delta_months = contract.end_date.month - contract.start_date.month

        total_months = (delta_years * 12) + delta_months

        # Ajustar se o dia final for antes do dia inicial
        if contract.end_date.day < contract.start_date.day:
            total_months -= 1

        return int(max(0, total_months))

    @staticmethod
    def get_days_until_contract_end(contract: Contract) -> int:
        """
        Calcula quantos dias faltam para o contrato terminar

        Args:
            contract: Contrato

        Returns:
            Número de dias até o término (negativo se já venceu)
        """
        current_date = datetime.now().date()
        delta = contract.end_date - current_date
        return int(delta.days)

    @staticmethod
    def should_send_contract_expiring_notification(contract: Contract) -> Optional[str]:
        """
        Verifica se deve enviar notificação de vencimento de contrato

        Args:
            contract: Contrato a verificar

        Returns:
            Tipo de notificação: '60_days', '30_days', ou None
        """
        if contract.status != "active":
            return None

        days_until_end = PaymentCalculationService.get_days_until_contract_end(contract)

        # 60 dias (2 meses) de antecedência
        if 59 <= days_until_end <= 61:
            return "60_days"

        # 30 dias de antecedência
        if 29 <= days_until_end <= 31:
            return "30_days"

        return None

    @staticmethod
    def should_send_payment_reminder(due_date: date) -> Optional[str]:
        """
        Verifica se deve enviar lembrete de pagamento

        Args:
            due_date: Data de vencimento

        Returns:
            Tipo de lembrete: '2_days_before', 'due_today', ou None
        """
        current_date = datetime.now().date()
        days_until_due = (due_date - current_date).days

        # 2 dias antes do vencimento
        if days_until_due == 2:
            return "2_days_before"

        # Dia do vencimento
        if days_until_due == 0:
            return "due_today"

        return None

    @classmethod
    def update_payment_status_automatically(cls, db: Session, payment_id: int) -> str:
        """
        Atualiza automaticamente o status de um pagamento

        Args:
            db: Sessão do banco
            payment_id: ID do pagamento

        Returns:
            Novo status do pagamento
        """
        from app.src.payments.models import Payment

        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")

        # Converter Column para tipos Python
        due_date_val = payment.due_date if isinstance(payment.due_date, date) else payment.due_date
        payment_date_val = (
            payment.payment_date
            if payment.payment_date is None or isinstance(payment.payment_date, date)
            else payment.payment_date
        )
        amount_val = Decimal(str(payment.amount)) if payment.payment_date else None
        total_val = Decimal(str(payment.total_amount))

        new_status = cls.determine_payment_status(
            due_date_val,  # type: ignore[arg-type]
            payment_date_val,  # type: ignore[arg-type]
            amount_val,
            total_val,
        )

        if payment.status != new_status:
            setattr(payment, "status", new_status)
            db.commit()
            db.refresh(payment)

        return new_status
