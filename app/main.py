"""cnesfy — API FastAPI fina + front estático.

Executar:  uvicorn app.main:app --reload
Modo mock: USE_MOCK=true (default) — sem Oracle e sem Credify reais.
"""
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import config, repositorio
from app.services import CUSTO_AVANCADO
from app.services.perfil import classificar
from app.services.tokens import saldo as servico_saldo
from app.services.tokens import debitar, estornar, extrato

FRONT_DIR = Path(__file__).resolve().parent.parent / "front"

app = FastAPI(title="cnesfy", version="0.1.0",
              description="Leads de médicos com créditos (mock)")

app.mount("/static", StaticFiles(directory=str(FRONT_DIR)), name="static")


@app.get("/")
def index():
    return FileResponse(str(FRONT_DIR / "index.html"))


# ---------------------------------------------------------------------------
# Lista anonimizada (grátis)
# ---------------------------------------------------------------------------
@app.get("/api/v1/medicos")
def lista_medicos(
    uf: str | None = Query(None),
    cidade: str | None = Query(None),
    especialidade: str | None = Query(None),
    sub_especialidade: str | None = Query(None),
    residencia: str | None = Query(None),
    situacao_crm: str | None = Query(None),
    sexo: str | None = Query(None),
    faixa_etaria: str | None = Query(None),
    apenas_com_enriquecimento: bool = Query(False),
    limite: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    filtros = {"uf": uf, "cidade": cidade, "especialidade": especialidade,
               "sub_especialidade": sub_especialidade, "residencia": residencia,
               "situacao_crm": situacao_crm, "sexo": sexo,
               "faixa_etaria": faixa_etaria,
               "apenas_com_enriquecimento": apenas_com_enriquecimento}
    ativos = {k: v for k, v in filtros.items() if v not in (None, False)}
    try:
        resultados, total = repositorio.listar_medicos(ativos, limite=limite, offset=offset)
    except Exception as e:  # ex.: falha de conexão Oracle -> JSON amigável, não 500 silencioso
        return JSONResponse(status_code=503, content={
            "modo": "mock" if config.USE_MOCK else "oracle",
            "erro": "falha_ao_consultar_a_base",
            "detalhe": str(e)[:400],
            "filtros": filtros,
            "resultados": [], "total": 0, "tem_mais": False})
    return {"modo": "mock" if config.USE_MOCK else "oracle",
            "filtros": filtros,
            "resultados": resultados,
            "total": total,
            "offset": offset,
            "limite": limite,
            "tem_mais": (offset + len(resultados)) < total}


# ---------------------------------------------------------------------------
# Opções de filtro (dropdowns) — uf/cidade/especialidade/sub/residência
# vêm DO BANCO; sexo e faixa etária são fixos (mockados)
# ---------------------------------------------------------------------------
@app.get("/api/v1/filtros")
def opcoes_filtros(uf: str | None = Query(None), especialidade: str | None = Query(None)):
    try:
        opcoes = repositorio.obter_opcoes_filtros(uf=uf or None, especialidade=especialidade or None)
    except Exception as e:
        return JSONResponse(status_code=503, content={
            "erro": "falha_ao_carregar_filtros", "detalhe": str(e)[:400]})
    opcoes["sexos"] = ["M", "F"]
    opcoes["faixas_etarias"] = ["ATE_29", "30_39", "40_49", "50_59", "60_MAIS"]
    return {"modo": "mock" if config.USE_MOCK else "oracle", **opcoes}


# ---------------------------------------------------------------------------
# Ficha básica (débito 700/2.000/4.000) — base + PF, sem quadro societário
# ---------------------------------------------------------------------------
@app.get("/api/v1/medicos/{id_medico}/ficha-basica")
def ficha_basica(id_medico: int, confirmar: bool = Query(False)):
    m = repositorio.detalhe_medico(id_medico)
    if not m:
        return JSONResponse(status_code=404, content={"erro": "medico_nao_encontrado"})

    perfil_info = classificar(m["especialidades"])
    custo = perfil_info["custo_tokens"]
    pf = repositorio.consultar_pf(m["cpf"]) if m.get("cpf") else None
    codigo = (pf or {}).get("RESPOSTA", {}).get("CODIGO", [])
    # CREDIFY real retorna CODIGO[x] como STRING ("1"/"2"/"3"); o MOCK
    # retorna INTEIRO (1/2/3). Comparei SEMPRE como string p/ casar os dois.
    codigo0 = str(codigo[0]).strip() if codigo else ""
    pf_encontrada = bool(m.get("cpf")) and codigo0 in ("1", "2")  # 2 = não encontrado sem penalidade

    # REGRA DE DÉBITO: o usuario CLICOU em 'abrir ficha' (confirmar=true),
    # portanto o preco do nivel (GENERALISTA/ESPECIALISTA/SUB) SEMPRE e cobrado,
    # independente da disponibilidade de dados PF. Antes: so debitava quando o
    # codigo[0] da Credify era 1 -> '0 tokens debitados' sempre que PF falhava.
    cobrado = 0
    if confirmar:
        ok, r = debitar("CONSUMO",
                        f"Ficha basica {perfil_info['perfil']} #{id_medico}",
                        custo, f"medico:{id_medico}")
        if not ok:
            return JSONResponse(status_code=402, content={"erro": r["erro"], **r})
        cobrado = custo

    def mascara_cpf(v):
        s = str(v or "")
        return (s[:3] + "." + s[3:6] + "." + s[6:9] + "-" + s[9:11]) if len(s) >= 11 else (s or None)

    def _cpf_enviado_credify(v):
        """CPF como enviado a Credify: somente digitos, zeros a esquerda
        preservados (mesma regra do CredifyClient._normalize_cpf_cnpj).
        Defensivo: se o normalizador real falhar, usa fallback local
        identico — nunca deixa o endpoint estourar 500."""
        if not v:
            return None
        try:
            from app.credify.client import CredifyClient
            return str(CredifyClient._normalize_cpf_cnpj(v))
        except Exception:
            s = "".join(ch for ch in str(v) if ch.isdigit())
            return s.zfill(11) if s and len(s) <= 11 else (s.zfill(14) if s else s)

    resp_pf = None
    if pf_encontrada:
        r = pf["RESPOSTA"]
        resp_pf = {"dados_cadastrais": r.get("DADOSCADASTRAIS"),
                   "enderecos":    r.get("ENDERECOS", []),
                   "telefones":    r.get("TELEFONES", []),
                   "emails":       r.get("EMAIL", []),
                   "participacao_societaria": None}  # nunca exibida na basica
    elif m.get("cpf"):
        resp_pf = {"dados_cadastrais": None, "enderecos": [], "telefones": [],
                   "emails": [], "participacao_societaria": None,
                   "aviso": ("PF nao encontrada na Credify (CODIGO[0]=%s). "
                             "Ficha basica entregue, sem dados de contato." % (codigo0 or "-"))}

    return {
        "id_medico": m["id_medico"], "perfil": perfil_info["perfil"],
        "custo_tokens": custo, "tokens_cobrados": cobrado,
        "pf_encontrada": pf_encontrada,
        # CPF volta em dois formatos p/ debug do front (sem expor ao cliente
        # o valor real alem do que ja tem na base mascarado):
        "cpf_base_mascarado": mascara_cpf(m.get("cpf")),
        # Debug: CPF enviado a Credify (somente digitos). Helper defensivo —
        # nunca gera 500 mesmo se o normalizador do client falhar.
        "cpf_enviado_credify": _cpf_enviado_credify(m.get("cpf")),
        "pf_codigo_pos0": codigo0,
        "dados_medico": {k: v for k, v in m.items() if k not in ("cpf",)},
        "pf": resp_pf,
        "prox": "/api/v1/medicos/{id}/ficha-avancada (+300)"
    }


# ---------------------------------------------------------------------------
# Ficha avançada (+300) — PJ dos vínculos do médico
# ---------------------------------------------------------------------------
@app.get("/api/v1/medicos/{id_medico}/ficha-avancada")
def ficha_avancada(id_medico: int, confirmar: bool = Query(False)):
    m = repositorio.detalhe_medico(id_medico)
    if not m:
        return JSONResponse(status_code=404, content={"erro": "medico_nao_encontrado"})

    pf = repositorio.consultar_pf(m["cpf"]) if m.get("cpf") else None
    vinculos = []
    if pf and (pf.get("RESPOSTA", {}).get("CODIGO") or [2])[4] == 1:
        vinculos = pf["RESPOSTA"].get("PARTICIPACAOSOCIETARIA", [])

    if not vinculos:
        return {"id_medico": m["id_medico"], "tokens_cobrados": 0,
                "aviso": "Médico sem vínculos empresariais — nada a cobrar",
                "empresas": []}

    custo = CUSTO_AVANCADO
    if confirmar:
        ok, r = debitar("CONSUMO", f"Ficha avançada (PJ) — #{id_medico}", custo,
                        f"medico:{id_medico}")
        if not ok:
            return JSONResponse(status_code=402, content={"erro": r["erro"], **r})

    empresas = []
    for v in vinculos:
        cnpj = v.get("CNPJ")
        pj = repositorio.consultar_pj(cnpj)
        empresas.append({"vinculo": v, "cnpj": cnpj,
                         "pj": pj.get("RESPOSTA", {}) if pj else None})
    return {"id_medico": m["id_medico"], "tokens_cobrados": custo if confirmar else 0,
            "custo_tokens": custo, "empresas": empresas}


# ---------------------------------------------------------------------------
# Painel — saldo e extrato (mock)
# ---------------------------------------------------------------------------
@app.get("/api/v1/painel/saldo")
def painel_saldo():
    return servico_saldo()


@app.get("/api/v1/painel/extrato")
def painel_extrato():
    return {"transacoes": extrato()}
