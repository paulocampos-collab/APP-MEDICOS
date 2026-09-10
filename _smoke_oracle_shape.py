"""Smoke do SHAPE Oracle apos o fix de lowercase (correcao do 'undefined')."""
from app.db import queries

# Linhas fake devolvidas pelo oracledb thin: cur.description -> [d[0] for d in ...]
fake_cols_rows = {
    "SQL_MEDICO": (
        ["id_medico", "nome", "nome_social", "cpf", "ano_conclusao", "instituicao_graduacao"],
        [(142, "ALINE FONSECA LIMA", None, None, 2018, "FACULDADE DE MEDICINA DE BARBACENA")],
    ),
    "SQL_CRMS": (
        ["id_medico", "id_crm", "crm", "uf", "situacao", "dt_prim_inscricao_uf"],
        [
            (142, 9001, "654321", "MG", "ATIVO", "2019-01-10"),
            (142, 9002, "111222", "SP", "ATIVO", "2022-05-20"),
        ],
    ),
    "SQL_ESPECIALIDADES": (
        ["id_especialidade", "id_crm", "especialidade", "rqe", "flag_sub", "id_esp_sub"],
        [
            (8001, 9001, "CARDIOLOGIA", "99001", 0, None),
            (8002, 9001, "HEMODINAMICA", "99002", 1, 8001),
        ],
    ),
    "SQL_RESIDENCIAS": (
        ["id_residencia", "nm_programa", "nm_instituicao", "sg_uf", "dt_inicio", "dt_termino"],
        [(501, "CARDIOLOGIA", "HOSPITAL BARBACENA", "MG", "2019", "2022")],
    ),
    "SQL_ENDERECOS": (
        ["id_medico", "nu_addr", "co_type_addr", "co_type_logr", "ds_name_logr",
         "co_numb_logr", "ds_cmpl_logr", "ds_dist", "ds_city", "co_stte", "co_zipc"],
        [(142, 11, "1", "RUA", "Rua Principal", "100", "Apto 12", "Centro",
          "BARBACENA", "MG", "36200000")],
    ),
}


def fake_executar(sql, params):
    for k, (cols, rows) in fake_cols_rows.items():
        if k in sql:
            return [dict(zip(cols, r)) for r in rows]
    raise RuntimeError("nao mockado: " + sql[:80])


queries.executar = fake_executar

m = queries.consultar_medico(142)
c = queries.consultar_crms(142)
e = queries.consultar_especialidades(142)
r = queries.consultar_residencias(142)
end = queries.consultar_enderecos(142)

print("medico:", m["nome"], "|", m["instituicao_graduacao"])
print("crms:", [(x["crm"], x["uf"], x["situacao"]) for x in c])
print("especialidades:", [(x["especialidade"], x["rqe"], x["flag_sub"]) for x in e])
print("residencias:", [(x["nm_programa"], x["nm_instituicao"]) for x in r])
print("endereco:", end[0]["ds_city"], end[0]["co_stte"])

# Verificacao do bug: campo 'crm' da 1a linha precisa ser a STRING, nao None
assert c[0]["crm"] == "654321", "CRM veio errado: %r" % c[0]
assert e[0]["especialidade"] == "CARDIOLOGIA", "ESPECIALIDADE veio errada"
assert r[0]["nm_programa"] == "CARDIOLOGIA", "PROGRAMA veio errado"
print("OK — todos os campos do shape casam com o que o frontend (renderFicha) le.")
