import os
import re
from collections import Counter
from pathlib import Path

import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, render_template, request

from lessons.academy_data import ACADEMY, lesson_by_id as academy_lesson_by_id
from lessons.knowledge import (
    ARTICLES,
    article_by_slug,
    knowledge_cards,
    related_articles,
    sections as knowledge_sections,
)
from sql_coach import (
    diagnose_structure,
    explain_sql as explain_sql_query,
    friendly_sql_error,
    has_empty_select_list,
    strip_sql_line_comments,
)

app = Flask(__name__)

TABLE_LABELS = {
    "orders": "Aufträge",
    "clients": "Kunden",
    "stock": "Bestand",
    "order_items": "Positionen",
}


def _plain(text: str) -> str:
    return re.sub(r"[#*_`>|]+", " ", text or "").lower()


def _snippet(text: str, query: str, width: int = 180) -> str:
    raw = re.sub(r"\s+", " ", (text or "").replace("#", " ")).strip()
    if not raw:
        return ""
    q = (query or "").lower()
    lower = raw.lower()
    idx = lower.find(q) if q else 0
    if idx < 0:
        idx = 0
    start = max(0, idx - 40)
    chunk = raw[start:start + width]
    if start > 0:
        chunk = "…" + chunk
    if start + width < len(raw):
        chunk = chunk + "…"
    return chunk


def _step_text(step: dict) -> str:
    parts = [
        step.get("title") or "",
        step.get("text") or "",
        step.get("prompt") or "",
        step.get("question") or "",
        step.get("plain") or "",
        step.get("note") or "",
        " ".join(step.get("hints") or []),
    ]
    return " ".join(parts)


FLASHCARDS = knowledge_cards()
for lesson in ACADEMY["lessons"]:
    for i, q in enumerate(lesson.get("quiz") or [], start=1):
        options = q.get("options") or []
        correct = options[q["correct"]] if options else ""
        FLASHCARDS.append({
            "id": f"{lesson['id']}-quiz-{i}",
            "front": q["q"],
            "back": correct + ((" — " + q["explain"]) if q.get("explain") else ""),
            "sql": "",
            "kind": "check",
            "lesson_id": lesson["id"],
            "lesson": lesson["title"],
            "topic": "",
            "topic_label": "Kurzcheck",
            "slug": "",
            "source": "quiz",
        })

SEARCH_INDEX = []
for lesson in ACADEMY["lessons"]:
    letter = str(lesson.get("chapter", ""))
    url = f"/learn/{lesson['id']}"
    SEARCH_INDEX.append({
        "type": "lektion",
        "lesson_id": lesson["id"],
        "letter": letter,
        "title": f"Kapitel {letter} — {lesson['title']}",
        "url": url,
        "text": _plain(" ".join([
            lesson["title"],
            lesson.get("goal") or "",
            " ".join(_step_text(s) for s in lesson.get("steps") or []),
        ])),
        "preview": lesson.get("goal") or "",
    })
    for step in lesson.get("steps") or []:
        SEARCH_INDEX.append({
            "type": "schritt",
            "lesson_id": lesson["id"],
            "letter": letter,
            "title": step.get("title") or lesson["title"],
            "url": url,
            "text": _plain(_step_text(step)),
            "preview": (step.get("text") or step.get("prompt") or "")[:280],
        })
    for q in lesson.get("quiz") or []:
        SEARCH_INDEX.append({
            "type": "check",
            "lesson_id": lesson["id"],
            "letter": letter,
            "title": q["q"],
            "url": url,
            "text": _plain(q["q"] + " " + " ".join(q.get("options") or []) + " " + (q.get("explain") or "")),
            "preview": q.get("explain") or "",
        })

for item in ACADEMY.get("glossary") or []:
    SEARCH_INDEX.append({
        "type": "konzept",
        "lesson_id": item.get("lesson_id") or "",
        "letter": "SQL",
        "title": item["label"],
        "url": f"/learn/{item['lesson_id']}" if item.get("lesson_id") else "/wissen",
        "text": _plain(item["label"] + " " + item.get("text") + " " + (item.get("sql") or "")),
        "preview": item.get("text") or "",
    })

