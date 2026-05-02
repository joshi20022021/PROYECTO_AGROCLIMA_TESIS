"""
Conexion a PostgreSQL para AgroClima GT.
Usa psycopg2 con pool de conexiones.

Variables de entorno (con defaults para desarrollo local):
    DB_HOST  → localhost
    DB_PORT  → 5432
    DB_NAME  → agroclima
    DB_USER  → agroclima
    DB_PASS  → agroclima2024
"""

import os
import contextlib
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", "5435")),
    "dbname":   os.getenv("DB_NAME", "agroclima"),
    "user":     os.getenv("DB_USER", "agroclima"),
    "password": os.getenv("DB_PASS", "agroclima2024"),
}

_pool: pool.ThreadedConnectionPool | None = None


def get_pool() -> pool.ThreadedConnectionPool:
    global _pool
    if _pool is None:
        _pool = pool.ThreadedConnectionPool(1, 10, **DB_CONFIG)
    return _pool


@contextlib.contextmanager
def get_cursor(dict_cursor: bool = True):
    """Context manager: obtiene conexion del pool, crea cursor y hace commit/rollback."""
    conn = get_pool().getconn()
    try:
        factory = RealDictCursor if dict_cursor else None
        with conn.cursor(cursor_factory=factory) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        get_pool().putconn(conn)


def db_available() -> bool:
    """Retorna True si la base de datos está accesible."""
    try:
        with get_cursor() as cur:
            cur.execute("SELECT 1")
        return True
    except Exception:
        return False
