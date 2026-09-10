"""Configuração central — tudo vindo de variáveis de ambiente (.env)."""
import logging
import os

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("cnesfy")


def _bool(v):
    return str(v).strip().lower() in ("1", "true", "yes", "sim")


# true = dados mocados (default) / false = Oracle + Credify reais
USE_MOCK = _bool(os.getenv("USE_MOCK", "true"))
logger.info("MODO DE EXECUCAO: %s", "MOCK (dados de exemplo, sem banco)" if USE_MOCK else "ORACLE + CREDIFY (producao)")

# Banco Oracle — suporta DSN completo OU host/porta/servico separados
ORACLE_DSN = os.getenv("ORACLE_DSN", "").strip()
ORACLE_HOST = os.getenv("ORACLE_HOST", "").strip()
ORACLE_PORT = int(os.getenv("ORACLE_PORT", "1521"))
ORACLE_SERVICE = os.getenv("ORACLE_SERVICE", "").strip()
ORACLE_USER = os.getenv("ORACLE_USER", "").strip()
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "").strip()

# Credify (produção)
CREDIFY_CLIENT_ID = os.getenv("CREDIFY_CLIENT_ID", "").strip()
CREDIFY_CLIENT_SECRET = os.getenv("CREDIFY_CLIENT_SECRET", "").strip()
CREDIFY_BASE_URL = os.getenv("CREDIFY_BASE_URL", "https://api.credify.com.br").rstrip("/")
CREDIFY_AUTH_PATH = os.getenv("CREDIFY_AUTH_PATH", "/auth")
CREDIFY_PF_PATH = os.getenv("CREDIFY_PF_PATH", "/pfpesquisa")
CREDIFY_PJ_PATH = os.getenv("CREDIFY_PJ_PATH", "/pjpesquisa")
CREDIFY_TOKEN_TTL_HORAS = float(os.getenv("CREDIFY_TOKEN_TTL_HORAS", "24"))

# Carteira (mock)
SALDO_INICIAL_TOKENS = int(os.getenv("SALDO_INICIAL_TOKENS", "1000000"))
