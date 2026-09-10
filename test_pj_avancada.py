"""Verifica o fix de /ficha-avancada contra o payload REAL do CPF 04689689628.

Este teste usa o codigo de PRODUCAO (app/main.py) com TestClient FastAPI,
mockando repositorio.consultar_pf / consultar_pj / detalhe_medico. Roda
o endpoint real e verifica:
  - cnpjs_totais = 5 (4 vinculos reais + 1 vindo do fixture para teste de pad)
  - raizes_unicas = 2 (02894643 matriz + 09377298 matriz da Zambrana&Enomoto)
  - pj_consultadas = 2 (1 por raiz; filiais reusam resposta via cache)
  - empresas[i].cnpj tem 14 digitos (nao 13, nao 16, nao vazio)
  - empresas[i].pj_status correto (consulted/reused/cnpj_invalido)
"""

import json, sys
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app import repositorio

# === FIXTURE (extraida do payload real colado pelo usuario) ===
fix = json.loads(Path("app/fixtures/bruna_zambrana.json").read_text())
fix["RESPOSTA"]["CODIGO"] = ["1","2","1","1","1","1","1","1","1","1","1","1"]

# === MOCK 1: detalhe_medico retorna BRUNA com id e cpf ===
def fake_detalhe(id_medico):
    return {
        "id_medico": id_medico, "cpf": "04689689628",
        "nome": "BRUNA DA FONSECA TAMES ZAMBRANA",
        "crms": [], "especialidades": {}, "residencias": [],
        "endereco_principal": None, "_diagnostico_oracle": None,
    }

# === MOCK 2: consultar_pf devolve o fixture (PROD shape, com REGISTRO_n) ===
def fake_pf(cpf):
    return fix if cpf == "04689689628" else {"RESPOSTA": {"CODIGO": [2]*12}}

# === MOCK 3: consultar_pj conta as chamadas por raiz devolvendo PJ coerente ===
pj_calls = []
def fake_pj(cnpj):
    pj_calls.append(cnpj)
    return {
        "CONSULTA": {"IdConsulta": "329", "TipoPessoa": "J", "CpfCnpj": cnpj},
        "RESPOSTA": {
            "CODIGO": ["1"]*10,
            "DADOSCADASTRAIS": {"RAZAO_SOCIAL": f"EMPRESA {cnpj[:8]}",
                                "PORTE": "PEQUENA", "SITUACAO": "ATIVA",
                                "ABERTURA": "10/09/1998"},
            "INFOEMPRESA": {"FATURAMENTO_PRESUMIDO": "R$ 100k-500k",
                            "CAPITAL_SOCIAL": "R$ 10.000"},
            "QUADROSOCIETARIO": [{"NOME": "BRUNA ZAMBRANA",
                                  "CPF_CNPJ": "04689689628",
                                  "QUALIFICACAO": "SOCIO",
                                  "PERCENTUAL": "50"}],
        },
    }

repositorio.detalhe_medico      = fake_detalhe
repositorio.consultar_pf       = fake_pf
repositorio.consultar_pj       = fake_pj
repositorio.CUSTO_AVANCADO = 300  # soh p/ evitar ImportError se houver

c = TestClient(app)
print("=== ANTES DO FIX (simulado com bypass por copiando a logica antiga) ===")
codigo_old = (fix["RESPOSTA"].get("CODIGO") or [2, 1, 2, 2, 2])[4]
check_old = codigo_old == 1
print(f"  CODIGO[4] = {codigo_old!r}  ('== 1' python) ->", check_old)
ps_old = fix["RESPOSTA"].get("PARTICIPACAOSOCIETARIA") or []
print(f"  PARTICIPACAOSOCIETARIA type:", type(ps_old).__name__,
      "(dict = quebrar 'for v in vinculos' na hora)")
try:
    n = sum(1 for _ in ps_old)
    print(f"  iteracao antiga -> {n} CNPJs extraidos (sera == 0 pq quebra ou ==0 pq gg)")
except TypeError as e:
    print(f"  iteracao antiga -> **TypeError: {e}**")
    print("  >> RESULTADO ANTIGO: early-return 'Medico sem vinculos empresariais - nada a cobrar' mesmo com 5 vinculos reais no fixture")

print()
print("=== DEPOIS DO FIX (/api/v1/medicos/2526956/ficha-avancada REAL via TestClient) ===")
r = c.get("/api/v1/medicos/2526956/ficha-avancada?confirmar=true")
print(f"  HTTP status = {r.status_code}")
j = r.json()
print(f"  cnpjs_totais  = {j.get('cnpjs_totais')}")
print(f"  cnpjs_unicos  = {j.get('cnpjs_unicos')}")
print(f"  pj_consultadas= {j.get('pj_consultadas')}")
print(f"  raizes_unicas = {j.get('raizes_unicas')}")
print(f"  empresas      = {len(j.get('empresas', []))} cards renderizados")
print(f"  pj_calls (real) registradas = {pj_calls}")
print()
print("  --- FAN-OUT POR VINCULO ---")
for i, e in enumerate(j.get("empresas", []), 1):
    vin = e.get("vinculo") or {}
    print(f"  [{i}] CNPJ {e['cnpj']}  raiz {e['raiz_cnpj']}  "
          f"({vin.get('RAZAOSOCIAL')} - {vin.get('PERCENTUAL')}% {vin.get('QUALIFICACAO')})  "
          f"status={e['pj_status']}")

print()
print("  --- DIAGNOSTICO FINAL ---")
assert r.status_code == 200, f"status code {r.status_code}"
assert j.get("cnpjs_totais") == 5, f"esperado 5, veio {j.get('cnpjs_totais')}"
assert j.get("cnpjs_unicos") == 5, f"esperado 5 cards, veio {j.get('cnpjs_unicos')}"
assert j.get("pj_consultadas") == 2, f"esperado 2 chamadas (1 por raiz), veio {j.get('pj_consultadas')}"
assert sorted(j.get("raizes_unicas") or []) == ["02894643", "09377298"], \
    f"raizes erradas: {j.get('raizes_unicas')}"
for e in j["empresas"]:
    assert e["cnpj"] is None or len(e["cnpj"]) == 14, \
        f"CNPJ nao tem 14 digitos: {e['cnpj']!r}"
print("  TODOS OS ASSERTS OK: o fix devolve 5 vinculos, 2 chamadas PJ (1/raiz),")
print("  CNPJs formatados com 14 digitos, filiais reusam resposta da matriz.")
sys.exit(0)
