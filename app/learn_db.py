"""Postgres access for the learn sandbox — no Flask import."""

from __future__ import annotations

import os
import re

try:
    import psycopg2
    import psycopg2.extras
except ImportError:  # pragma: no cover - tests mock SQL, Desktop-Python hat psycopg2
    psycopg2 = None
    extras = None
else:
    extras = psycopg2.extras

from sql_coach import friendly_sql_error, has_empty_select_list, strip_sql_line_comments

MAX_ROWS = 200
SAFE_IDENT = re.compile(r"^[a-zA-Z0-9_]+$")
ALLOWED_SCHEMAS = ("learn", "practice")
PRACTICE_SCHEMA = "practice"
SEARCH_PATH = "practice, learn, public"
MAINTENANCE_DB = os.environ.get("DB_MAINTENANCE_NAME", "postgres")
DATASET_MAX_TABLES = 8
DATASET_MAX_COLUMNS = 24
DATASET_MAX_ROWS = 80
RESERVED_TABLE_NAMES = frozenset({"learn", "practice", "public", "pg_catalog", "information_schema"})
DATASET_PG_TYPES = {
    "integer": "integer",
    "int": "integer",
    "int4": "integer",
    "bigint": "bigint",
    "int8": "bigint",
    "smallint": "integer",
    "numeric": "numeric",
    "decimal": "numeric",
    "real": "numeric",
    "double precision": "numeric",
    "float": "numeric",
    "text": "text",
    "varchar": "text",
    "character varying": "text",
    "character": "text",
    "char": "text",
    "boolean": "boolean",
    "bool": "boolean",
    "date": "date",
    "timestamp": "timestamp",
    "timestamptz": "timestamp",
    "timestamp without time zone": "timestamp",
    "timestamp with time zone": "timestamp",
    "json": "text",
    "jsonb": "text",
}

TABLE_LABELS = {
    "orders": "Aufträge",
    "clients": "Kunden",
    "stock": "Bestand",
    "order_items": "Positionen",
}

CORE_SANDBOX = [
    {
        "name": "clients",
        "label": "Kunden",
        "columns": ["id", "name", "country"],
        "approx_rows": 4,
    },
    {
        "name": "orders",
        "label": "Aufträge",
        "columns": [
            "id", "order_number", "client_id", "client",
            "status", "quantity", "note", "created_at",
        ],
        "approx_rows": 24,
    },
    {
        "name": "stock",
        "label": "Bestand",
        "columns": ["id", "item", "quantity", "weight"],
        "approx_rows": 7,
    },
    {
        "name": "order_items",
        "label": "Positionen",
        "columns": ["id", "order_id", "sku", "qty"],
        "approx_rows": 28,
    },
]

FORBIDDEN_KEYWORDS = re.compile(
    r"\b(drop|alter|truncate|grant|revoke|create|copy|vacuum|comment|"
    r"reindex|cluster|lock|load|discard|reassign|security)\b",
    re.IGNORECASE,
)
WRITE_KEYWORDS = re.compile(r"\b(insert|update|delete)\b", re.IGNORECASE)
QUERY_HEADS = {"select", "with", "explain"}
WRITE_HEADS = {"insert", "update", "delete"}
BEGIN_HEADS = {"begin", "start"}
COMMIT_HEADS = {"commit"}
ROLLBACK_HEADS = {"rollback", "abort"}

_DATASET_LABELS: dict[str, str] = {}


def db_config() -> dict:
    """Read connection settings at call time so MCP env wins over import order."""
    return dict(
        host=os.environ.get("DB_HOST") or "127.0.0.1",
        port=os.environ.get("DB_PORT") or "5432",
        dbname=os.environ.get("DB_NAME") or "learnsql",
        user=os.environ.get("DB_USER") or "lernuser",
        password=os.environ.get("DB_PASSWORD") or "lernuser",
        connect_timeout=int(os.environ.get("DB_CONNECT_TIMEOUT") or "5"),
        options="-c statement_timeout=8s",
    )


def admin_config() -> dict:
    cfg = db_config()
    cfg["user"] = os.environ.get("DB_ADMIN_USER", "postgres")
    cfg["password"] = os.environ.get("DB_ADMIN_PASSWORD", "postgres")
    return cfg


# Snapshot for callers that still read the module dict (tests, restore messages).
DB_CONFIG = db_config()
ADMIN_CONFIG = admin_config()


