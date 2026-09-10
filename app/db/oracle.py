"""Conexão Oracle (thin mode — não precisa de cliente Oracle instalado).

Modos de DSN:
  1) ORACLE_DSN completo  ->  ex.: "10.0.0.5:1521/ORCLPDB1"
  2) ORACLE_HOST + ORACLE_PORT + ORACLE_SERVICE (usado se DSN vazio)

Teste rápido: python -c "from app.db.oracle import executar; print(executar('SELECT 1 FROM dual'))"
"""
import oracledb

from app import config

_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        if config.ORACLE_DSN:
            dsn = config.ORACLE_DSN
        else:
            dsn = oracledb.makedsn(config.ORACLE_HOST, config.ORACLE_PORT,
                                   service_name=config.ORACLE_SERVICE)
        _pool = oracledb.create_pool(user=config.ORACLE_USER,
                                     password=config.ORACLE_PASSWORD,
                                     dsn=dsn, min=1, max=5)
    return _pool


def executar(sql, params=None):
    """Executa SQL e devolve lista de dicts. Erro de conexão vira RuntimeError legível."""
    try:
        pool = _get_pool()
        with pool.acquire() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params or {})
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, row)) for row in cur.fetchall()]
    except RuntimeError:
        raise
    except Exception as e:  # DPY-xxxx, ORA-xxxx, timeout etc.
        raise RuntimeError(f"Falha ao consultar o Oracle ({type(e).__name__}): {e}") from e
