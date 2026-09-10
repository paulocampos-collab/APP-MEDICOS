"""SQL hardcoded das tabelas reais (usado com USE_MOCK=false).

Tabelas:
- credpf.credi01300_new        (médico)
- credpf.credi01301            (CRM por UF)
- credpf.credi01302            (especialidade)
- credpf.credi01303            (residência)
- Paulo.tmp_endereco_medico_principal (melhor endereço)
"""
from app.db.oracle import executar

SQL_MEDICO = """
SELECT ID_MEDICO, NOME, NOME_SOCIAL, CPF, ANO_CONCLUSAO,
       INSTITUICAO_GRADUACAO
FROM   credpf.credi01300_new
WHERE  ID_MEDICO = :id
"""

SQL_CRMS = """
SELECT ID_CRM, CRM, UF, SITUACAO, DT_PRIM_INSCRICAO_UF
FROM   credpf.credi01301
WHERE  ID_MEDICO = :id
"""

SQL_ESPECIALIDADES = """
SELECT ID_ESPECIALIDADE, ID_CRM, ESPECIALIDADE, RQE, FLAG_SUB, ID_ESP_SUB
FROM   credpf.credi01302
WHERE  ID_CRM IN (SELECT ID_CRM FROM credpf.credi01301 WHERE ID_MEDICO = :id)
"""

SQL_RESIDENCIAS = """
SELECT ID_RESIDENCIA, NM_PROGRAMA, NM_INSTITUICAO, SG_UF, DT_INICIO, DT_TERMINO
FROM   credpf.credi01303
WHERE  ID_MEDICO = :id
"""

SQL_ENDERECOS = """
SELECT NU_ADDR, CO_TYPE_ADDR, CO_TYPE_LOGR, DS_NAME_LOGR, CO_NUMB_LOGR,
       DS_CMPL_LOGR, DS_DIST, DS_CITY, CO_STTE, CO_ZIPC
FROM   Paulo.tmp_endereco_medico_principal
WHERE  ID_MEDICO = :id
"""

SQL_LISTA = """
SELECT m.ID_MEDICO,
       TRIM(m.NOME)              AS NOME,
       e.DS_CITY,
       e.CO_STTE                 AS UF,
       e.DS_DIST                 AS BAIRRO,
       m.CPF,
       (SELECT c.SITUACAO
          FROM credpf.credi01301 c
         WHERE c.ID_MEDICO = m.ID_MEDICO
           AND ROWNUM = 1)       AS SITUACAO_CRM,
       (SELECT COUNT(*)
          FROM credpf.credi01301 c
         WHERE c.ID_MEDICO = m.ID_MEDICO) AS QT_CRMS,
       (SELECT LISTAGG(e2.ESPECIALIDADE, ';') WITHIN GROUP (ORDER BY e2.ESPECIALIDADE)
          FROM credpf.credi01301 c2
          JOIN credpf.credi01302 e2 ON e2.ID_CRM = c2.ID_CRM
         WHERE c2.ID_MEDICO = m.ID_MEDICO) AS ESPECIALIDADES,
       (SELECT LISTAGG(r.NM_PROGRAMA, ';') WITHIN GROUP (ORDER BY r.NM_PROGRAMA)
          FROM credpf.credi01303 r
         WHERE r.ID_MEDICO = m.ID_MEDICO)  AS RESIDENCIAS
FROM   credpf.credi01300_new m
LEFT JOIN Paulo.tmp_endereco_medico_principal e
       ON e.ID_MEDICO = m.ID_MEDICO
WHERE  1 = 1
"""


def consultar_medicos():
    return executar(SQL_LISTA)


def consultar_medico(id_medico):
    rows = executar(SQL_MEDICO, {"id": id_medico})
    return rows[0] if rows else None


def consultar_crms(id_medico):
    return executar(SQL_CRMS, {"id": id_medico})


def consultar_especialidades(id_medico):
    return executar(SQL_ESPECIALIDADES, {"id": id_medico})


def consultar_residencias(id_medico):
    return executar(SQL_RESIDENCIAS, {"id": id_medico})


def consultar_enderecos(id_medico):
    return executar(SQL_ENDERECOS, {"id": id_medico})
