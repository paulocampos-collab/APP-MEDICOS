"""Camada de dados: escolhe mock (USE_MOCK=true) ou Oracle real (USE_MOCK=false).

Funções públicas (mesma assinatura nos dois modos):
  listar_medicos(filtros) -> lista anonimizada de leads
  detalhe_medico(id)      -> dados completos do médico (base)
  consultar_pf(cpf) / consultar_pj(cnpj) -> payloads Credify
"""
from app import config

if config.USE_MOCK:
    from app.mock_data import (MEDICOS, CRMS, ESPECIALIDADES, RESIDENCIAS,
                               ENDERECOS, SIMULACOES_PF, SIMULACOES_PJ,
                               CPF_NAO_ENCONTRADO, CNPJ_NAO_ENCONTRADO)
else:
    from app.db.queries import (consultar_medicos_com_filtros,
                                consultar_opcoes_filtros,
                                consultar_medico, consultar_crms,
                                consultar_especialidades, consultar_residencias,
                                consultar_enderecos)
    from app.credify.client import CredifyClient

from app.services.endereco import escolher_principal
from app.services.anonimizacao import mascara_nome
from app.services.texto import normalizar


def _idade(dt_nasc):
    import datetime
    if not dt_nasc:
        return None
    n = datetime.date.fromisoformat(str(dt_nasc)[:10])
    hoje = datetime.date.today()
    return hoje.year - n.year - ((hoje.month, hoje.day) < (n.month, n.day))


def _faixa_etaria(idade):
    if idade is None:
        return "INDEFINIDA"
    if idade < 30:
        return "ATE_29"
    if idade < 40:
        return "30_39"
    if idade < 50:
        return "40_49"
    if idade < 60:
        return "50_59"
    return "60_MAIS"


# =========================================================================
# MODO MOCK — fixtures de app/mock_data.py
# =========================================================================
def _listar_medicos_mock(filtros):
    resultado = []
    for m in MEDICOS:
        crms = CRMS.get(m["id_medico"], [])
        esp_por_crm = []
        for c in crms:
            esp_por_crm += ESPECIALIDADES.get(c["id_crm"], [])
        end = escolher_principal(ENDERECOS.get(m["id_medico"], []))
        cidade = (end or {}).get("ds_city")
        uf = (end or {}).get("co_stte")
        bairro = (end or {}).get("ds_dist")
        idade = _idade(m.get("dt_nascimento"))
        perfis = [e.get("especialidade") for e in esp_por_crm] or ["NAO_INFORMADO"]
        resid_prog = [r.get("programa", "") for r in RESIDENCIAS.get(m["id_medico"], [])]
        sit_crms = [c.get("situacao", "") for c in crms]

        if filtros.get("uf") and filtros["uf"].upper() != (uf or "").upper():
            continue
        if filtros.get("cidade") and filtros["cidade"].upper() != (cidade or "").upper():
            continue
        if filtros.get("especialidade") and filtros["especialidade"].upper() not in [p.upper() for p in perfis]:
            continue
        if filtros.get("sub_especialidade"):
            sub = filtros["sub_especialidade"].upper()
            tem_sub = any(normalizar(e.get("especialidade")) == sub
                          and (e.get("flag_sub") or e.get("id_esp_sub")) for e in esp_por_crm)
            if not tem_sub:
                continue
        if filtros.get("residencia") and filtros["residencia"].upper() not in [r.upper() for r in resid_prog]:
            continue
        if filtros.get("situacao_crm") and filtros["situacao_crm"].upper() not in [s.upper() for s in sit_crms]:
            continue
        if filtros.get("sexo") and filtros["sexo"].upper() != (m.get("sexo") or "").upper():
            continue
        if filtros.get("faixa_etaria") and filtros["faixa_etaria"].upper() != _faixa_etaria(idade):
            continue
        if filtros.get("apenas_com_enriquecimento") and not m.get("cpf"):
            continue

        resultado.append({
            "id_medico": m["id_medico"],
            "nome_anonimizado": mascara_nome(m["nome"]),
            "especialidades": perfis,
            "cidade": cidade, "uf": uf, "bairro": bairro,
            "situacao_crm": sit_crms[0] if sit_crms else None,
            "faixa_etaria": _faixa_etaria(idade),
            "sexo": m.get("sexo"),
            "tem_enriquecimento": bool(m.get("cpf")),
        })
    return resultado


# =========================================================================
# MODO ORACLE — filtragem NO BANCO (WHERE dinâmico) + paginação
# =========================================================================
def _listar_medicos_oracle(filtros, limite, offset):
    rows, total = consultar_medicos_com_filtros(filtros, limite=limite, offset=offset)
    resultado = []
    for r in rows:
        uf = r.get("UF") or r.get("CO_STTE")
        cidade = r.get("DS_CITY")
        bairro = r.get("BAIRRO") or r.get("DS_DIST")
        esp = [p.strip() for p in (r.get("ESPECIALIDADES") or "").split(";") if p.strip()]
        resid = [x.strip() for x in (r.get("RESIDENCIAS") or "").split(";") if x.strip()]
        resultado.append({
            "id_medico": r.get("ID_MEDICO"),
            "nome_anonimizado": mascara_nome(r.get("NOME")),
            "especialidades": esp or ["NAO_INFORMADO"],
            "cidade": cidade, "uf": uf, "bairro": bairro,
            "situacao_crm": r.get("SITUACAO_CRM"),
            "faixa_etaria": None, "sexo": None,  # dependem de staging (a evoluir)
            "tem_enriquecimento": bool(r.get("CPF")),
        })
    return resultado, total


