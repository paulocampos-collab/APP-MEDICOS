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
# Padrão do produto: CAIXA ALTA + SEM ACENTUAÇÃO (igual nos dois modos)
# =========================================================================
_ACENTOS = "ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ"
_SEM_ACENTO = "AAAAAEEEEIIIIOOOOOUUUUC"


def _norm(col):
    return f"UPPER(TRANSLATE(TRIM({col}), '{_ACENTOS}', '{_SEM_ACENTO}'))"

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
            "WHERE c2.ID_MEDICO = m.ID_MEDICO AND UPPER(e2.ESPECIALIDADE) = :esp "
            "AND e2.ID_ESP_SUB IS NULL)")
    if filtros.get("sub_especialidade"):
        params["sub"] = str(filtros["sub_especialidade"]).upper()
        conds.append(
            "EXISTS (SELECT 1 FROM credpf.credi01302 e4 "
            "WHERE e4.ID_CRM IN (SELECT c4.ID_CRM FROM credpf.credi01301 c4 "
            "WHERE c4.ID_MEDICO = m.ID_MEDICO) "
            "AND e4.ID_ESP_SUB IS NOT NULL AND " + _norm("e4.ESPECIALIDADE") + " = :sub)")
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
SELECT id_medico, nome, nome_social, cpf, ano_conclusao, instituicao_graduacao
FROM   credpf.credi01300_new
WHERE  id_medico = :id
"""

# Chaves em CAIXA BAIXA para casar exatamente com app/mock_data.py e
# com o que o frontend (front/app.js -> renderFicha) lê. Sem isso,
# renderFicha recebe 'CRM','UF','SITUACAO' (uppercase do Oracle) e imprime
# 'undefined' em todas as colunas (bug visível na captura do cliente).
SQL_CRMS = """
SELECT id_medico, id_crm, crm, uf, situacao, dt_prim_inscricao_uf
FROM   credpf.credi01301
WHERE  id_medico = :id
"""

SQL_ESPECIALIDADES = """
SELECT id_especialidade, id_crm, especialidade, rqe, flag_sub, id_esp_sub
FROM   credpf.credi01302
WHERE  id_crm IN (SELECT id_crm FROM credpf.credi01301 WHERE id_medico = :id)
"""

SQL_RESIDENCIAS = """
SELECT id_residencia, programa AS nm_programa, instituicao AS nm_instituicao,
       sg_uf, dt_inicio, dt_termino
FROM   credpf.credi01303
WHERE  id_medico = :id
"""

SQL_ENDERECOS = """
SELECT id_medico, nu_addr, co_type_addr, co_type_logr, ds_name_logr,
       co_numb_logr, ds_cmpl_logr, ds_dist, ds_city, co_stte, co_zipc
FROM   Paulo.tmp_endereco_medico_principal
WHERE  id_medico = :id
"""


# =========================================================================
# Opções de filtro (dropdowns) — carregadas DO BANCO
# uf/cidades  -> Paulo.tmp_endereco_medico_principal
# especialidade/sub -> credpf.credi01302 (sub = linha com ID_ESP_SUB)
# residencia -> credpf.credi01303 (NM_PROGRAMA)
# =========================================================================
def consultar_opcoes_filtros(uf=None, especialidade=None):
    opcoes = {"ufs": [], "cidades": [], "especialidades": [],
              "subespecialidades": [], "residencias": []}

    opcoes["ufs"] = [r["UF"] for r in executar(
        "SELECT DISTINCT " + _norm("CO_STTE") + " AS UF"
        " FROM Paulo.tmp_endereco_medico_principal"
        " WHERE CO_STTE IS NOT NULL"
        " ORDER BY UF")]

    if uf:
        opcoes["cidades"] = [r["CIDADE"] for r in executar(
            "SELECT DISTINCT " + _norm("DS_CITY") + " AS CIDADE"
            " FROM Paulo.tmp_endereco_medico_principal"
            " WHERE DS_CITY IS NOT NULL AND " + _norm("CO_STTE") + " = :uf"
            " ORDER BY CIDADE", {"uf": str(uf).upper()})]
    else:
        opcoes["cidades"] = [r["CIDADE"] for r in executar(
            "SELECT DISTINCT " + _norm("DS_CITY") + " AS CIDADE"
            " FROM Paulo.tmp_endereco_medico_principal"
            " WHERE DS_CITY IS NOT NULL"
            " ORDER BY CIDADE")]

    # Especialidade PRINCIPAL = linha SEM ID_ESP_SUB
    opcoes["especialidades"] = [r["ESP"] for r in executar(
        "SELECT DISTINCT " + _norm("ESPECIALIDADE") + " AS ESP"
        " FROM credpf.credi01302"
        " WHERE ESPECIALIDADE IS NOT NULL AND ID_ESP_SUB IS NULL"
        " ORDER BY ESP")]

    # Sub-especialidade = linha COM ID_ESP_SUB (dependente da especialidade pai)
    if especialidade:
        sql_sub = (
            "SELECT DISTINCT " + _norm("e.ESPECIALIDADE") + " AS SUB"
            + " FROM credpf.credi01302 e"
            + " WHERE e.ID_ESP_SUB IS NOT NULL"
            + " AND (SELECT " + _norm("p.ESPECIALIDADE")
            + " FROM credpf.credi01302 p"
            + " WHERE p.ID_ESPECIALIDADE = e.ID_ESP_SUB) = :esp"
            + " ORDER BY SUB")
        opcoes["subespecialidades"] = [r["SUB"] for r in executar(
            sql_sub, {"esp": str(especialidade).upper()})]
    else:
        opcoes["subespecialidades"] = [r["SUB"] for r in executar(
            "SELECT DISTINCT " + _norm("ESPECIALIDADE") + " AS SUB"
            + " FROM credpf.credi01302"
            + " WHERE ESPECIALIDADE IS NOT NULL AND ID_ESP_SUB IS NOT NULL"
            + " ORDER BY SUB")]

    opcoes["residencias"] = [r["RES"] for r in executar(
        "SELECT DISTINCT " + _norm("NM_PROGRAMA") + " AS RES"
        " FROM credpf.credi01303"
        " WHERE NM_PROGRAMA IS NOT NULL"
        " ORDER BY RES")]
    return opcoes


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
