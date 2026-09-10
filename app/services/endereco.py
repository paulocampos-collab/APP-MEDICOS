"""Regra do melhor endereço do médico (Paulo.tmp_endereco_medico_principal).

Prioridade (fechada com o cliente):
1) tipo de endereço (CO_TYPE_ADDR: 1=residencial > 2=comercial > 3=correspondência)
2) completude (logradouro + número + cidade + UF preenchidos)
3) CEP válido (CO_ZIPC com 8 dígitos)
4) menor NU_ADDR (desempate estável e determinístico)
"""

PRIORIDADE_TIPO = {"1": 0, "2": 1, "3": 2}


def escolher_principal(enderecos):
    if not enderecos:
        return None

    def chave(e):
        tipo = PRIORIDADE_TIPO.get(str(e.get("CO_TYPE_ADDR") or e.get("co_type_addr") or ""), 9)
        completude = sum(1 for c in ("DS_NAME_LOGR", "CO_NUMB_LOGR", "DS_CITY", "CO_STTE")
                         if e.get(c))
        cep_ok = 1 if len(str(e.get("CO_ZIPC") or e.get("co_zipc") or "")) == 8 else 0
        nu = int(e.get("NU_ADDR") or e.get("nu_addr") or 0)
        return (tipo, -completude, -cep_ok, nu)

    return min(enderecos, key=chave)
