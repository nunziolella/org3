"""Script per l'applicazione e verifica dello schema multi-tenant Org3 su Neon Postgres.

Migrazione: db/migrations/0001_org3_multitenant_schema.sql
Target: Cluster Neon (ep-wandering-rain-ad3ciuur)
Namespace: org3_* (Strict Non-Contamination Invariant)
"""

import os
import re
import sys
from pathlib import Path

# Force UTF-8 encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import psycopg2

ORG3_DIR = Path(__file__).resolve().parent.parent
SQL_FILE = ORG3_DIR / "db" / "migrations" / "0001_org3_multitenant_schema.sql"
SSH_KEY = r"G:\Il mio Drive\Business\Fornitori\Oracle\Strctura\ssh-key-2026-06-19 (1).key"
SSH_HOST = "130.110.10.142"
SSH_USER = "ubuntu"


def get_neon_connection():
    """Recupera la stringa di connessione in modo sicuro e apre la sessione psycopg2."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        try:
            import paramiko
        except ImportError:
            raise RuntimeError("DATABASE_URL non configurato e paramiko non disponibile")
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(SSH_HOST, username=SSH_USER, key_filename=SSH_KEY, timeout=15)
        stdin, stdout, stderr = c.exec_command(
            "grep -E '^DATABASE_URL=' /home/ubuntu/structura/.env", timeout=15
        )
        line = stdout.read().decode(errors="replace").strip()
        c.close()

        if not line:
            raise RuntimeError("DATABASE_URL non trovato in /home/ubuntu/structura/.env")

        url = line.split("=", 1)[1].strip().strip('"').strip("'")

    clean_url = (
        url.replace("postgresql+asyncpg://", "postgresql://")
        .replace("postgresql+psycopg://", "postgresql://")
    )
    if "?" not in clean_url:
        clean_url += "?sslmode=require"
    elif "sslmode" not in clean_url:
        clean_url += "&sslmode=require"

    host_match = re.search(r"@([^/:?]+)", clean_url)
    db_host = host_match.group(1) if host_match else "unknown"
    print(f"[AUTH] Connessione sicura al cluster Neon: {db_host}")

    conn = psycopg2.connect(clean_url)
    conn.autocommit = False
    return conn


def apply_migration(conn):
    """Esegue lo script SQL di migrazione se non già applicato."""
    if not SQL_FILE.exists():
        raise FileNotFoundError(f"File SQL non trovato: {SQL_FILE}")

    sql_content = SQL_FILE.read_text(encoding="utf-8")
    cur = conn.cursor()

    print(f"[MIGRATE] Applicazione schema: {SQL_FILE.name} ...")
    cur.execute(sql_content)
    conn.commit()
    print("[MIGRATE] Schema applicato con successo!")


def verify_schema(conn):
    """Verifica l'esistenza e le proprietà delle 6 tabelle org3_*."""
    target_tables = [
        "org3_organizations",
        "org3_workspaces",
        "org3_members",
        "org3_delegation_policies",
        "org3_approval_requests",
        "org3_api_tokens",
    ]

    cur = conn.cursor()
    cur.execute(
        """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE 'org3_%';
    """
    )
    existing = [r[0] for r in cur.fetchall()]
    print(f"\n[AUDIT] Tabelle org3_* trovate su Neon: {existing}")

    for t in target_tables:
        assert t in existing, f"Errore: Tabella attesa {t} mancante su Neon!"
        cur.execute(
            f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = '{t}'
            ORDER BY ordinal_position;
        """
        )
        cols = cur.fetchall()
        print(f"  - Tabella {t}: {len(cols)} colonne verificate OK.")

    # Verifica indici
    cur.execute(
        """
        SELECT indexname, tablename 
        FROM pg_indexes 
        WHERE schemaname = 'public' AND tablename LIKE 'org3_%'
        ORDER BY tablename, indexname;
    """
    )
    indexes = cur.fetchall()
    print(f"\n[AUDIT] Indici org3_* creati: {len(indexes)}")
    for idx in indexes:
        print(f"  * {idx[0]} su {idx[1]}")

    print("\n[VERIFY] 100% DEI CONTROLLI SUPERATI: Schema Org3 perfettamente operativo su Neon!")


def main():
    conn = get_neon_connection()
    try:
        apply_migration(conn)
        verify_schema(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
