"""Carteira de tokens — DÉBITO MOCKADO em memória.

Tabela de custo isolada (fácil de trocar por tabela real no futuro):
  GENERALISTA      700   (R$ 35)
  ESPECIALISTA     2000  (R$ 100)
  SUB_ESPECIALISTA 4000  (R$ 200)
  AVANCADO         +300  (R$ 15)

Saldo em memória + log de transações. NÃO é persistente — é mock para o MVP.
"""
import time
from threading import Lock

from app import config
from app.services import CUSTO_PERFIL, CUSTO_AVANCADO

_lock = Lock()
_SALDO = config.SALDO_INICIAL_TOKENS
_EXTRATO = []


def saldo():
    with _lock:
        return {"saldo_tokens": _SALDO,
                "saldo_reais": round(_SALDO * 0.05, 2),
                "custo_tabela": {**CUSTO_PERFIL, "AVANCADO": CUSTO_AVANCADO}}


def _registrar(tp, descricao, valor, ref):
    global _SALDO
    _SALDO -= valor
    tx = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "tipo": tp,
          "descricao": descricao, "tokens": -valor if valor else 0,
          "saldo_apos": _SALDO, "ref": ref}
    _EXTRATO.append(tx)
    return tx


def debitar(tp, descricao, valor, ref=None):
    """Debita tokens. Retorna (ok, tx_ou_erro)."""
    with _lock:
        if _SALDO < valor:
            return False, {"erro": "saldo_insuficiente",
                           "saldo_tokens": _SALDO, "necessario": valor}
        return True, _registrar(tp, descricao, valor, ref)


def estornar(descricao, valor, ref=None):
    with _lock:
        return _registrar("ESTORNO", descricao, -valor if valor else 0, ref)


def extrato():
    with _lock:
        return list(reversed(_EXTRATO))