for art in ARTICLES:
    SEARCH_INDEX.append({
        "type": "artikel",
        "lesson_id": art.get("lesson_id") or "",
        "letter": art.get("section_label") or "SQL",
        "title": art["title"],
        "url": f"/wissen/{art['slug']}",
        "text": _plain(" ".join([
            art["title"],
            art.get("summary") or "",
            art.get("body") or "",
            " ".join(art.get("sql") or []),
            " ".join(art.get("pitfalls") or []),
        ])),
        "preview": art.get("summary") or "",
    })

DB_CONFIG = dict(
    host=os.environ.get("DB_HOST", "db"),
    port=os.environ.get("DB_PORT", "5432"),
    dbname=os.environ.get("DB_NAME", "learnsql"),
    user=os.environ.get("DB_USER", "lernuser"),
    password=os.environ.get("DB_PASSWORD", "lernuser"),
    connect_timeout=5,
    options="-c statement_timeout=8s",
)

MAX_ROWS = 200
SAFE_IDENT = re.compile(r"^[a-zA-Z0-9_]+$")
ALLOWED_SCHEMAS = ("learn",)
ADMIN_CONFIG = dict(
    DB_CONFIG,
    user=os.environ.get("DB_ADMIN_USER", "postgres"),
    password=os.environ.get("DB_ADMIN_PASSWORD", "postgres"),
)
MAINTENANCE_DB = os.environ.get("DB_MAINTENANCE_NAME", "postgres")

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


def _init_sql_path():
    env = os.environ.get("SQL_INIT_PATH")
    here = Path(__file__).parent
    candidates = []
    if env:
        candidates.append(Path(env))
    candidates.extend([
        here / "db" / "01_schema_and_data.sql",
        here.parent / "db" / "init" / "01_schema_and_data.sql",
    ])
    for path in candidates:
        if path.is_file():
            return path
    return None


def _is_missing_database_error(exc, dbname):
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


def _format_restore_error(err):
    text = str(err or "")
    if _is_missing_database_error(text, DB_CONFIG["dbname"]):
        return (
            "Die Übungsdatenbank learnsql fehlt im Postgres-Container. "
            "Im Projektordner ausführen: "
            'docker compose exec db psql -U postgres -c "CREATE DATABASE learnsql;" '
            "Danach in der App erneut prüfen. "
            "Alternativ mit frischem Volume: docker compose down -v && docker compose up --build. "
            f"({text})"
        )
    return text


def _admin_connect(dbname):
    cfg = dict(ADMIN_CONFIG, dbname=dbname)
    conn = psycopg2.connect(**cfg)
    conn.autocommit = True
    return conn


def ensure_app_database():
    """Legt die Übungsdatenbank an, wenn der Server läuft, die DB aber fehlt."""
    target = str(DB_CONFIG["dbname"])
    if not SAFE_IDENT.match(target):
        return False, f"Ungültiger Datenbankname: {target}"
    try:
        conn = _admin_connect(target)
        conn.close()
        return True, None
    except Exception as exc:  # noqa: BLE001
        if not _is_missing_database_error(exc, target):
            return False, str(exc)
    try:
        conn = _admin_connect(MAINTENANCE_DB)
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
    cfg = dict(ADMIN_CONFIG if admin else DB_CONFIG)
    try:
        conn = psycopg2.connect(**cfg)
    except Exception as exc:  # noqa: BLE001
        if not _is_missing_database_error(exc, cfg["dbname"]):
            raise
        ok, err = ensure_app_database()
        if not ok:
            raise ConnectionError(err or str(exc)) from exc
        conn = psycopg2.connect(**cfg)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SET search_path TO learn, public")
    return conn


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


