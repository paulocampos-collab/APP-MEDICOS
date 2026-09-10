"""Normalização de texto: CAIXA ALTA + sem acentuação (padrão do produto)."""
import unicodedata


def normalizar(texto):
    """'Cardiologia' -> 'CARDIOLOGIA'; 'Clinica Médica' -> 'CLINICA MEDICA'."""
    if not texto:
        return ""
    t = unicodedata.normalize("NFD", str(texto))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.upper().strip()
