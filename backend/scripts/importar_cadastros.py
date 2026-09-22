"""
Sincroniza na plataforma o JSON gerado por `extrair_planilha_alugueis.py`.

Ordem obrigatória: imóveis e inquilinos primeiro (a API devolve os ids), depois
contratos e pagamentos, que referenciam ambos. O JSON usa refs textuais
(`property_ref` / `tenant_ref` / `contract_ref`) porque os ids só existem após
o POST.

É idempotente e corretivo: o que não existe é criado, o que existe e divergiu
é atualizado via PUT. Rodar de novo depois de corrigir a planilha propaga a
correção em vez de duplicar. As chaves de identidade são:

  imóvel     `name`
  inquilino  `cpf_cnpj` (estável entre execuções) ou `email`
  contrato   (property_id, tenant_id, start_date) -- não o título, que muda
             quando o nome do inquilino é corrigido
  pagamento  (contract_id, payment_date, amount)

Uso:
    python importar_cadastros.py cadastros.json --dry-run
    python importar_cadastros.py cadastros.json --email ... --senha ...

Credenciais também podem vir de IMOBLY_EMAIL / IMOBLY_SENHA.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_PADRAO = "http://localhost:8000/api/v1"

# Refs textuais e campos de diagnóstico não são enviados à API.
CHAVES_INTERNAS = ("ref", "property_ref", "tenant_ref", "contract_ref")


class ErroApi(RuntimeError):
    pass


def requisitar(metodo: str, url: str, token: str | None = None, corpo: dict | None = None):
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request(url, data=dados, method=metodo)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            texto = resp.read().decode("utf-8")
            return json.loads(texto) if texto else None
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode("utf-8", "replace")
        raise ErroApi(f"{metodo} {url} -> HTTP {e.code}: {detalhe}") from e
    except urllib.error.URLError as e:
        raise ErroApi(f"{metodo} {url} -> falha de conexão: {e.reason}") from e


def limpar(registro: dict) -> dict:
    """Remove refs e campos de diagnóstico ('_...') antes do POST/PUT."""
    return {
        k: v for k, v in registro.items()
        if not k.startswith("_") and k not in CHAVES_INTERNAS
    }


def divergencias(desejado: dict, atual: dict) -> dict:
    """Campos cujo valor no servidor difere do desejado.

    Compara como texto normalizado: a API devolve Decimal serializado
    ('600.00') onde o JSON traz float (600.0), e a comparação crua acusaria
    diferença em todo registro.
    """

    def norma(v):
        if isinstance(v, (int, float)):
            return f"{float(v):.2f}"
        if isinstance(v, str):
            try:
                return f"{float(v):.2f}"
            except ValueError:
                return v.strip()
        return v

    return {
        k: v for k, v in desejado.items()
        if k in atual and norma(v) != norma(atual[k])
    }


def autenticar(api: str, email: str, senha: str) -> str:
    resposta = requisitar("POST", f"{api}/auth/login", corpo={"username": email, "password": senha})
    token = (resposta or {}).get("access_token")
    if not token:
        raise ErroApi("login não retornou access_token")
    return token


def sincronizar(
    api: str, token: str, recurso: str, rotulo: str,
    desejados: list[dict], achar, dry_run: bool,
) -> dict[str, int]:
    """Cria ou atualiza uma lista de registros. Devolve {ref: id}."""
    atuais = requisitar("GET", f"{api}/{recurso}/", token)
    ids: dict[str, int] = {}

    for desejado in desejados:
        ref = desejado.get("ref") or desejado.get("title") or desejado.get("name")
        corpo = limpar(desejado)
        existente = achar(desejado, corpo, atuais)

        if existente is None:
            if dry_run:
                print(f"  [dry-run] + {rotulo}: {ref}")
                ids[ref] = 0
                continue
            criado = requisitar("POST", f"{api}/{recurso}/", token, corpo)
            ids[ref] = criado["id"]
            print(f"  + {rotulo}: {ref} (id {criado['id']})")
            continue

        ids[ref] = existente["id"]
        mudou = divergencias(corpo, existente)
        if not mudou:
            print(f"  = {rotulo}: {ref} (id {existente['id']})")
            continue
        resumo = ", ".join(f"{k}: {existente[k]} -> {v}" for k, v in mudou.items())
        if dry_run:
            print(f"  [dry-run] ~ {rotulo}: {ref} ({resumo})")
            continue
        requisitar("PUT", f"{api}/{recurso}/{existente['id']}", token, mudou)
        print(f"  ~ {rotulo}: {ref} ({resumo})")

    return ids


def importar(api: str, token: str, dados: dict, dry_run: bool) -> None:
    # -- imóveis --
    id_imovel = sincronizar(
        api, token, "properties", "imóvel", dados["properties"],
        lambda desejado, c, atuais: next((p for p in atuais if p["name"] == c["name"]), None),
        dry_run,
    )

    # -- inquilinos --
    id_inquilino = sincronizar(
        api, token, "tenants", "inquilino", dados["tenants"],
        lambda desejado, c, atuais: next(
            (t for t in atuais
             if t["cpf_cnpj"] == c["cpf_cnpj"]
             or t["email"] == c["email"]
             # Registro criado antes de a aba de classificação trazer o nome
             # completo: CPF/e-mail eram placeholder, a única pista que
             # sobrevive é o nome curto com que o inquilino foi cadastrado.
             or (desejado.get("_nome_anterior") and t["name"] == desejado["_nome_anterior"])),
            None,
        ),
        dry_run,
    )

    # -- contratos --
    contratos = []
    for contrato in dados["contracts"]:
        corpo = dict(contrato)
        corpo["property_id"] = id_imovel[contrato["property_ref"]]
        corpo["tenant_id"] = id_inquilino[contrato["tenant_ref"]]
        contratos.append(corpo)

    id_contrato = sincronizar(
        api, token, "contracts", "contrato", contratos,
        lambda desejado, c, atuais: next(
            (k for k in atuais
             if k["property_id"] == c["property_id"]
             and k["tenant_id"] == c["tenant_id"]
             and k["start_date"] == c["start_date"]),
            None,
        ),
        dry_run,
    )
    # A sincronização indexa contratos pelo título; os pagamentos referenciam
    # o mesmo título via `contract_ref`.

    # -- cobranças + recebimentos (modelo charges/entries) --
    if not dados.get("charges"):
        return
    atuais = requisitar("GET", f"{api}/charges/?limit=500", token)
    for cobranca in dados["charges"]:
        contract_id = id_contrato[cobranca["contract_ref"]]
        rotulo = f"{cobranca['contract_ref']} {cobranca['competencia'][:7]}"

        existente = next(
            (c for c in atuais
             if c["contract_id"] == contract_id
             and c["competencia"][:7] == cobranca["competencia"][:7]),
            None,
        )

        if existente is None:
            corpo = {
                "contract_id": contract_id,
                "competencia": cobranca["competencia"],
                "due_date": cobranca["due_date"],
                "rent_amount": cobranca["rent_amount"],
                "charges_amount": cobranca["charges_amount"],
                "discount_amount": cobranca["discount_amount"],
                "description": cobranca["description"],
            }
            if dry_run:
                print(f"  [dry-run] + cobrança: {rotulo} (aluguel {corpo['rent_amount']})")
                entradas_existentes = []
            else:
                criada = requisitar("POST", f"{api}/charges/", token, corpo)
                charge_id = criada["id"]
                entradas_existentes = []
                print(f"  + cobrança: {rotulo} (id {charge_id}, aluguel {corpo['rent_amount']})")
        else:
            charge_id = existente["id"]
            entradas_existentes = requisitar("GET", f"{api}/charges/{charge_id}/entries", token) or []
            print(f"  = cobrança: {rotulo} (id {charge_id})")

        # -- recebimentos da cobrança --
        for entrada in cobranca["entries"]:
            rotulo_entrada = f"{rotulo} | {entrada['date']} R$ {entrada['amount']}"
            ja_existe = any(
                e["date"] == entrada["date"] and float(e["amount"]) == float(entrada["amount"])
                for e in entradas_existentes
            )
            if ja_existe:
                print(f"    = recebimento: {rotulo_entrada}")
                continue
            if dry_run:
                print(f"    [dry-run] + recebimento: {rotulo_entrada}")
                continue
            requisitar("POST", f"{api}/charges/{charge_id}/entries", token, entrada)
            print(f"    + recebimento: {rotulo_entrada}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Sincroniza cadastros na plataforma Imobly.")
    ap.add_argument("json", type=Path)
    ap.add_argument("--api", default=os.environ.get("IMOBLY_API", API_PADRAO))
    ap.add_argument("--email", default=os.environ.get("IMOBLY_EMAIL"))
    ap.add_argument("--senha", default=os.environ.get("IMOBLY_SENHA"))
    ap.add_argument("--dry-run", action="store_true", help="mostra o que faria, sem gravar")
    args = ap.parse_args()

    if not args.email or not args.senha:
        ap.error("informe --email/--senha (ou IMOBLY_EMAIL/IMOBLY_SENHA)")

    dados = json.loads(args.json.read_text(encoding="utf-8"))
    print(f"API: {args.api}  |  usuário: {args.email}")
    try:
        token = autenticar(args.api, args.email, args.senha)
        importar(args.api, token, dados, args.dry_run)
    except ErroApi as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 1
    print("concluído.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