def is_missing_database_error(exc, dbname) -> bool:
    """True, wenn Postgres erreichbar ist, die Zieldatenbank aber fehlt."""
    msg = str(exc).lower()
    name = str(dbname).lower()
    if name not in msg:
        return False
    return (
        "does not exist" in msg
        or "existiert nicht" in msg
        or "n'existe pas" in msg
    )


def _format_restore_error(err) -> str:
    text = str(err or "")
    name = db_config()["dbname"]
    if is_missing_database_error(text, name):
        return (
            "Die Übungsdatenbank learnsql fehlt im Postgres-Container. "
            "Im Projektordner ausführen: "
            'docker compose exec db psql -U postgres -c "CREATE DATABASE learnsql;" '
            "Danach in der App erneut prüfen. "
            "Alternativ mit frischem Volume: docker compose down -v && docker compose up --build. "
            f"({text})"
        )
    return text


def _require_psycopg2():
    if psycopg2 is None:
        raise RuntimeError(
            "psycopg2 ist nicht installiert. "
            "Im Windows-Paket liegt es neben python.exe, lokal: pip install psycopg2-binary."
        )
    return psycopg2, extras


def _admin_connect(dbname):
    pg, _extras = _require_psycopg2()
    cfg = dict(admin_config(), dbname=dbname)
    conn = pg.connect(**cfg)
    conn.autocommit = True
    return conn


def ensure_app_database():
    """Legt die Übungsdatenbank an, wenn der Server läuft, die DB aber fehlt."""
    target = str(db_config()["dbname"])
    if not SAFE_IDENT.match(target):
        return False, f"Ungültiger Datenbankname: {target}"
    try:
        conn = _admin_connect(target)
        conn.close()
        return True, None
    except Exception as exc:  # noqa: BLE001
        if not is_missing_database_error(exc, target):
            return False, str(exc)
    try:
        conn = _admin_connect(os.environ.get("DB_MAINTENANCE_NAME", "postgres"))
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target,))
                if cur.fetchone() is None:
                    cur.execute(f'CREATE DATABASE "{target}"')
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        msg = str(exc)
        if "already exists" in msg.lower() or "existiert bereits" in msg.lower():
            return True, None
        return False, msg
    return True, None


def get_connection(admin=False):
    pg, _extras = _require_psycopg2()
    cfg = dict(admin_config() if admin else db_config())
    try:
        conn = pg.connect(**cfg)
    except Exception as exc:  # noqa: BLE001
        if not is_missing_database_error(exc, cfg["dbname"]):
            raise
        ok, err = ensure_app_database()
        if not ok:
            raise ConnectionError(err or str(exc)) from exc
        conn = pg.connect(**cfg)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(f"SET search_path TO {SEARCH_PATH}")
    return conn


def core_table_names() -> set[str]:
    return {t["name"] for t in CORE_SANDBOX}


def table_label(name: str) -> str:
    key = str(name or "")
    return _DATASET_LABELS.get(key) or TABLE_LABELS.get(key, key)


def split_statements(sql: str):
    """Teilt ein Skript an Semikolons, lässt Strings und --Kommentare in Ruhe."""
    statements = []
    buf = []
    i = 0
    in_single = False
    n = len(sql)
    while i < n:
        ch = sql[i]
        nxt = sql[i + 1] if i + 1 < n else ""
        if not in_single and ch == "-" and nxt == "-":
            while i < n and sql[i] != "\n":
                buf.append(sql[i])
                i += 1
            continue
        if ch == "'" and not in_single:
            in_single = True
            buf.append(ch)
            i += 1
            continue
        if ch == "'" and in_single:
            if nxt == "'":
                buf.append("''")
                i += 2
                continue
            in_single = False
            buf.append(ch)
            i += 1
            continue
        if ch == ";" and not in_single:
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def first_keyword(stmt: str):
    text = stmt.strip()
    while text.startswith("--"):
        text = text.split("\n", 1)[-1].strip() if "\n" in text else ""
    match = re.match(r"([a-zA-Z]+)", text)
    return match.group(1).lower() if match else None