def run_sql(sql: str, allow_write: bool = False):
    """Führt SQL gegen Schema learn aus. DDL bleibt gesperrt."""
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
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                for stmt in statements:
                    kind = classify_statement(stmt)
                    if kind == "empty":
                        continue
                    if not allow_write and kind in {"write", "begin", "commit", "rollback"}:
                        return {
                            "ok": False,
                            "error": (
                                "Hier sind nur lesende Abfragen erlaubt: `SELECT`, `WITH` und `EXPLAIN`. "
                                "Schreiben übst du in den späteren Kapiteln — oder im Playground."
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
            "error": friendly_sql_error(pg_error, raw),
            "pg_error": pg_error,
            "columns": None,
            "rows": None,
        }

    return {
        "ok": True,
        "columns": columns,
        "rows": rows,
        "note": note,
        "messages": messages,
        "error": None,
        "pg_error": None,
    }


def restore_learn_schema():
    sql_path = _init_sql_path()
    if not sql_path:
        return False, "Init-SQL nicht gefunden. Bitte die App neu installieren bzw. den Container mit db/init starten."
    ok, err = ensure_app_database()
    if not ok:
        return False, _format_restore_error(err)
    script = sql_path.read_text(encoding="utf-8")
    try:
        with get_connection(admin=True) as conn:
            with conn.cursor() as cur:
                cur.execute(script)
    except Exception as e:  # noqa: BLE001
        return False, _format_restore_error(e)
    return True, "Lern-Datenbank ist wieder im Ausgangszustand."


def _restore_error():
    ok, message = restore_learn_schema()
    if ok:
        return None
    return {
        "ok": False,
        "error": "Die Übungsdatenbank konnte nicht zurückgesetzt werden: " + (message or ""),
    }


def reset_learning_db():
    return restore_learn_schema()


def ensure_learn_schema():
    try:
        ok, _err = ensure_app_database()
        if not ok:
            return
        with get_connection(admin=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'learn' AND table_name = 'order_items'
                    """
                )
                if cur.fetchone():
                    cur.execute(
                        """
                        GRANT USAGE ON SCHEMA learn TO lernuser;
                        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA learn TO lernuser;
                        """
                    )
                    return
        restore_learn_schema()
    except Exception:  # noqa: BLE001
        try:
            restore_learn_schema()
        except Exception:
            pass


def _cell_str(value):
    return "" if value is None else str(value)


def row_value_counter(row):
    return Counter(_cell_str(v) for v in (row or {}).values())


def row_covers(user_row, sol_row):
    user_c = row_value_counter(user_row)
    sol_c = row_value_counter(sol_row)
    return all(user_c[k] >= n for k, n in sol_c.items())


def unique_rows(rows):
    seen = set()
    out = []
    for row in rows or []:
        key = tuple(sorted(_cell_str(v) for v in row.values()))
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def compare_by_values(user_rows, sol_rows):
    users = unique_rows(user_rows)
    sols = unique_rows(sol_rows)
    if not sols and not users:
        return True, 0, 0
    if any(not any(row_covers(u, s) for s in sols) for u in users):
        return False, len(users), len(sols)
    if any(not any(row_covers(u, s) for u in users) for s in sols):
        return False, len(users), len(sols)
    return True, len(users), len(sols)


def project_rows(rows, wanted_cols, col_map):
    keys = []
    for row in rows or []:
        keys.append(tuple(str(row.get(col_map[c])) for c in wanted_cols))
    return sorted(set(keys))


def project_row_seq(rows, wanted_cols, col_map):
    seq = []
    for row in rows or []:
        seq.append(tuple(_cell_str(row.get(col_map[c])) for c in wanted_cols))
    return seq


def compare_query_result(user_cols, user_rows, sol_cols, sol_rows, ordered=False, strict_columns=False):
    user_map = {c.lower(): c for c in (user_cols or [])}
    sol_map = {c.lower(): c for c in (sol_cols or [])}
    sol_names = [c.lower() for c in (sol_cols or [])]
    missing = [c for c in sol_names if c not in user_map]
    extra = sorted(set(user_map) - set(sol_names))
    if strict_columns and extra:
        return False, missing, extra, len(user_rows or []), len(sol_rows or [])
    if ordered:
        if missing:
            return False, missing, extra, len(user_rows or []), len(sol_rows or [])
        user_seq = project_row_seq(user_rows, sol_names, user_map)
        sol_seq = project_row_seq(sol_rows, sol_names, sol_map)
        return user_seq == sol_seq, missing, extra, len(user_seq), len(sol_seq)
    sol_keys = project_rows(sol_rows, sol_names, sol_map) if sol_names else []
    if not missing:
        user_keys = project_rows(user_rows, sol_names, user_map)
        if user_keys == sol_keys:
            return True, missing, extra, len(user_keys), len(sol_keys)
    ok, user_n, sol_n = compare_by_values(user_rows, sol_rows)
    if ok and not (strict_columns and extra):
        return True, [], extra, user_n, sol_n
    return False, missing, extra, user_n, sol_n


def academy_nav(lesson_id):
    ids = [l["id"] for l in ACADEMY["lessons"]]
    if lesson_id not in ids:
        return None, None
    idx = ids.index(lesson_id)
    return (
        ids[idx - 1] if idx > 0 else None,
        ids[idx + 1] if idx < len(ids) - 1 else None,
    )


@app.context_processor
def inject_nav():
    return {
        "academy": ACADEMY,
        "academy_lessons": ACADEMY["lessons"],
    }


@app.route("/")
def index():
    return render_template(
        "index.html",
        academy_lessons=ACADEMY["lessons"],
        academy_concepts=ACADEMY["concepts"],
        academy_step_count=sum(len(l.get("steps") or []) for l in ACADEMY["lessons"]),
    )


@app.route("/learn/<lesson_id>")
def academy_lesson(lesson_id):
    lesson_obj = academy_lesson_by_id(lesson_id)
    if not lesson_obj:
        return "Lektion nicht gefunden", 404
    prev_id, next_id = academy_nav(lesson_id)
    return render_template(
        "academy.html",
        lesson=lesson_obj,
        prev_id=prev_id,
        next_id=next_id,
        current_academy_id=lesson_id,
    )


@app.route("/playground")
def playground():
    return render_template("playground.html", active_tool="playground")


@app.route("/cards")
def cards():
    return render_template(
        "cards.html",
        active_tool="cards",
        card_count=len(FLASHCARDS),
        academy_lessons=ACADEMY["lessons"],
        card_topics=knowledge_sections(),
    )


@app.route("/wissen")
def wissen():
    return render_template(
        "wissen.html",
        active_tool="wissen",
        index_count=len(ARTICLES),
        sections=knowledge_sections(),
        glossary=ACADEMY.get("glossary") or [],
    )


@app.route("/wissen/<slug>")
def wissen_article(slug):
    art = article_by_slug(slug)
    if not art:
        return "Artikel nicht gefunden", 404
    return render_template(
        "wissen_article.html",
        active_tool="wissen",
        article=art,
        related=related_articles(art),
    )


@app.route("/api/run", methods=["POST"])
def api_run():
    data = request.get_json(force=True) or {}
    allow_write = bool(data.get("allow_write"))
    result = run_sql(data.get("sql", ""), allow_write=allow_write)
    if not result["ok"]:
        return jsonify({
            "ok": False,
            "error": result["error"],
            "pg_error": result.get("pg_error"),
            "empty_select": bool(result.get("empty_select")),
        })
    return jsonify({
        "ok": True,
        "columns": result["columns"],
        "rows": result["rows"],
        "note": result.get("note"),
        "messages": result.get("messages") or [],
    })


def sql_requirement_coach(sql: str, exercise: dict):
    blob = strip_sql_line_comments(sql or "")
    low = blob.lower()
    for needle in exercise.get("require") or []:
        if needle.lower() not in low:
            return f"Für diese Aufgabe braucht die Abfrage noch `{needle}`."
    for needle in exercise.get("forbid") or []:
        if needle.lower() in low:
            return f"`{needle}` soll in dieser Aufgabe nicht vorkommen."
    return None


def _wants_strict_columns(step):
    """Spaltenlektionen prüfen das Ergebnis streng — außer die Musterlösung ist SELECT *."""
    if "strict_columns" in step:
        return bool(step.get("strict_columns"))
    sol = strip_sql_line_comments(step.get("solution") or "")
    return not re.search(r"(?is)\bselect\s+(?:distinct\s+)?\*", sol)


def academy_sql_feedback(user_sql, step, user, solution):
    ordered = bool(step.get("ordered"))
    strict = _wants_strict_columns(step)
    user_cols, user_rows = user["columns"] or [], user["rows"] or []
    sol_cols, sol_rows = solution["columns"] or [], solution["rows"] or []
    correct, missing, extra, user_n, sol_n = compare_query_result(
        user_cols, user_rows, sol_cols, sol_rows, ordered=ordered, strict_columns=strict
    )
    req_coach = sql_requirement_coach(user_sql, step)
    if req_coach:
        correct = False
    coach = diagnose_structure(user_sql, step.get("solution") or "", step)
    if not correct and not coach:
        if req_coach:
            coach = req_coach
        elif strict and extra and not missing:
            coach = (
                "SELECT bestimmt, welche Spalten erscheinen. "
                f"Du hast zusätzlich: {', '.join(extra)}. Lass überflüssige Spalten weg."
            )
        elif missing:
            coach = (
                "Im Ergebnis fehlen noch Spalten: "
                + ", ".join(missing)
                + ". Nach `SELECT` stehen die gewünschten Spalten."
            )
        elif ordered and user_n == sol_n:
            coach = "Die Zeilen stimmen, die Reihenfolge noch nicht. Prüfe `ORDER BY` und `ASC`/`DESC`."
        elif user_n != sol_n:
            coach = (
                f"Es kommen {user_n} Zeilen zurück, erwartet sind {sol_n}. "
                "Prüfe Filter (`WHERE`) und ob ein JOIN Zeilen weglässt."
            )
        else:
            coach = "Die zurückgegebenen Zeilen passen noch nicht zur Aufgabe. Vergleiche Filter und Werte."
    elif correct:
        coach = None
    elif req_coach:
        coach = req_coach
    return {
        "ok": True,
        "correct": correct,
        "columns": user_cols,
        "rows": user_rows,
        "row_count": len(user_rows),
        "expected_row_count": sol_n,
        "coach": coach,
        "explain": explain_sql_query(user_sql) if correct else None,
        "messages": user.get("messages") or [],
    }


def _fail_payload(user_sql, step, user):
    coach = diagnose_structure(user_sql, step.get("solution") or "", step) or user.get("error")
    return {
        "ok": True,
        "correct": False,
        "columns": user.get("columns") or [],
        "rows": user.get("rows") or [],
        "row_count": len(user.get("rows") or []),
        "coach": coach,
        "error": user.get("error"),
        "pg_error": user.get("pg_error"),
        "messages": user.get("messages") or [],
    }


def academy_write_check(user_sql, step):
    err = _restore_error()
    if err:
        return err
    try:
        sol = run_sql(step["solution"], allow_write=True)
        if not sol["ok"]:
            return {"ok": False, "error": "Interner Fehler in der Musterlösung: " + (sol.get("error") or "")}
        expected = run_sql(step["verify"], allow_write=False)
        if not expected["ok"]:
            return {"ok": False, "error": "Interner Fehler in der Prüfung: " + (expected.get("error") or "")}

        err = _restore_error()
        if err:
            return err
        user = run_sql(user_sql, allow_write=True)
        if user.get("empty_select") or not user["ok"]:
            return _fail_payload(user_sql, step, user)
        verified = run_sql(step["verify"], allow_write=False)
        if not verified["ok"]:
            return _fail_payload(user_sql, step, verified)
        payload = academy_sql_feedback(user_sql, step, verified, expected)
        payload["messages"] = user.get("messages") or []
        return payload
    finally:
        restore_learn_schema()


@app.route("/api/academy/check", methods=["POST"])
def api_academy_check():
    data = request.get_json(force=True) or {}
    lesson_obj = academy_lesson_by_id(data.get("lesson_id"))
    if not lesson_obj:
        return jsonify({"ok": False, "error": "Unbekannte Lektion."})
    try:
        idx = int(data.get("step", 0))
        step = lesson_obj["steps"][idx]
    except (TypeError, ValueError, IndexError):
        return jsonify({"ok": False, "error": "Unbekannter Schritt."})

    sql_types = {"write", "build", "fill", "apply", "challenge", "demo"}
    if step.get("type") not in sql_types and not step.get("solution"):
        return jsonify({"ok": False, "error": "Dieser Schritt wird in der App geprüft."})

    sql = data.get("sql") or ""
    allow_write = bool(step.get("allow_write") or step.get("verify"))

    err = _restore_error()
    if err:
        return jsonify(err)

    if step.get("check") == "explain":
        user = run_sql(sql, allow_write=False)
        req = sql_requirement_coach(sql, step)
        if req:
            return jsonify({
                "ok": True,
                "correct": False,
                "columns": user.get("columns") or [],
                "rows": user.get("rows") or [],
                "coach": req,
            })
        cols = [c.lower() for c in (user.get("columns") or [])]
        ok = bool(user.get("ok")) and "query plan" in cols
        coach = None if ok else (
            diagnose_structure(sql, step.get("solution") or "", step)
            or "Vor die Abfrage gehört `EXPLAIN` — du willst den Plan, nicht die Datenzeilen."
        )
        return jsonify({
            "ok": True,
            "correct": ok,
            "columns": user.get("columns") or [],
            "rows": user.get("rows") or [],
            "row_count": len(user.get("rows") or []),
            "coach": coach,
            "error": user.get("error"),
            "pg_error": user.get("pg_error"),
        })

    if step.get("verify"):
        payload = academy_write_check(sql, step)
        return jsonify(payload)

    user = run_sql(sql, allow_write=allow_write)
    if user.get("empty_select") or not user["ok"]:
        return jsonify(_fail_payload(sql, step, user))

    solution = run_sql(step["solution"], allow_write=allow_write)
    if not solution["ok"]:
        return jsonify({"ok": False, "error": "Interner Fehler in der Musterlösung: " + solution["error"]})
    return jsonify(academy_sql_feedback(sql, step, user, solution))


@app.route("/api/explain", methods=["POST"])
def api_explain():
    data = request.get_json(force=True) or {}
    sql = data.get("sql") or ""
    if not sql.strip():
        return jsonify({"ok": False, "error": "Bitte SQL einfügen."})
    explained = explain_sql_query(sql)
    return jsonify({"ok": True, **explained})


@app.route("/api/schema")
def api_schema():
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT c.table_schema, c.table_name, c.column_name, c.data_type,
                           c.ordinal_position
                    FROM information_schema.columns c
                    WHERE c.table_schema = 'learn'
                    ORDER BY c.table_name, c.ordinal_position
                    """
                )
                rows = cur.fetchall()
    except Exception as e:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(e)})

    tables = {}
    for row in rows:
        key = row["table_name"]
        if key not in tables:
            tables[key] = {
                "schema": row["table_schema"],
                "name": row["table_name"],
                "short": row["table_name"],
                "qualified": f"learn.{row['table_name']}",
                "sandbox": "learn",
                "label": TABLE_LABELS.get(row["table_name"], row["table_name"]),
                "parent": "",
                "kind": "Training",
                "columns": [],
            }
        tables[key]["columns"].append({
            "name": row["column_name"],
            "type": row["data_type"],
        })
    return jsonify({"ok": True, "tables": list(tables.values())})


