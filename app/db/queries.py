"""SQL hardcoded das tabelas reais (usado com USE_MOCK=false).

Tabelas:
- credpf.credi01300_new        (médico)
- credpf.credi01301            (CRM por UF)
- credpf.credi01302            (especialidade)
- credpf.credi01303            (residência)
- Paulo.tmp_endereco_medico_principal (melhor endereço)

Princípio de desempenho: TODA filtragem acontece no banco (WHERE dinâmico),
com COUNT para o total e paginação (OFFSET/FETCH). A aplicação nunca carrega
a base inteira em memória — devolve no máximo `limite` linhas por chamada.
"""
from app.db.oracle import executar

# =========================================================================
# 1 endereço principal por médico (regra fechada: tipo -> completude ->
# CEP válido -> menor NU_ADDR)
# =========================================================================
SQL_ENDERECO_PRINCIPAL = """
SELECT ID_MEDICO, DS_CITY, CO_STTE, DS_DIST
FROM (
    SELECT ID_MEDICO, DS_CITY, CO_STTE, DS_DIST,
           ROW_NUMBER() OVER (
               PARTITION BY ID_MEDICO
               ORDER BY DECODE(CO_TYPE_ADDR, '1', 0, '2', 1, '3', 2, 9),
                        CASE WHEN DS_NAME_LOGR IS NOT NULL AND CO_NUMB_LOGR IS NOT NULL
                                  AND DS_CITY IS NOT NULL AND CO_STTE IS NOT NULL
                             THEN 0 ELSE 1 END,
                        CASE WHEN LENGTH(TRIM(CO_ZIPC)) = 8 THEN 0 ELSE 1 END,
                        NU_ADDR
           ) rn
    FROM Paulo.tmp_endereco_medico_principal
)
WHERE rn = 1
"""

# =========================================================================
# SELECT base da lista (as pontas de especialidade/residência/situação do
# CRM entram como EXISTS no WHERE, para o Oracle filtrar antes de agregar)
# =========================================================================
SQL_LISTA_BASE = """
SELECT m.ID_MEDICO,
       TRIM(m.NOME) AS NOME,
       e.DS_CITY,
       e.CO_STTE AS UF,
       e.DS_DIST AS BAIRRO,
       m.CPF,
       (SELECT c.SITUACAO
          FROM credpf.credi01301 c
         WHERE c.ID_MEDICO = m.ID_MEDICO
           AND ROWNUM = 1) AS SITUACAO_CRM,
       (SELECT LISTAGG(e2.ESPECIALIDADE, ';') WITHIN GROUP (ORDER BY e2.ESPECIALIDADE)
          FROM credpf.credi01301 c2
          JOIN credpf.credi01302 e2 ON e2.ID_CRM = c2.ID_CRM
         WHERE c2.ID_MEDICO = m.ID_MEDICO) AS ESPECIALIDADES,
       (SELECT LISTAGG(r.NM_PROGRAMA, ';') WITHIN GROUP (ORDER BY r.NM_PROGRAMA)
          FROM credpf.credi01303 r
         WHERE r.ID_MEDICO = m.ID_MEDICO) AS RESIDENCIAS
FROM credpf.credi01300_new m
LEFT JOIN (__ENDERECO__) e ON e.ID_MEDICO = m.ID_MEDICO
WHERE 1 = 1
"""


def montar_where(filtros):
    """Constrói cláusulas WHERE a partir dos filtros (bind parameters)."""
    conds, params = [], {}
    if filtros.get("uf"):
        params["uf"] = str(filtros["uf"]).upper()
        conds.append("UPPER(e.CO_STTE) = :uf")
    if filtros.get("cidade"):
        params["cidade"] = str(filtros["cidade"]).upper()
        conds.append("UPPER(e.DS_CITY) = :cidade")
    if filtros.get("especialidade"):
        params["esp"] = str(filtros["especialidade"]).upper()
        conds.append(
            "EXISTS (SELECT 1 FROM credpf.credi01301 c2 "
            "JOIN credpf.credi01302 e2 ON e2.ID_CRM = c2.ID_CRM "
            "WHERE c2.ID_MEDICO = m.ID_MEDICO AND UPPER(e2.ESPECIALIDADE) = :esp)")
    if filtros.get("residencia"):
        params["res"] = str(filtros["residencia"]).upper()
        conds.append(
            "EXISTS (SELECT 1 FROM credpf.credi01303 r "
            "WHERE r.ID_MEDICO = m.ID_MEDICO AND UPPER(r.NM_PROGRAMA) = :res)")
    if filtros.get("situacao_crm"):
        params["sit"] = str(filtros["situacao_crm"]).upper()
        conds.append(
            "EXISTS (SELECT 1 FROM credpf.credi01301 c3 "
            "WHERE c3.ID_MEDICO = m.ID_MEDICO AND UPPER(c3.SITUACAO) = :sit)")
    if filtros.get("apenas_com_enriquecimento"):
        conds.append("m.CPF IS NOT NULL")
    where = (" AND " + " AND ".join(conds)) if conds else ""
    return where, params


def consultar_medicos_com_filtros(filtros=None, limite=50, offset=0):
    """Lista paginada de médicos + total. FILTRA NO BANCO (nunca em memória)."""
    filtros = filtros or {}
    where, params = montar_where(filtros)

    sql = (SQL_LISTA_BASE.replace("__ENDERECO__", SQL_ENDERECO_PRINCIPAL) + where
           + " ORDER BY m.ID_MEDICO"
             " OFFSET :offset ROWS FETCH NEXT :limite ROWS ONLY")
    p = dict(params)
    p["limite"] = int(limite)
    p["offset"] = int(offset)
    rows = executar(sql, p)

    sql_count = ("SELECT COUNT(*) AS TOTAL"
                 " FROM credpf.credi01300_new m"
                 " LEFT JOIN (__ENDERECO__) e ON e.ID_MEDICO = m.ID_MEDICO"
                 " WHERE 1 = 1" + where).replace("__ENDERECO__", SQL_ENDERECO_PRINCIPAL)
    total = executar(sql_count, dict(params))[0]["TOTAL"]

    return rows, total


# =========================================================================
# Detalhe do médico (por ID — sempre pontual)
# =========================================================================
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
