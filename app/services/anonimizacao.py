"""Anonimização da lista de leads: nome mascarado, endereço oculto."""


def mascara_nome(nome):
    partes = [p for p in (nome or "").strip().split() if p]
    if not partes:
        return "ANONIMO"
    if len(partes) == 1:
        return f"{partes[0][0]}."
    return f"{partes[0]} {partes[-1][0]}."