@app.route("/api/preview", methods=["POST"])
def api_preview():
    data = request.get_json(force=True) or {}
    schema = data.get("schema", "learn")
    table = data.get("table", "")
    if schema not in ALLOWED_SCHEMAS or not SAFE_IDENT.match(table):
        return jsonify({"ok": False, "error": "Ungültige Tabelle."})
    sql = f"SELECT * FROM {schema}.{table} LIMIT 8"
    result = run_sql(sql)
    if not result["ok"]:
        return jsonify({"ok": False, "error": result["error"]})
    return jsonify({
        "ok": True,
        "columns": result["columns"],
        "rows": result["rows"],
        "note": result.get("note"),
        "sql": sql,
    })


@app.route("/api/reset", methods=["POST"])
def api_reset():
    ok, message = reset_learning_db()
    if not ok:
        return jsonify({"ok": False, "error": message})
    return jsonify({"ok": True, "message": message})


@app.route("/api/cards")
def api_cards():
    return jsonify({"ok": True, "cards": FLASHCARDS})


@app.route("/api/search")
def api_search():
    query = (request.args.get("q") or "").strip()
    if len(query) < 2:
        return jsonify({"ok": True, "results": [], "hint": "Mindestens zwei Zeichen."})
    terms = [t for t in _plain(query).split() if t]
    scored = []
    for item in SEARCH_INDEX:
        hay = item["text"]
        if not all(t in hay for t in terms):
            continue
        title_l = item["title"].lower()
        score = 0
        for t in terms:
            if t in title_l:
                score += 8
            score += hay.count(t)
        if item["type"] in {"lektion", "konzept", "artikel"}:
            score += 3
        if item["type"] == "artikel":
            score += 4
        scored.append((score, item))
    scored.sort(key=lambda x: (-x[0], x[1]["letter"], x[1]["title"]))
    results = []
    seen = set()
    for score, item in scored:
        key = (item["type"], item["title"], item["url"])
        if key in seen:
            continue
        seen.add(key)
        results.append({
            "type": item["type"],
            "letter": item["letter"],
            "title": item["title"],
            "url": item["url"],
            "snippet": _snippet(item.get("preview") or item["title"], query),
            "lesson_id": item["lesson_id"],
        })
        if len(results) >= 24:
            break
    return jsonify({"ok": True, "results": results, "query": query})


if __name__ == "__main__":
    ensure_learn_schema()
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    host = os.environ.get("APP_HOST", "0.0.0.0")
    port = int(os.environ.get("APP_PORT", "8080"))
    app.run(host=host, port=port, debug=debug, use_reloader=debug)
