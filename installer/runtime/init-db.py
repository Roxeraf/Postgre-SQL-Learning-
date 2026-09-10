"""Create learnsql and import the learning schema via psycopg2 (no psql required)."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import psycopg2


def connect(dbname: str, port: int, password: str):
    return psycopg2.connect(
        host="127.0.0.1",
        port=port,
        user="postgres",
        password=password,
        dbname=dbname,
    )


def wait_for_server(port: int, password: str):
    last = None
    for _ in range(50):
        try:
            conn = connect("postgres", port, password)
            conn.close()
            return
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(0.4)
    raise SystemExit(f"PostgreSQL auf Port {port} nicht erreichbar: {last}")


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: init-db.py <schema.sql>")
    sql_path = Path(sys.argv[1])
    port = int(os.environ.get("DB_PORT", "5432"))
    password = os.environ.get("PGPASSWORD", "postgres")
    dbname = os.environ.get("DB_NAME", "learnsql")

    wait_for_server(port, password)

    conn = connect("postgres", port, password)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        if cur.fetchone() is None:
            cur.execute(f'CREATE DATABASE "{dbname}"')
    conn.close()

    sql = sql_path.read_text(encoding="utf-8")
    conn = connect(dbname, port, password)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.close()
    print("ok")


if __name__ == "__main__":
    main()
