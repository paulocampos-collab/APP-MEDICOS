"""Deriva o perfil do médico a partir das especialidades (credi01302).

Regra (fechada com o cliente):
  SUB_ESPECIALISTA (4.000) quando houver ID_ESP_SUB/FLAG_SUB
  ESPECIALISTA     (2.000) quando houver RQE
  GENERALISTA      (700)   caso contrário

Atenção: aceita chaves em maiúsculas (colunas do Oracle — oracledb devolve
nomes em CAIXA ALTA) e minúsculas (fixtures do modo mock).
"""
from app.services import CUSTO_PERFIL


def _v(e, nome):
    """Lê o campo tolerando maiúsculas (Oracle) e minúsculas (mock)."""
    return e.get(nome) if nome in e else e.get(nome.lower())


def classificar(especialidades_por_crm):
    """especialidades_por_crm: {id_crm: [ {ESPECIALIDADE, RQE, FLAG_SUB, ID_ESP_SUB}, ... ]}"""
    ordem = 1
    perfil = "GENERALISTA"
    for _crm, lista in (especialidades_por_crm or {}).items():
        for e in lista or []:
            if _v(e, "ID_ESP_SUB") or _v(e, "FLAG_SUB"):
                if ordem < 3:
                    ordem, perfil = 3, "SUB_ESPECIALISTA"
            elif _v(e, "RQE"):
                if ordem < 2:
                    ordem, perfil = 2, "ESPECIALISTA"
    return {"perfil": perfil, "ordem": ordem, "custo_tokens": CUSTO_PERFIL[perfil]}
