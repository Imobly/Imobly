"""
Varre a planilha de controle de aluguéis (CSV exportado do Excel, separador ';',
codificação cp1252) e produz um JSON normalizado com imóveis, inquilinos e
contratos prontos para importação via API.

A planilha é um histórico de PAGAMENTOS, não um cadastro: cada linha é um
recebimento. Os cadastros são derivados por agregação:

  imóvel    <- (Endereço, Apartamento/Kits)  -> uma unidade = um imóvel
  inquilino <- Inquilino
  contrato  <- (Inquilino, unidade), com datas e aluguel inferidos dos pagamentos

Campos obrigatórios da API que a planilha não possui (CPF, e-mail, telefone,
profissão, CEP, área, quartos, banheiros) recebem PLACEHOLDERS explícitos --
veja PLACEHOLDER_* abaixo. Eles existem só para satisfazer a validação e
devem ser corrigidos depois no sistema.

Uso:
    python extrair_planilha_alugueis.py <planilha.csv> [-o saida.json]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

# -- Placeholders (dados ausentes na planilha) --
PLACEHOLDER_EMAIL_DOMINIO = "nao-informado.example.com"
PLACEHOLDER_TELEFONE = "(61) 00000-0000"
PLACEHOLDER_PROFISSAO = "Não informado"
PLACEHOLDER_CEP = "71800-000"  # faixa do Riacho Fundo; confirmar por unidade
PLACEHOLDER_CPF_PREFIXO = "PENDENTE-"

CIDADE = "Brasília"
ESTADO = "DF"

# Estimativas por tipo de unidade -- a planilha não traz metragem nem cômodos.
PERFIL_POR_TIPO = {
    "studio": {"area": 25, "bedrooms": 1, "bathrooms": 1},
    "apartment": {"area": 60, "bedrooms": 2, "bathrooms": 1},
    "house": {"area": 80, "bedrooms": 2, "bathrooms": 1},
}

MESES_VALIDOS = {"jan", "fev", "mar", "abr", "mai", "jun",
                 "jul", "ago", "set", "out", "nov", "dez"}

# -- Correções informadas pelo proprietário --
# O aluguel contratado nem sempre é o valor pago: há meses com pagamento
# parcial. Onde o valor correto foi informado, ele prevalece sobre a inferência
# a partir dos pagamentos. Chave: nome do inquilino na planilha (minúsculo,
# sem acento).
ALUGUEL_CORRIGIDO = {
    "ze fabio": 3000.0,
    "alessandro ferreira": 2000.0,
}

# Nomes completos, vindos da aba "classificação" (colunas Q-X). Substituem o
# nome abreviado da aba de pagamentos. Chave: como o inquilino aparece na
# aba de pagamentos (minúsculo, sem acento).
NOME_CORRIGIDO = {
    "bianca/michely": "Michely Câmara",
    "alessandro ferreira": "Alessandro Ferreira da Silva",
    "thiago jesus": "Thiago Jesus da Fonseca",
    "franciso jeihson": "Franciso Jeihson Alves Bezerra",
    "lucas gabriel": "Lucas Gabriel Oliveira de Souza",
    "allan": "Allan Claudio dos Santos",
    "samia vanessa": "Samia Vanessa da Silva Mourao",
    "ana celia": "Ana Célia Favacho da Costa",
    "rosangela": "Rosangela Oliveira",
}

# CPF e telefone, também da aba "classificação". Dois inquilinos (Zé Fábio e
# Benia) não têm correspondência clara nessa aba — ver aviso no README do
# script. `cpf` None mantém o placeholder PENDENTE-xx.
#
# Duas ressalvas sobre os dados de origem:
#   - "franciso jeihson" e "samia vanessa" tinham CPF com 10 dígitos na
#     planilha (5707179143 / 5823977310) — provável zero à esquerda perdido
#     na formatação numérica do Excel. Restaurado como suposição; CONFERIR.
#   - "lucas gabriel" tinha CPF com a letra 'o' no lugar de '0'
#     (o6014806199) — corrigido.
DADOS_PESSOAIS = {
    "alessandro ferreira": {"cpf": "97755974120", "telefone": "61996119643"},
    "allan": {"cpf": "44278535104", "telefone": "61992027355"},
    "ana celia": {"cpf": "00537788123", "telefone": "61982564901"},
    "rosangela": {"cpf": None, "telefone": "61981898588"},
    "franciso jeihson": {"cpf": "05707179143", "telefone": "61992436690"},  # zero à esquerda restaurado
    "lucas gabriel": {"cpf": "06014806199", "telefone": "61985122361"},
    "samia vanessa": {"cpf": "05823977310", "telefone": "98970284097"},  # zero à esquerda restaurado
    "bianca/michely": {"cpf": "61189072343", "telefone": "61982096156"},
    "thiago jesus": {"cpf": "03270535180", "telefone": "61983544220"},
}


def formatar_cpf(cpf: str) -> str:
    """'97755974120' -> '977.559.741-20'. Sem os 11 dígitos, devolve como veio."""
    if len(cpf) != 11 or not cpf.isdigit():
        return cpf
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def formatar_telefone(tel: str) -> str:
    """'61996119643' -> '(61) 99611-9643'; 10 dígitos -> '(61) 9611-9643'."""
    if not tel.isdigit() or len(tel) not in (10, 11):
        return tel
    ddd, resto = tel[:2], tel[2:]
    meio = len(resto) - 4
    return f"({ddd}) {resto[:meio]}-{resto[meio:]}"


# Forma de pagamento da planilha -> enum aceito pela API.
FORMA_PAGAMENTO = {"pix": "pix", "boleto": "boleto", "dinheiro": "dinheiro",
                   "transferencia": "transferencia"}

DIAS_NO_MES = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def sem_acento(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def slug(texto: str) -> str:
    base = sem_acento(texto).lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return base or "sem-nome"


def titulo(texto: str) -> str:
    """Normaliza capitalização: 'lucas gabriel' -> 'Lucas Gabriel'."""
    minusculas = {"de", "da", "do", "das", "dos", "e"}
    partes = []
    for i, palavra in enumerate(re.split(r"(\s+|/)", texto.strip())):
        if not palavra.strip() or palavra == "/":
            partes.append(palavra)
            continue
        p = palavra.lower()
        partes.append(p if (i > 0 and p in minusculas) else p.capitalize())
    return "".join(partes)


def ler_valor(bruto: str) -> float | None:
    """' R$ 1.400,00 ' -> 1400.0"""
    limpo = bruto.replace("R$", "").replace(".", "").replace(",", ".").strip()
    limpo = re.sub(r"[^0-9.\-]", "", limpo)
    try:
        return float(limpo)
    except ValueError:
        return None


def ler_data(bruto: str) -> date | None:
    try:
        d, m, a = (int(x) for x in bruto.strip().split("/"))
        return date(a, m, d)
    except (ValueError, TypeError):
        return None


def inferir_tipo(unidade: str) -> str:
    u = sem_acento(unidade).lower()
    if u.startswith("kit"):
        return "studio"
    if u.startswith("apt") or u.startswith("ap "):
        return "apartment"
    return "house"  # 'Casa 23', 'Terreo'


def moda(valores: list):
    """Valor mais frequente; empate resolvido pelo último da lista (mais recente)."""
    contagem = Counter(valores)
    maior = max(contagem.values())
    candidatos = [v for v in valores if contagem[v] == maior]
    return candidatos[-1]


def somar_meses(d: date, meses: int) -> date:
    mes = d.month - 1 + meses
    ano = d.year + mes // 12
    mes = mes % 12 + 1
    ultimo = DIAS_NO_MES[mes - 1]
    if mes == 2 and ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0):
        ultimo = 29
    return date(ano, mes, min(d.day, ultimo))


def ler_pagamentos(caminho: Path) -> list[dict]:
    """Extrai apenas as linhas de recebimento (colunas 0..8) da planilha."""
    pagamentos = []
    with caminho.open(encoding="cp1252", newline="") as fh:
        for linha in csv.reader(fh, delimiter=";"):
            if len(linha) < 9:
                continue
            mes, data, cidade, endereco, forma, unidade, inquilino, valor, destinatario = (
                c.strip() for c in linha[:9]
            )
            if sem_acento(mes).lower() not in MESES_VALIDOS:
                continue  # cabeçalho, linhas vazias e o bloco de repasses à direita
            dt, vl = ler_data(data), ler_valor(valor)
            if not (dt and vl and endereco and unidade and inquilino):
                continue
            pagamentos.append({
                "data": dt,
                "cidade": cidade,
                "endereco": endereco,
                "forma": forma,
                "unidade": unidade,
                "inquilino": inquilino,
                "valor": vl,
                "destinatario": destinatario,
            })
    return pagamentos


def montar_cadastros(pagamentos: list[dict]) -> dict:
    # Um contrato por par (inquilino, unidade); a chave da unidade é (endereço, unidade).
    por_locacao: dict[tuple, list[dict]] = defaultdict(list)
    for p in pagamentos:
        por_locacao[(p["endereco"], p["unidade"], sem_acento(p["inquilino"]).lower())].append(p)

    imoveis: dict[tuple, dict] = {}
    inquilinos: dict[str, dict] = {}
    contratos: list[dict] = []
    pagamentos_saida: list[dict] = []

    for (endereco, unidade, chave_inq), pags in sorted(por_locacao.items()):
        pags.sort(key=lambda p: p["data"])
        tipo = inferir_tipo(unidade)
        perfil = PERFIL_POR_TIPO[tipo]
        # Valor informado pelo proprietário > moda dos pagamentos.
        aluguel = ALUGUEL_CORRIGIDO.get(chave_inq) or moda([p["valor"] for p in pags])
        nome_inquilino = NOME_CORRIGIDO.get(chave_inq) or titulo(pags[-1]["inquilino"])

        # -- imóvel --
        chave_imovel = (endereco, unidade)
        if chave_imovel not in imoveis:
            imoveis[chave_imovel] = {
                "ref": f"{slug(endereco)}--{slug(unidade)}",
                "name": f"{endereco} - {unidade}",
                "address": f"{endereco}, {unidade}",
                "neighborhood": titulo(pags[0]["cidade"]),  # 'Riacho Fundo' é região adm.
                "city": CIDADE,
                "state": ESTADO,
                "zip_code": PLACEHOLDER_CEP,
                "type": tipo,
                "area": perfil["area"],
                "bedrooms": perfil["bedrooms"],
                "bathrooms": perfil["bathrooms"],
                "parking_spaces": 0,
                "rent": aluguel,
                "status": "inactive",
                "description": (
                    "Importado da planilha de controle de aluguéis 2026. "
                    "Área, quartos, banheiros e CEP são estimativas -- revisar."
                ),
            }

        # -- inquilino --
        if chave_inq not in inquilinos:
            indice = len(inquilinos) + 1
            pessoais = DADOS_PESSOAIS.get(chave_inq, {})
            cpf_real = pessoais.get("cpf")
            telefone_real = pessoais.get("telefone")
            placeholders = ["email", "profession"]
            if not cpf_real:
                placeholders.append("cpf_cnpj")
            if not telefone_real:
                placeholders.append("phone")
            nome_curto = titulo(pags[-1]["inquilino"])
            inquilinos[chave_inq] = {
                "ref": slug(nome_inquilino),
                "name": nome_inquilino,
                "email": f"{slug(nome_inquilino)}@{PLACEHOLDER_EMAIL_DOMINIO}",
                "phone": formatar_telefone(telefone_real) if telefone_real else PLACEHOLDER_TELEFONE,
                "cpf_cnpj": formatar_cpf(cpf_real) if cpf_real else f"{PLACEHOLDER_CPF_PREFIXO}{indice:02d}",
                "profession": PLACEHOLDER_PROFISSAO,
                "_placeholders": placeholders,
                # Nome com que este inquilino foi cadastrado antes de a aba de
                # classificação trazer o nome completo. O importador usa isto
                # para reconhecer o registro já criado (CPF/e-mail mudaram de
                # placeholder para o valor real, e não servem mais de chave).
                "_nome_anterior": nome_curto if nome_curto != nome_inquilino else None,
            }

        # -- contrato --
        inicio = pags[0]["data"]
        fim = somar_meses(inicio, 12)
        while fim <= pags[-1]["data"]:
            fim = somar_meses(fim, 12)
        dia_vencimento = moda([p["data"].day for p in pags])
        titulo_contrato = f"{nome_inquilino} - {unidade}"

        # -- cobranças (histórico da planilha, modelo charges + entries) --
        # Uma cobrança por mês de competência (rent_amount = aluguel do
        # contrato), com um "entry" por recebimento daquele mês -- na
        # planilha normalmente um só, mas Alessandro e Zé Fábio têm dois
        # recebimentos no mesmo mês.
        por_competencia: dict[date, list[dict]] = defaultdict(list)
        for p in pags:
            por_competencia[date(p["data"].year, p["data"].month, 1)].append(p)

        for competencia, pags_do_mes in sorted(por_competencia.items()):
            ultimo_dia = DIAS_NO_MES[competencia.month - 1]
            if competencia.month == 2 and competencia.year % 4 == 0:
                ultimo_dia = 29
            vencimento = date(competencia.year, competencia.month, min(dia_vencimento, ultimo_dia))
            pagamentos_saida.append({
                "contract_ref": titulo_contrato,
                "competencia": competencia.isoformat(),
                "due_date": vencimento.isoformat(),
                "rent_amount": aluguel,
                "charges_amount": 0,
                "discount_amount": 0,
                "description": "Importado da planilha de controle de aluguéis 2026.",
                "entries": [
                    {
                        "date": p["data"].isoformat(),
                        "amount": p["valor"],
                        "method": FORMA_PAGAMENTO.get(p["forma"].strip().lower(), "outro"),
                        "description": (
                            f"Recebido em {p['data'].strftime('%d/%m/%Y')} por "
                            f"{p['destinatario'] or 'não informado'} (planilha 2026)"
                        ),
                    }
                    for p in pags_do_mes
                ],
            })

        contratos.append({
            "title": titulo_contrato,
            "property_ref": imoveis[chave_imovel]["ref"],
            "tenant_ref": inquilinos[chave_inq]["ref"],
            "start_date": inicio.isoformat(),
            "end_date": fim.isoformat(),
            "rent": aluguel,
            "deposit": 0,
            "interest_rate": 0,
            "fine_rate": 0,
            "due_day": dia_vencimento,
            "status": "inativo",
            "_pagamentos": len(pags),
            "_valores_observados": sorted({p["valor"] for p in pags}),
            "_primeiro_pagamento": inicio.isoformat(),
            "_ultimo_pagamento": pags[-1]["data"].isoformat(),
        })

    return {
        "properties": list(imoveis.values()),
        "tenants": list(inquilinos.values()),
        "contracts": contratos,
        "charges": pagamentos_saida,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Extrai cadastros da planilha de aluguéis.")
    ap.add_argument("planilha", type=Path)
    ap.add_argument("-o", "--saida", type=Path, default=Path("cadastros.json"))
    args = ap.parse_args()

    pagamentos = ler_pagamentos(args.planilha)
    dados = montar_cadastros(pagamentos)
    args.saida.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"pagamentos lidos: {len(pagamentos)}")
    print(f"imoveis:    {len(dados['properties'])}")
    print(f"inquilinos: {len(dados['tenants'])}")
    print(f"contratos:  {len(dados['contracts'])}")
    print(f"cobranças:  {len(dados['charges'])}")
    print(f"-> {args.saida}")


if __name__ == "__main__":
    main()
