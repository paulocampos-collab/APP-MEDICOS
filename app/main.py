"""APP-MEDICOS — API FastAPI fina + front estático.

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

app = FastAPI(title="APP-MEDICOS", version="0.1.0",
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
    sub_especialidade: bool | None = Query(None),
    residencia: str | None = Query(None),
    situacao_crm: str | None = Query(None),
    sexo: str | None = Query(None),
    faixa_etaria: str | None = Query(None),
    apenas_com_enriquecimento: bool = Query(False),
):
    filtros = {"uf": uf, "cidade": cidade, "especialidade": especialidade,
               "sub_especialidade": sub_especialidade, "residencia": residencia,
               "situacao_crm": situacao_crm, "sexo": sexo,
               "faixa_etaria": faixa_etaria,
               "apenas_com_enriquecimento": apenas_com_enriquecimento}
    return {"modo": "mock" if config.USE_MOCK else "oracle",
            "filtros": filtros,
            "resultados": repositorio.listar_medicos({k: v for k, v in filtros.items() if v not in (None, False)})}


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
    codigo = (pf or {}).get("RESPOSTA", {}).get("CODIGO", [2])
    pf_encontrada = bool(m.get("cpf")) and codigo[0] == 1

    if pf_encontrada and confirmar:
        ok, r = debitar("CONSUMO",
                        f"Ficha básica {perfil_info['perfil']} — #{id_medico}",
                        custo, f"medico:{id_medico}")
        if not ok:
            return JSONResponse(status_code=402, content={"erro": r["erro"], **r})

    resp_pf = None
    if pf_encontrada:
        r = pf["RESPOSTA"]
        resp_pf = {"dados_cadastrais": r.get("DADOSCADASTRAIS"),
                   "enderecos": r.get("ENDERECOS", []),
                   "telefones": r.get("TELEFONES", []),
                   "emails": r.get("EMAIL", []),
                   "participacao_societaria": None}  # nunca exibida na básica
    elif m.get("cpf"):
        resp_pf = {"dados_cadastrais": None, "enderecos": [], "telefones": [],
                   "emails": [], "participacao_societaria": None,
                   "aviso": "PF não encontrada — entrega apenas o básico, sem débito do enriquecimento"}

    cobrado = custo if pf_encontrada and confirmar else 0
    return {"id_medico": m["id_medico"], "perfil": perfil_info["perfil"],
            "custo_tokens": custo, "tokens_cobrados": cobrado,
            "pf_encontrada": pf_encontrada,
            "dados_medico": {k: v for k, v in m.items() if k not in ("cpf",)},
            "pf": resp_pf,
            "prox": "/api/v1/medicos/{id}/ficha-avancada (+300)"}


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
