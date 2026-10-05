"""Database connection manager for Org3 Platform API.

Connette in modo trasparente e sicuro al cluster Neon Postgres (ep-wandering-rain-ad3ciuur).
Supporta:
1. Variabile d'ambiente DATABASE_URL (se definita su Cloud Run / container).
2. Fallback sicuro tramite get_neon_connection() per esecuzione locale e test.
"""

from __future__ import annotations

import os
import re
from typing import Generator
import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection():
    """Restituisce una connessione psycopg2 a Neon Postgres con RealDictCursor."""
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        clean_url = (
            db_url.replace("postgresql+asyncpg://", "postgresql://")
            .replace("postgresql+psycopg://", "postgresql://")
        )
        if "?" not in clean_url:
            clean_url += "?sslmode=require"
        elif "sslmode" not in clean_url:
            clean_url += "&sslmode=require"
        conn = psycopg2.connect(clean_url, cursor_factory=RealDictCursor)
        conn.autocommit = True
        return conn

    # Fallback per ambiente di test/sviluppo locale
    from scripts.run_migration_0001_neon import get_neon_connection

    conn = get_neon_connection()
    conn.cursor_factory = RealDictCursor
    conn.autocommit = True
    return conn


def get_db() -> Generator[Any, None, None]:
    """Dependency FastAPI per ottenere una connessione dal pool."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