def listar_medicos(filtros=None, limite=50, offset=0):
    filtros = filtros or {}
    if config.USE_MOCK:
        todos = _listar_medicos_mock(filtros)
        return todos[offset:offset + limite], len(todos)
    return _listar_medicos_oracle(filtros, limite, offset)


# =========================================================================
# Opções de filtro (dropdowns) — mock e Oracle com o MESMO padrão
# (caixa alta, sem acento, ordenado)
# =========================================================================
def _obter_opcoes_mock(uf=None, especialidade=None):
    ufs = sorted({normalizar(e["co_stte"]) for lista in ENDERECOS.values()
                  for e in lista if e.get("co_stte")})
    cidades = sorted({normalizar(e["ds_city"]) for lista in ENDERECOS.values()
                      for e in lista if e.get("ds_city")
                      and (not uf or normalizar(e["co_stte"]) == uf)})

    esp_principais = set()
    subs = set()
    for lista in ESPECIALIDADES.values():
        # pai = linha do mesmo CRM sem flag_sub/id_esp_sub; sub = demais
        pais = {normalizar(e.get("especialidade"))
                for e in lista if not (e.get("flag_sub") or e.get("id_esp_sub"))}
        esp_principais.update(p for p in pais if p)
        for e in lista:
            if e.get("flag_sub") or e.get("id_esp_sub"):
                nome = normalizar(e.get("especialidade"))
                if nome and (not especialidade or especialidade in pais):
                    subs.add(nome)

    residencias = sorted({normalizar(r.get("programa")) for lista in RESIDENCIAS.values()
                          for r in lista if r.get("programa")})
    return {
        "ufs": ufs,
        "cidades": cidades,
        "especialidades": sorted(esp_principais),
        "subespecialidades": sorted(subs),
        "residencias": residencias,
    }


def obter_opcoes_filtros(uf=None, especialidade=None):
    uf = (uf or "").upper() or None
    especialidade = (especialidade or "").upper() or None
    if config.USE_MOCK:
        return _obter_opcoes_mock(uf=uf, especialidade=especialidade)
    return consultar_opcoes_filtros(uf=uf, especialidade=especialidade)


def detalhe_medico(id_medico):
    if config.USE_MOCK:
        m = next((x for x in MEDICOS if x["id_medico"] == int(id_medico)), None)
        if not m:
            return None
        crms = CRMS.get(m["id_medico"], [])
        return {
            "id_medico": m["id_medico"],
            "nome": m["nome"],
            "nome_social": m.get("nome_social"),
            "cpf": m.get("cpf"),
            "sexo": m.get("sexo"),
            "ano_conclusao": m.get("ano_conclusao"),
            "instituicao_graduacao": m.get("instituicao_graduacao"),
            "crms": crms,
            "especialidades": {c["id_crm"]: ESPECIALIDADES.get(c["id_crm"], []) for c in crms},
            "residencias": RESIDENCIAS.get(m["id_medico"], []),
            "endereco_principal": escolher_principal(ENDERECOS.get(m["id_medico"], [])),
        }
    # ORACLE: falhas parciais (ex.: coluna errada em credi01303) NAO podem
    # derrubar a ficha inteira. Cada sub-query entra em try/except e devolve
    # lista vazia + entrada em "_diagnostico_oracle" para a UI mostrar o aviso.
    diag = []
    try:
        m = consultar_medico(id_medico)
    except Exception as e:
        diag.append({"secao": "medico", "erro": str(e)[:300]})
        return {"id_medico": id_medico, "_diagnostico_oracle": diag}
    if not m:
        return None

    try:
        crms = consultar_crms(id_medico)
    except Exception as e:
        diag.append({"secao": "crms", "erro": str(e)[:300]})
        crms = []
    try:
        esp_map = {c["id_crm"]: consultar_especialidades(id_medico) for c in (crms or [])}
    except Exception as e:
        diag.append({"secao": "especialidades", "erro": str(e)[:300]})
        esp_map = {}
    try:
        resid = consultar_residencias(id_medico)
    except Exception as e:
        diag.append({"secao": "residencias", "erro": str(e)[:300]})
        resid = []
    try:
        ends = consultar_enderecos(id_medico)
    except Exception as e:
        diag.append({"secao": "enderecos", "erro": str(e)[:300]})
        ends = []
    return {
        "id_medico":              m["id_medico"],
        "nome":                    m.get("nome"),
        "nome_social":             m.get("nome_social"),
        "cpf":                     str(m.get("cpf")) if m.get("cpf") else None,
        "sexo":                    None,
        "ano_conclusao":           m.get("ano_conclusao"),
        "instituicao_graduacao":   m.get("instituicao_graduacao"),
        "crms":                    crms,
        "especialidades":          esp_map,
        "residencias":             resid,
        "endereco_principal":      escolher_principal(ends),
        "_diagnostico_oracle":     diag or None,
    }


def consultar_pf(cpf):
    if config.USE_MOCK:
        return SIMULACOES_PF.get(cpf, CPF_NAO_ENCONTRADO)
    return CredifyClient().consultar_pf(cpf)


def consultar_pj(cnpj):
    if config.USE_MOCK:
        return SIMULACOES_PJ.get(cnpj, CNPJ_NAO_ENCONTRADO)
    return CredifyClient().consultar_pj(cnpj)
