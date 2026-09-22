"""
Transições de ocupação de um imóvel.

Ocupação é um estado que vive em TRÊS tabelas ao mesmo tempo:
`properties.status` + `properties.tenant_id`, `contracts.status` e
`tenants.contract_id`. Antes cada uma era alterada pela tela que por acaso
estivesse aberta, e as três divergiam: imóvel marcado como vago continuava
apontando para o inquilino, que continuava exibindo como vigente um contrato
de um imóvel que ele já tinha deixado.

Aqui as três andam juntas, no servidor, para valer qualquer que seja o cliente
que dispare a mudança.
"""

from typing import Optional

from sqlalchemy.orm import Session

from src.contracts.models import Contract
from src.tenants.models import Tenant

from .models import Property

OCUPADO = "occupied"
VAGO = "vacant"


def encerrar_contratos_ativos(db: Session, property_id: int, user_id: int) -> int:
    """
    Inativa os contratos ativos do imóvel e desfaz o vínculo do inquilino.

    Não apaga nada: o contrato encerrado continua sendo a prova do que foi
    cobrado enquanto vigia, e as cobranças já emitidas seguem apontando para
    ele. O que muda é só o status — é ele que o restante do sistema lê para
    decidir se ainda gera aluguel no mês seguinte.

    Devolve quantos contratos foram encerrados.
    """
    contratos = (
        db.query(Contract)
        .filter(
            Contract.property_id == property_id,
            Contract.user_id == user_id,
            Contract.status == "ativo",
        )
        .all()
    )

    for contrato in contratos:
        contrato.status = "inativo"

        # `tenants.contract_id` é o contrato VIGENTE do inquilino. Deixá-lo
        # apontando para um contrato inativo faz a ficha do inquilino mostrar
        # aluguel e vencimento de uma locação que acabou.
        inquilino = (
            db.query(Tenant)
            .filter(Tenant.id == contrato.tenant_id, Tenant.user_id == user_id)
            .first()
        )
        if inquilino is not None and inquilino.contract_id == contrato.id:
            inquilino.contract_id = None

    return len(contratos)


def aplicar_transicao(
    db: Session,
    imovel: Property,
    user_id: int,
    novo_status: Optional[str],
    novo_tenant_id: Optional[int],
    tenant_id_informado: bool,
) -> Optional[int]:
    """
    Valida e executa a mudança de ocupação, SEM commit.

    `tenant_id_informado` distingue "o cliente mandou tenant_id: null" de "o
    cliente não tocou no campo" — num PATCH parcial os dois chegam como `None`,
    e tratá-los igual desvincularia o inquilino a cada edição de descrição.

    Devolve o número de contratos encerrados, ou `None` quando a ocupação não
    mudou.
    """
    if novo_status is None or novo_status == imovel.status:
        return None

    status_anterior = imovel.status

    if novo_status == OCUPADO:
        # Só exigido na TRANSIÇÃO para ocupado. Exigir em toda edição travaria
        # imóveis importados de planilha, que já estão ocupados sem `tenant_id`.
        tenant_final = novo_tenant_id if tenant_id_informado else imovel.tenant_id
        if tenant_final is None:
            raise ValueError(
                "Para marcar o imóvel como ocupado, selecione o inquilino que vai ocupá-lo."
            )
        return None

    if novo_status == VAGO and status_anterior == OCUPADO:
        imovel.tenant_id = None
        return encerrar_contratos_ativos(db, imovel.id, user_id)

    return None
