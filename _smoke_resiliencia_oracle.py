"""Confirma que o sistema NAO derruba a ficha inteira quando UMA sub-query
do Oracle falha por nome de coluna invalida (ORA-00904)."""
fake_medico = [
    (1, "ALINE FONSECA LIMA", None, None, 2018, "FACULDADE DE MEDICINA DE BARBACENA")
]


def fake_executar(sql, params):
    if "credi01300_new" in sql:
        return [dict(zip(
            ["ID_MEDICO", "NOME", "NOME_SOCIAL", "CPF", "ANO_CONCLUSAO", "INSTITUICAO_GRADUACAO"],
            r)) for r in fake_medico]
    if "credi01301" in sql:
        return [{"ID_MEDICO": 1, "ID_CRM": 9001, "CRM": "654321", "UF": "MG", "SITUACAO": "ATIVO"}]
    if "credi01303" in sql:
        # SIMULA o erro "INSTITUICAO": invalid identifier do log do usuario
        raise RuntimeError("ORA-00904: \"INSTITUICAO\": invalid identifier")
    if "tmp_endereco" in sql:
        return [{"ID_MEDICO": 1, "NU_ADDR": 11, "CO_TYPE_ADDR": "1", "DS_NAME_LOGR": "RUA X",
                 "CO_NUMB_LOGR": "100", "DS_CITY": "BARBACENA", "CO_STTE": "MG", "CO_ZIPC": "36200000",
                 "DS_DIST": "Centro"}]
    return []


import app.db.queries as q
q.executar = fake_executar
from app.repositorio import detalhe_medico
r = detalhe_medico(1)
assert r["nome"] == "ALINE FONSECA LIMA", "ficha deveria abrir (medico OK)"
assert r["crms"], "crms deveriam vir"
assert r["residencias"] == [], "residencias vazias (sub-query falhou, mas nao derruba)"
assert r["_diagnostico_oracle"], "diagnostico deveria sinalizar o erro"
assert any("residencias" in d.get("secao", "") for d in r["_diagnostico_oracle"])
print("OK:", r["_diagnostico_oracle"])
print("Resiliencia: ficha ABERTA mesmo com 1 sub-query quebrada.")
