"""Cliente da API Credify — auth com cache (24h) + refresh automático no 401.

POST {BASE}/auth          -> { "ClientID": ..., "ClientSecret": ... } -> Dados = token JWT
POST {BASE}/pfpesquisa    -> { "Consulta": { "IdConsulta":"328", "CpfCnpj":..., "TipoPessoa":"F" } }
POST {BASE}/pjpesquisa    -> { "Consulta": { "IdConsulta":"329", "CpfCnpj":..., "TipoPessoa":"J" } }

No modo USE_MOCK=true as chamadas retornam as simulações de app/mock_data.py
(sem rede, sem credencial real em lugar nenhum).
"""
import time

import httpx

from app import config
from app import repositorio  # noqa: F401  (apenas para não circular no mock)

_TOKEN = {"valor": None, "expira_em": 0.0}


class CredifyClient:
    def __init__(self):
        self.base = config.CREDIFY_BASE_URL
        self.timeout = httpx.Timeout(30.0)

    # ---------------- auth com cache ----------------
    def _token_valido(self):
        return self._TOKEN()["valor"] and time.time() < self._TOKEN()["expira_em"]

    @staticmethod
    def _TOKEN():
        return _TOKEN

    def autenticar(self):
        payload = {"ClientID": config.CREDIFY_CLIENT_ID,
                   "ClientSecret": config.CREDIFY_CLIENT_SECRET}
        with httpx.Client(timeout=self.timeout) as c:
            r = c.post(self.base + config.CREDIFY_AUTH_PATH, json=payload)
            r.raise_for_status()
            dados = r.json().get("Dados")
            if not dados:
                raise RuntimeError(f"Credify auth sem token: {r.json()}")
        ttl = config.CREDIFY_TOKEN_TTL_HORAS * 3600 * 0.95  # margem de 5%
        _TOKEN.update(valor=dados, expira_em=time.time() + ttl)
        return dados

    def _headers(self):
        if not self._token_valido():
            self.autenticar()
        return {"Authorization": f"Bearer {_TOKEN['valor']}",
                "Content-Type": "application/json"}

    # ---------------- chamadas com retry (401 renova token) ----------------
    def _post(self, path, payload):
        headers = self._headers()
        with httpx.Client(timeout=self.timeout) as c:
            r = c.post(self.base + path, json=payload, headers=headers)
            if r.status_code == 401:  # token expirado -> renova e tenta 1x
                _TOKEN.update(valor=None, expira_em=0.0)
                headers = self._headers()
                r = c.post(self.base + path, json=payload, headers=headers)
            r.raise_for_status()
            return r.json()

    # ---------------- PF / PJ ----------------
    def consultar_pf(self, cpf):
        payload = {"Consulta": {"IdConsulta": "328", "CpfCnpj": cpf, "TipoPessoa": "F"}}
        return self._post(config.CREDIFY_PF_PATH, payload)

    def consultar_pj(self, cnpj):
        payload = {"Consulta": {"IdConsulta": "329", "CpfCnpj": cnpj, "TipoPessoa": "J"}}
        return self._post(config.CREDIFY_PJ_PATH, payload)