def classify_statement(stmt: str):
    head = first_keyword(stmt)
    if not head:
        return "empty"
    if head in QUERY_HEADS and not (head == "with" and WRITE_KEYWORDS.search(stmt)):
        return "query"
    if head in WRITE_HEADS or (head == "with" and WRITE_KEYWORDS.search(stmt)):
        return "write"
    if head in BEGIN_HEADS:
        return "begin"
    if head in COMMIT_HEADS:
        return "commit"
    if head in ROLLBACK_HEADS:
        return "rollback"
    return "unknown"


def jsonable_value(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def jsonable_rows(columns, rows):
    out = []
    for row in rows or []:
        item = {}
        if columns:
            for col in columns:
                try:
                    item[str(col)] = jsonable_value(row[col])
                except Exception:  # noqa: BLE001
                    item[str(col)] = jsonable_value(row.get(col) if hasattr(row, "get") else None)
        elif isinstance(row, dict):
            for key, value in row.items():
                if isinstance(key, str):
                    item[key] = jsonable_value(value)
        if item:
            out.append(item)
    return out


def describe_target() -> str:
    cfg = db_config()
    return f"{cfg['host']}:{cfg['port']}/{cfg['dbname']}"


def run_sql(sql: str, allow_write: bool = False, as_ids: str | None = None):
    """Führt SQL gegen learn und practice aus. DDL bleibt gesperrt."""
    raw = (sql or "").strip()
    if not raw:
        return {"ok": False, "error": "Bitte gib eine SQL-Abfrage ein.", "columns": None, "rows": None, "pg_error": None}

    if FORBIDDEN_KEYWORDS.search(strip_sql_line_comments(raw)):
        return {
            "ok": False,
            "error": "Im Übungsbereich darfst du das Datenbank-Schema nicht ändern (kein DROP/ALTER/CREATE).",
            "columns": None,
            "rows": None,
            "pg_error": None,
        }

    statements = split_statements(raw)
    if not statements:
        return {"ok": False, "error": "Bitte gib eine SQL-Abfrage ein.", "columns": None, "rows": None, "pg_error": None}

    incomplete = next((s for s in statements if has_empty_select_list(s)), None)
    if incomplete:
        return {
            "ok": False,
            "error": "Nach SELECT fehlt noch, **was** du sehen möchtest — zum Beispiel `*` oder Spaltennamen.",
            "columns": None,
            "rows": None,
            "empty_select": True,
            "pg_error": None,
        }

    columns, rows, note = [], [], None
    messages = []
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                for stmt in statements:
                    kind = classify_statement(stmt)
                    if kind == "empty":
                        continue
                    if not allow_write and kind in {"write", "begin", "commit", "rollback"}:
                        return {
                            "ok": False,
                            "error": (
                                "Hier sind nur lesende Abfragen erlaubt: `SELECT`, `WITH` und `EXPLAIN`. "
                                "Schreiben übst du in den späteren Kapiteln."
                            ),
                            "columns": None,
                            "rows": None,
                            "pg_error": None,
                        }
                    if kind == "unknown":
                        allowed = (
                            "Erlaubt sind SELECT, EXPLAIN, INSERT, UPDATE, DELETE und BEGIN/COMMIT/ROLLBACK."
                            if allow_write
                            else "Erlaubt sind SELECT, WITH und EXPLAIN."
                        )
                        return {
                            "ok": False,
                            "error": "Dieser Befehl ist hier nicht erlaubt. " + allowed,
                            "columns": None,
                            "rows": None,
                            "pg_error": None,
                        }
                    if kind == "query":
                        cur.execute(stmt)
                        if not cur.description:
                            messages.append("Ausgeführt.")
                            continue
                        fetched = cur.fetchmany(MAX_ROWS + 1)
                        truncated = len(fetched) > MAX_ROWS
                        fetched = fetched[:MAX_ROWS]
                        columns = [d.name for d in cur.description]
                        rows = jsonable_rows(columns, fetched)
                        note = f"(Ergebnis auf {MAX_ROWS} Zeilen begrenzt.)" if truncated else None
                    else:
                        cur.execute(stmt)
                        if kind == "write":
                            messages.append(f"{cur.rowcount} Zeile(n) geändert.")
                        elif kind == "begin":
                            messages.append("Transaktion gestartet (BEGIN).")
                        elif kind == "commit":
                            messages.append("Änderung übernommen (COMMIT).")
                        elif kind == "rollback":
                            messages.append("Änderung verworfen (ROLLBACK).")
    except Exception as e:  # noqa: BLE001
        pg_error = str(e)
        return {
            "ok": False,
            "error": friendly_sql_error(pg_error, raw, tables=_coach_table_names()),
            "pg_error": pg_error,
            "columns": None,
            "rows": None,
            "target": describe_target(),
        }

    result = {
        "ok": True,
        "columns": columns,
        "rows": rows,
        "note": note,
        "messages": messages,
        "error": None,
        "pg_error": None,
    }
    if as_ids:
        field = str(as_ids).strip()
        if not SAFE_IDENT.match(field):
            return {
                "ok": False,
                "error": "as_ids muss ein Spaltenname sein (Buchstaben, Zahlen, Unterstrich).",
                "columns": None,
                "rows": None,
                "pg_error": None,
            }
        ids = []
        for row in rows or []:
            if field not in row:
                return {
                    "ok": False,
                    "error": f"Spalte {field} fehlt im Ergebnis. Vorhanden: {', '.join(columns)}.",
                    "columns": columns,
                    "rows": rows,
                    "pg_error": None,
                }
            ids.append(row[field])
        result["ids"] = ids
        result["id_field"] = field
        result["rows"] = None
        result["columns"] = [field]
    return result


def _coach_table_names() -> list[str]:
    try:
        names = list_table_names()
    except Exception:  # noqa: BLE001
        names = []
    return names or [t["name"] for t in CORE_SANDBOX]


def fetch_schema():
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT c.table_schema, c.table_name, c.column_name, c.data_type,
                           c.ordinal_position
                    FROM information_schema.columns c
                    WHERE c.table_schema IN ('learn', 'practice')
                    ORDER BY CASE c.table_schema WHEN 'practice' THEN 0 ELSE 1 END,
                             c.table_name, c.ordinal_position
                    """
                )
                rows = cur.fetchall()
                counts = {}
                seen = set()
                for row in rows:
                    schema = row["table_schema"]
                    name = row["table_name"]
                    if not SAFE_IDENT.match(schema) or not SAFE_IDENT.match(name):
                        continue
                    key = (schema, name)
                    if key in seen:
                        continue
                    seen.add(key)
                    cur.execute(f"SELECT COUNT(*) AS n FROM {schema}.{name}")
                    counts[key] = int(cur.fetchone()["n"])
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e), "target": describe_target(), "tables": []}

    tables = {}
    for row in rows:
        name = row["table_name"]
        schema = row["table_schema"]
        if name in tables:
            if tables[name]["schema"] != schema:
                continue
            tables[name]["columns"].append({
                "name": row["column_name"],
                "type": row["data_type"],
            })
            continue
        tables[name] = {
            "schema": schema,
            "name": name,
            "short": name,
            "qualified": f"{schema}.{name}",
            "sandbox": schema,
            "label": table_label(name),
            "parent": "",
            "kind": "Übung" if schema == PRACTICE_SCHEMA else "Training",
            "row_count": counts.get((schema, name)),
            "columns": [{
                "name": row["column_name"],
                "type": row["data_type"],
            }],
        }
    return {"ok": True, "tables": list(tables.values())}


def list_table_names() -> list[str]:
    result = fetch_schema()
    if not result.get("ok"):
        return [t["name"] for t in CORE_SANDBOX]
    return [t["name"] for t in result.get("tables") or []]


def table_block(table: str, columns=None, where: str | None = None):
    """Return a step `table` object: {name, label, columns, rows}."""
    name = str(table or "").strip()
    if not SAFE_IDENT.match(name):
        return {"ok": False, "error": "Ungültiger Tabellenname."}
    col_sql = "*"
    col_list = None
    if columns:
        if isinstance(columns, str):
            columns = [c.strip() for c in columns.split(",") if c.strip()]
        col_list = []
        for col in columns:
            if not SAFE_IDENT.match(str(col)):
                return {"ok": False, "error": f"Ungültiger Spaltenname: {col}"}
            col_list.append(str(col))
        col_sql = ", ".join(col_list)
    sql = f"SELECT {col_sql} FROM {name}"
    clause = (where or "").strip()
    if clause:
        if ";" in clause or FORBIDDEN_KEYWORDS.search(clause):
            return {"ok": False, "error": "where darf kein zweites Statement und kein DDL enthalten."}
        sql += f" WHERE {clause}"
    result = run_sql(sql, allow_write=False)
    if not result.get("ok"):
        return result
    cols = col_list or list(result.get("columns") or [])
    return {
        "ok": True,
        "name": name,
        "label": table_label(name),
        "columns": cols,
        "rows": result.get("rows") or [],
    }


def _pg_type(raw) -> str:
    text = str(raw or "text").strip().lower()
    text = re.sub(r"\s*\(.*\)$", "", text).strip()
    return DATASET_PG_TYPES.get(text, "text")


def _normalize_column(col, index: int, errors: list, prefix: str) -> dict | None:
    if isinstance(col, str):
        name = col.strip()
        pg_type = "text"
    elif isinstance(col, dict):
        name = str(col.get("name") or "").strip()
        pg_type = _pg_type(col.get("type"))
    else:
        errors.append(f"{prefix}.columns[{index}]: Spalte muss Name oder Objekt sein.")
        return None
    if not SAFE_IDENT.match(name):
        errors.append(f"{prefix}.columns[{index}]: ungültiger Spaltenname {name!r}.")
        return None
    return {"name": name, "type": pg_type}


def _normalize_row(row, columns: list, index: int, errors: list, prefix: str) -> dict | None:
    names = [c["name"] for c in columns]
    if isinstance(row, dict):
        out = {name: row.get(name) for name in names}
        return out
    if isinstance(row, (list, tuple)):
        if len(row) > len(names):
            errors.append(
                f"{prefix}.rows[{index}]: {len(row)} Werte, aber nur {len(names)} Spalten."
            )
            return None
        out = {name: (row[i] if i < len(row) else None) for i, name in enumerate(names)}
        return out
    errors.append(f"{prefix}.rows[{index}]: Zeile muss Objekt oder Liste sein.")
    return None


def normalize_dataset(raw) -> tuple[dict | None, list[str]]:
    """Validate and freeze a lesson dataset. Returns (payload, errors)."""
    errors: list[str] = []
    if raw in (None, "", {}, []):
        return {"tables": []}, []
    if isinstance(raw, list):
        tables_in = raw
    elif isinstance(raw, dict):
        tables_in = raw.get("tables")
        if tables_in is None:
            errors.append("dataset.tables fehlt.")
            return None, errors
    else:
        errors.append("dataset muss ein Objekt mit tables sein.")
        return None, errors
    if not isinstance(tables_in, list):
        errors.append("dataset.tables muss eine Liste sein.")
        return None, errors
    if len(tables_in) > DATASET_MAX_TABLES:
        errors.append(
            f"dataset: höchstens {DATASET_MAX_TABLES} Tabellen (Lehrdaten, kein Dump)."
        )
        return None, errors

    reserved = core_table_names() | RESERVED_TABLE_NAMES
    seen_names = set()
    tables = []
    for ti, item in enumerate(tables_in):
        prefix = f"dataset.tables[{ti}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix}: muss ein Objekt sein.")
            continue
        name = str(item.get("name") or "").strip()
        if not SAFE_IDENT.match(name):
            errors.append(f"{prefix}: ungültiger Tabellenname {name!r}.")
            continue
        low = name.lower()
        if low in reserved or name in reserved:
            errors.append(
                f"{prefix}: `{name}` ist eine Kern- oder Systemtabelle und darf nicht überschrieben werden."
            )
            continue
        if low in seen_names:
            errors.append(f"{prefix}: Tabellenname {name} ist doppelt.")
            continue
        seen_names.add(low)
        raw_cols = item.get("columns")
        if not raw_cols:
            errors.append(f"{prefix}: columns fehlen.")
            continue
        if isinstance(raw_cols, str):
            raw_cols = [c.strip() for c in raw_cols.split(",") if c.strip()]
        if not isinstance(raw_cols, list):
            errors.append(f"{prefix}: columns muss eine Liste sein.")
            continue
        if len(raw_cols) > DATASET_MAX_COLUMNS:
            errors.append(f"{prefix}: höchstens {DATASET_MAX_COLUMNS} Spalten.")
            continue
        columns = []
        col_seen = set()
        for ci, col in enumerate(raw_cols):
            parsed = _normalize_column(col, ci, errors, prefix)
            if not parsed:
                continue
            if parsed["name"] in col_seen:
                errors.append(f"{prefix}: Spalte {parsed['name']} ist doppelt.")
                continue
            col_seen.add(parsed["name"])
            columns.append(parsed)
        if not columns:
            errors.append(f"{prefix}: keine gültigen Spalten.")
            continue
        raw_rows = item.get("rows") or []
        if not isinstance(raw_rows, list):
            errors.append(f"{prefix}: rows muss eine Liste sein.")
            continue
        if len(raw_rows) > DATASET_MAX_ROWS:
            errors.append(f"{prefix}: höchstens {DATASET_MAX_ROWS} Zeilen.")
            continue
        rows = []
        for ri, row in enumerate(raw_rows):
            parsed_row = _normalize_row(row, columns, ri, errors, prefix)
            if parsed_row is not None:
                rows.append(parsed_row)
        label = str(item.get("label") or "").strip() or name
        tables.append({
            "name": name,
            "label": label,
            "columns": columns,
            "rows": rows,
        })

    if errors:
        return None, errors
    return {"tables": tables}, []


def _create_practice_table(cur, table: dict):
    name = table["name"]
    cols = table["columns"]
    parts = []
    has_pk = False
    for col in cols:
        piece = f"{col['name']} {col['type']}"
        if not has_pk and col["name"] == "id" and col["type"] in {"integer", "bigint"}:
            piece += " PRIMARY KEY"
            has_pk = True
        parts.append(piece)
    cur.execute(f"CREATE TABLE {PRACTICE_SCHEMA}.{name} ({', '.join(parts)})")
    if not table["rows"]:
        return
    col_names = [c["name"] for c in cols]
    placeholders = ", ".join(["%s"] * len(col_names))
    sql = (
        f"INSERT INTO {PRACTICE_SCHEMA}.{name} ({', '.join(col_names)}) "
        f"VALUES ({placeholders})"
    )
    for row in table["rows"]:
        cur.execute(sql, tuple(row.get(c) for c in col_names))


def _grant_practice(cur):
    cur.execute(f"GRANT USAGE ON SCHEMA {PRACTICE_SCHEMA} TO lernuser")
    cur.execute(
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {PRACTICE_SCHEMA} TO lernuser"
    )
    cur.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {PRACTICE_SCHEMA} "
        "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO lernuser"
    )


def clear_dataset() -> dict:
    """Leert Schema practice. Kern-Tabellen in learn bleiben."""
    _DATASET_LABELS.clear()
    try:
        with get_connection(admin=True) as conn:
            with conn.cursor() as cur:
                cur.execute(f"DROP SCHEMA IF EXISTS {PRACTICE_SCHEMA} CASCADE")
                cur.execute(f"CREATE SCHEMA {PRACTICE_SCHEMA}")
                _grant_practice(cur)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "target": describe_target()}
    return {"ok": True, "tables": [], "schema": PRACTICE_SCHEMA}


def apply_dataset(dataset) -> dict:
    """Materialisiert Lehr-Tabellen in Schema practice."""
    if dataset in (None, "", {}, []):
        return clear_dataset()
    normalized, errors = normalize_dataset(dataset)
    if errors:
        return {"ok": False, "error": errors[0], "errors": errors}
    tables = (normalized or {}).get("tables") or []
    if not tables:
        return clear_dataset()
    _DATASET_LABELS.clear()
    _DATASET_LABELS.update({t["name"]: t["label"] for t in tables})
    try:
        with get_connection(admin=True) as conn:
            with conn.cursor() as cur:
                cur.execute(f"DROP SCHEMA IF EXISTS {PRACTICE_SCHEMA} CASCADE")
                cur.execute(f"CREATE SCHEMA {PRACTICE_SCHEMA}")
                _grant_practice(cur)
                for table in tables:
                    _create_practice_table(cur, table)
                _grant_practice(cur)
    except Exception as exc:  # noqa: BLE001
        _DATASET_LABELS.clear()
        return {"ok": False, "error": str(exc), "target": describe_target()}
    return {
        "ok": True,
        "tables": [t["name"] for t in tables],
        "schema": PRACTICE_SCHEMA,
        "dataset": normalized,
    }


def ensure_lesson_sandbox(lesson) -> dict:
    """Overlay der Übungs-Tabellen — ohne Dataset wird practice geleert."""
    try:
        dataset = (lesson or {}).get("dataset") if isinstance(lesson, dict) else None
        if dataset:
            return apply_dataset(dataset)
        return clear_dataset()
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}
