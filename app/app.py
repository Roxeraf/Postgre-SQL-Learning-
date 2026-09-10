import json
import os
import re
from collections import Counter
from pathlib import Path

import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, render_template, request

from lessons.academy_data import ACADEMY, lesson_by_id as academy_lesson_by_id
from sql_coach import (
    diagnose_structure,
    explain_sql as explain_sql_query,
    friendly_sql_error,
    has_empty_select_list,
    strip_sql_line_comments,
)

app = Flask(__name__)

LESSONS_PATH = Path(__file__).parent / "lessons" / "lessons.json"
with open(LESSONS_PATH, encoding="utf-8") as f:
    LESSONS = json.load(f)

CATALOG_PATH = Path(__file__).parent / "lessons" / "table_catalog.json"
if CATALOG_PATH.exists():
    with open(CATALOG_PATH, encoding="utf-8") as f:
        TABLE_CATALOG = json.load(f)
else:
    TABLE_CATALOG = {}

LESSONS_BY_ID = {l["id"]: l for l in LESSONS}
TABLE_NAME_RE = re.compile(r"\b((?:instance_1|subscription)\.[a-zA-Z0-9_]+)", re.I)


def catalog_info(short: str) -> dict:
    return TABLE_CATALOG.get(short) or {}


def tables_used(*sql_parts):
    found, seen = [], set()
    blob = " ".join(part or "" for part in sql_parts)
    for match in TABLE_NAME_RE.findall(blob):
        key = match.lower()
        if key in seen:
            continue
        seen.add(key)
        short = match.split(".")[-1]
        for prefix in ("flowapp_demo_", "flowapp_13d663_"):
            if short.lower().startswith(prefix):
                short = short[len(prefix):]
                break
        info = catalog_info(short)
        found.append({
            "qualified": match,
            "short": short,
            "label": info.get("label") or short,
            "parent": info.get("parent") or "",
            "kind": info.get("kind") or "",
        })
    return found


EXERCISES_BY_ID = {}
for lesson in LESSONS:
    for ex in lesson.get("exercises", []):
        ex["tables"] = tables_used(ex.get("solution"), ex.get("verify"), ex.get("starter"))
        EXERCISES_BY_ID[ex["id"]] = ex

FLASHCARDS = []
for lesson in LESSONS:
    for card in lesson.get("flashcards", []):
        FLASHCARDS.append({**card, "lesson_id": lesson["id"], "lesson": lesson["title"]})
    for i, q in enumerate(lesson.get("quiz", []), start=1):
        correct = q["options"][q["correct"]]
        FLASHCARDS.append({
            "id": f"{lesson['id']}-quiz-{i}",
            "front": q["q"],
            "back": correct + ((" — " + q["explain"]) if q.get("explain") else ""),
            "lesson_id": lesson["id"],
            "lesson": lesson["title"],
        })

TRACKS = [
    {
        "id": "einstieg",
        "label": "Einstieg · SQL, A–J",
        "blurb": "Zuerst SELECT und JOINs, dann Grundlagen, Umgebung, Datenmodell und Arbeitsregeln aus der Einarbeitung.",
        "lessons": [l for l in LESSONS if l.get("track") == "einstieg"],
    },
    {
        "id": "vertiefung",
        "label": "Vertiefung K–P",
        "blurb": "Installations-Eigenheiten, Statuslogik, Alias-Filter, Verpackung, Zoll und Tracking.",
        "lessons": [l for l in LESSONS if l.get("track") == "vertiefung"],
    },
]


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


SEARCH_INDEX = []
for lesson in LESSONS:
    letter = lesson.get("letter") or lesson["id"].upper()
    url = f"/lesson/{lesson['id']}"
    SEARCH_INDEX.append({
        "type": "lektion",
        "lesson_id": lesson["id"],
        "letter": letter,
        "title": f"Teil {letter} — {lesson['title']}",
        "url": url,
        "text": _plain(" ".join([
            lesson["title"],
            " ".join(lesson.get("goals") or []),
            lesson.get("content") or "",
        ])),
        "preview": " ".join(lesson.get("goals") or []),
    })
    for block in re.split(r"\n##\s+", lesson.get("content") or ""):
        block = block.strip()
        if not block:
            continue
        title, _, body = block.partition("\n")
        if not title.strip():
            continue
        SEARCH_INDEX.append({
            "type": "abschnitt",
            "lesson_id": lesson["id"],
            "letter": letter,
            "title": title.strip(),
            "url": url,
            "text": _plain(title + " " + body),
            "preview": body[:280],
        })
    for card in lesson.get("flashcards") or []:
        SEARCH_INDEX.append({
            "type": "karte",
            "lesson_id": lesson["id"],
            "letter": letter,
            "title": card["front"],
            "url": "/cards",
            "text": _plain(card["front"] + " " + card["back"]),
            "preview": card["back"],
        })
    for ex in lesson.get("exercises") or []:
        SEARCH_INDEX.append({
            "type": "übung",
            "lesson_id": lesson["id"],
            "letter": letter,
            "title": ex["prompt"][:90],
            "url": url,
            "text": _plain(
                " ".join([
                    ex.get("why") or "",
                    ex.get("task") or ex.get("prompt") or "",
                    " ".join(ex.get("look") or []),
                    " ".join(ex.get("hints") or []),
                ])
            ),
            "preview": ex["prompt"],
        })

DB_CONFIG = dict(
    host=os.environ.get("DB_HOST", "db"),
    port=os.environ.get("DB_PORT", "5432"),
    dbname=os.environ.get("DB_NAME", "flowapp_learn"),
    user=os.environ.get("DB_USER", "lernuser"),
    password=os.environ.get("DB_PASSWORD", "lernuser"),
    connect_timeout=5,
    options="-c statement_timeout=8s",
)

MAX_ROWS = 200
SAFE_IDENT = re.compile(r"^[a-zA-Z0-9_]+$")
ALLOWED_SCHEMAS = ("instance_1", "subscription", "learn")
ADMIN_CONFIG = dict(
    DB_CONFIG,
    user=os.environ.get("DB_ADMIN_USER", "postgres"),
    password=os.environ.get("DB_ADMIN_PASSWORD", "postgres"),
)

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


def get_connection(admin=False, search_path=None):
    cfg = dict(ADMIN_CONFIG if admin else DB_CONFIG)
    conn = psycopg2.connect(**cfg)
    conn.autocommit = True
    if search_path == "learn":
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


def run_sql(sql: str, sandbox: str = "wmx"):
    """Führt SQL aus. sandbox=learn: nur lesen, search_path=learn. sandbox=wmx: bestehende Übungs-DB."""
    raw = (sql or "").strip()
    sandbox = "learn" if sandbox == "learn" else "wmx"
    if not raw:
        return {"ok": False, "error": "Bitte gib eine SQL-Abfrage ein.", "columns": None, "rows": None, "pg_error": None}

    if FORBIDDEN_KEYWORDS.search(strip_sql_line_comments(raw)):
        msg = (
            "Im Übungsbereich darfst du das Datenbank-Schema nicht ändern (kein DROP/ALTER/CREATE)."
            if sandbox == "learn"
            else (
                "DROP, ALTER, CREATE und ähnliche Schema-Befehle sind in der Lern-App gesperrt. "
                "SELECT, INSERT, UPDATE, DELETE sowie BEGIN/COMMIT sind erlaubt."
            )
        )
        return {"ok": False, "error": msg, "columns": None, "rows": None, "pg_error": None}

    statements = split_statements(raw)
    if not statements:
        return {"ok": False, "error": "Bitte gib eine SQL-Abfrage ein.", "columns": None, "rows": None, "pg_error": None}

    incomplete = next((s for s in statements if has_empty_select_list(s)), None)
    if incomplete:
        empty_msg = (
            "Nach SELECT fehlt noch, **was** du sehen möchtest — zum Beispiel `*` oder Spaltennamen."
            if sandbox == "learn"
            else (
                "Die SELECT-Liste ist noch leer. Rechts eine Spalte anklicken — sie landet in der Lücke nach SELECT."
            )
        )
        return {
            "ok": False,
            "error": empty_msg,
            "columns": None,
            "rows": None,
            "empty_select": True,
            "pg_error": None,
        }

    columns, rows, note = [], [], None
    messages = []
    try:
        with get_connection(search_path="learn" if sandbox == "learn" else None) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                for stmt in statements:
                    kind = classify_statement(stmt)
                    if kind == "empty":
                        continue
                    if sandbox == "learn" and kind in {"write", "begin", "commit", "rollback"}:
                        return {
                            "ok": False,
                            "error": (
                                "Im Anfänger-Bereich sind nur lesende Abfragen erlaubt: "
                                "`SELECT`, `WITH` und `EXPLAIN`."
                            ),
                            "columns": None,
                            "rows": None,
                            "pg_error": None,
                        }
                    if kind == "unknown":
                        allowed = (
                            "Erlaubt sind SELECT und EXPLAIN."
                            if sandbox == "learn"
                            else "Erlaubt sind SELECT, INSERT, UPDATE, DELETE und BEGIN/COMMIT/ROLLBACK."
                        )
                        return {
                            "ok": False,
                            "error": "Dieser Befehl ist hier nicht erlaubt. " + allowed,
                            "columns": None,
                            "rows": None,
                            "pg_error": None,
                        }
                    if kind == "write" and not re.search(
                        r"\b(instance_1|subscription)\.", stmt, re.IGNORECASE
                    ):
                        return {
                            "ok": False,
                            "error": (
                                "Schreibzugriffe bitte vollqualifiziert auf instance_1 oder subscription "
                                "(z. B. UPDATE instance_1.flowapp_demo_order_head ...)."
                            ),
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
    except Exception as e:  # noqa: BLE001 - want to surface DB errors to the learner
        pg_error = str(e)
        return {
            "ok": False,
            "error": friendly_sql_error(pg_error, raw, sandbox=sandbox),
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


def _learn_sql_fragment(script: str) -> str | None:
    start = script.find("DROP SCHEMA IF EXISTS learn")
    return script[start:] if start >= 0 else None


def reset_learning_db():
    sql_path = _init_sql_path()
    if not sql_path:
        return False, "Init-SQL nicht gefunden. Bitte die App neu installieren bzw. den Container mit db/init starten."
    script = sql_path.read_text(encoding="utf-8")
    try:
        with get_connection(admin=True) as conn:
            with conn.cursor() as cur:
                cur.execute("DROP SCHEMA IF EXISTS instance_1 CASCADE")
                cur.execute("DROP SCHEMA IF EXISTS subscription CASCADE")
                cur.execute("DROP SCHEMA IF EXISTS learn CASCADE")
                cur.execute(script)
    except Exception as e:  # noqa: BLE001
        return False, str(e)
    return True, "Lern-Datenbank ist wieder im Ausgangszustand."


def ensure_learn_schema():
    """Alte Volumes ohne learn-Schema nachziehen."""
    sql_path = _init_sql_path()
    if not sql_path:
        return
    try:
        with get_connection(admin=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM information_schema.schemata WHERE schema_name = 'learn'")
                if cur.fetchone():
                    return
        fragment = _learn_sql_fragment(sql_path.read_text(encoding="utf-8"))
        if not fragment:
            return
        with get_connection(admin=True) as conn:
            with conn.cursor() as cur:
                cur.execute(fragment)
    except Exception:  # noqa: BLE001
        pass


def ensure_write_privileges():
    """Damit bestehende Docker-Volumes ohne Neuaufsetzen schreiben dürfen."""
    try:
        with get_connection(admin=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA instance_1 TO lernuser;
                    GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA subscription TO lernuser;
                    GRANT USAGE ON SCHEMA learn TO lernuser;
                    GRANT SELECT ON ALL TABLES IN SCHEMA learn TO lernuser;
                    """
                )
    except Exception:  # noqa: BLE001
        pass


def normalize_rows(rows):
    """Erzeugt eine ordnungs- und typunabhaengige Repraesentation zum Vergleich."""
    normalized = []
    for row in rows:
        values = tuple(sorted(row.items(), key=lambda kv: kv[0]))
        normalized.append(tuple(str(v) for _, v in values))
    return sorted(normalized)


def project_rows(rows, wanted_cols, col_map):
    keys = []
    for row in rows or []:
        keys.append(tuple(str(row.get(col_map[c])) for c in wanted_cols))
    return sorted(set(keys))


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
    """Alias-unabhängig: Lösungswerte müssen in den Nutzerzeilen vorkommen."""
    users = unique_rows(user_rows)
    sols = unique_rows(sol_rows)
    if not sols and not users:
        return True, 0, 0
    if any(not any(row_covers(u, s) for s in sols) for u in users):
        return False, len(users), len(sols)
    if any(not any(row_covers(u, s) for u in users) for s in sols):
        return False, len(users), len(sols)
    return True, len(users), len(sols)


def project_row_seq(rows, wanted_cols, col_map):
    seq = []
    for row in rows or []:
        seq.append(tuple(_cell_str(row.get(col_map[c])) for c in wanted_cols))
    return seq


def compare_query_result(user_cols, user_rows, sol_cols, sol_rows, ordered=False, strict_columns=False):
    """Vergleicht Ergebnisse. Extra-Spalten und andere Aliase sind ok, außer strict_columns."""
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


def lesson_nav(lesson_id):
    ids = list(LESSONS_BY_ID.keys())
    idx = ids.index(lesson_id)
    return (
        ids[idx - 1] if idx > 0 else None,
        ids[idx + 1] if idx < len(ids) - 1 else None,
    )


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
        "tracks": TRACKS,
        "academy": ACADEMY,
        "academy_lessons": ACADEMY["lessons"],
    }


@app.route("/")
def index():
    return render_template(
        "index.html",
        lessons=LESSONS,
        academy_lessons=ACADEMY["lessons"],
        academy_concepts=ACADEMY["concepts"],
        current_lesson_id=None,
        exercise_count=sum(len(l.get("exercises") or []) for l in LESSONS),
        quiz_count=sum(len(l.get("quiz") or []) for l in LESSONS),
        card_count=len(FLASHCARDS),
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
        lessons=LESSONS,
        prev_id=prev_id,
        next_id=next_id,
        current_lesson_id=None,
        current_academy_id=lesson_id,
    )


@app.route("/lesson/<lesson_id>")
def lesson(lesson_id):
    lesson_obj = LESSONS_BY_ID.get(lesson_id)
    if not lesson_obj:
        return "Lektion nicht gefunden", 404
    prev_id, next_id = lesson_nav(lesson_id)
    return render_template(
        "lesson.html",
        lesson=lesson_obj,
        lessons=LESSONS,
        prev_id=prev_id,
        next_id=next_id,
        current_lesson_id=lesson_id,
    )


@app.route("/playground")
def playground():
    return render_template(
        "playground.html",
        lessons=LESSONS,
        current_lesson_id=None,
        active_tool="playground",
    )


@app.route("/cards")
def cards():
    return render_template(
        "cards.html",
        lessons=LESSONS,
        current_lesson_id=None,
        active_tool="cards",
        card_count=len(FLASHCARDS),
    )


@app.route("/wissen")
def wissen():
    return render_template(
        "wissen.html",
        lessons=LESSONS,
        current_lesson_id=None,
        active_tool="wissen",
        index_count=len(SEARCH_INDEX),
    )


@app.route("/api/run", methods=["POST"])
def api_run():
    data = request.get_json(force=True)
    sandbox = data.get("sandbox") or "wmx"
    result = run_sql(data.get("sql", ""), sandbox=sandbox)
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
            return f"In der Abfrage fehlt noch: {needle}."
    for needle in exercise.get("forbid") or []:
        if needle.lower() in low:
            return f"Bitte {needle} nicht verwenden — siehe Aufgabe."
    return None


def empty_select_coach(exercise: dict) -> str:
    look = exercise.get("look") or []
    hint = (exercise.get("hints") or [None])[0]
    parts = ["Die SELECT-Liste ist noch leer. Rechts eine Spalte anklicken — sie landet in der Lücke nach SELECT."]
    if look:
        parts.append(look[0])
    elif hint:
        parts.append(hint)
    return " ".join(parts)


@app.route("/api/check", methods=["POST"])
def api_check():
    data = request.get_json(force=True)
    ex_id = data.get("exercise_id")
    sql = data.get("sql", "")
    exercise = EXERCISES_BY_ID.get(ex_id)
    if not exercise:
        return jsonify({"ok": False, "error": "Unbekannte Übung."})

    if exercise.get("kind") == "write":
        applied = run_sql(sql)
        if not applied["ok"]:
            return jsonify({"ok": False, "error": applied["error"]})
        verified = run_sql(exercise["verify"])
        if not verified["ok"]:
            return jsonify({"ok": False, "error": "Prüfung fehlgeschlagen: " + verified["error"]})
        expected = exercise.get("expected") or []
        correct = normalize_rows(verified["rows"]) == normalize_rows(expected)
        coach = None
        if not correct:
            if re.search(r"\bbegin\b", sql, re.I) and not re.search(r"\bcommit\b", sql, re.I):
                coach = "Du hast BEGIN ohne COMMIT — die Änderung wurde beim Schließen der Verbindung verworfen."
            else:
                coach = (
                    "Der Datenstand nach deinem Skript stimmt noch nicht. "
                    "Prüfe WHERE, die Zielwerte und das Sicherheitsmuster (BEGIN → Änderung → SELECT → COMMIT)."
                )
        return jsonify({
            "ok": True,
            "correct": correct,
            "columns": verified["columns"],
            "rows": verified["rows"],
            "messages": applied.get("messages") or [],
            "note": applied.get("note"),
            "row_count": len(verified["rows"] or []),
            "coach": coach,
        })

    user = run_sql(sql)
    if user.get("empty_select"):
        return jsonify({
            "ok": True,
            "correct": False,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "coach": empty_select_coach(exercise),
        })
    if not user["ok"]:
        return jsonify({"ok": False, "error": user["error"]})

    req_coach = sql_requirement_coach(sql, exercise)

    solution = run_sql(exercise["solution"])
    if not solution["ok"]:
        return jsonify({"ok": False, "error": "Interner Fehler in der Musterlösung: " + solution["error"]})

    user_cols, user_rows = user["columns"] or [], user["rows"] or []
    sol_cols, sol_rows = solution["columns"] or [], solution["rows"] or []
    correct, missing, extra, user_n, sol_n = compare_query_result(
        user_cols, user_rows, sol_cols, sol_rows
    )
    if req_coach:
        correct = False
    coach = None
    if not correct:
        if req_coach:
            coach = req_coach
        elif missing and extra:
            coach = (
                "Ein Alias in der SELECT-Liste ist nicht nötig. "
                "Die Werte weichen aber noch ab — prüfe Konvertierung, Filter und Joins."
            )
        elif missing:
            coach = (
                "Es fehlen noch Daten in der SELECT-Liste. "
                "Schau in der Aufgabe, welche Felder ausgegeben werden sollen."
            )
        elif user_n != sol_n:
            coach = (
                f"Zeilenanzahl stimmt nicht: du hast {user_n} eindeutige Treffer, "
                f"erwartet werden {sol_n}. Prüfe JOIN, WHERE und Deduplizierung."
            )
        else:
            coach = (
                "Spaltenanzahl passt, der Inhalt weicht aber noch ab. "
                "Prüfe Filter, JSON-Zugriff (->) und ob du den neuesten Datensatz nimmst."
            )

    return jsonify({
        "ok": True,
        "correct": correct,
        "columns": user_cols,
        "rows": user_rows,
        "row_count": len(user_rows),
        "expected_row_count": sol_n,
        "coach": coach,
    })


@app.route("/api/hint/<exercise_id>")
def api_hint(exercise_id):
    exercise = EXERCISES_BY_ID.get(exercise_id)
    if not exercise:
        return jsonify({"ok": False, "error": "Unbekannte Übung."})
    try:
        level = int(request.args.get("level", "1"))
    except ValueError:
        level = 1
    hints = exercise.get("hints") or []
    if level > len(hints) + 1:
        return jsonify({"ok": False, "error": "Keine weiteren Hinweise."})
    if level <= len(hints):
        return jsonify({
            "ok": True,
            "kind": "hint",
            "level": level,
            "total": len(hints) + 1,
            "text": hints[level - 1],
        })
    return jsonify({
        "ok": True,
        "kind": "solution",
        "level": level,
        "total": len(hints) + 1,
        "solution": exercise["solution"],
    })


@app.route("/api/solution/<exercise_id>")
def api_solution(exercise_id):
    exercise = EXERCISES_BY_ID.get(exercise_id)
    if not exercise:
        return jsonify({"ok": False, "error": "Unbekannte Übung."})
    return jsonify({"ok": True, "solution": exercise["solution"]})


def academy_sql_feedback(user_sql, step, user, solution):
    ordered = bool(step.get("ordered"))
    strict = bool(step.get("strict_columns"))
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
                + ". SELECT sagt, was du sehen möchtest."
            )
        elif ordered and user_n == sol_n:
            coach = "Die Zeilen stimmen, die Reihenfolge noch nicht. Prüfe `ORDER BY` und `ASC`/`DESC`."
        elif user_n != sol_n:
            coach = (
                f"Zeilenanzahl stimmt nicht: du hast {user_n}, erwartet werden {sol_n}. "
                "Prüfe `WHERE`, `AND`/`OR` und `LIMIT`."
            )
        else:
            coach = "Das Ergebnis weicht noch ab. Vergleiche Filter, Spalten und Werte mit der Aufgabenstellung."
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
    }


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
    user = run_sql(sql, sandbox="learn")
    if user.get("empty_select") or not user["ok"]:
        coach = diagnose_structure(sql, step.get("solution") or "", step) or user.get("error")
        return jsonify({
            "ok": True,
            "correct": False,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "coach": coach,
            "error": user.get("error"),
            "pg_error": user.get("pg_error"),
        })

    solution = run_sql(step["solution"], sandbox="learn")
    if not solution["ok"]:
        return jsonify({"ok": False, "error": "Interner Fehler in der Musterlösung: " + solution["error"]})
    payload = academy_sql_feedback(sql, step, user, solution)
    return jsonify(payload)


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
                    WHERE c.table_schema IN ('instance_1', 'subscription', 'learn')
                    ORDER BY c.table_schema, c.table_name, c.ordinal_position
                    """
                )
                rows = cur.fetchall()
    except Exception as e:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(e)})

    tables = {}
    for row in rows:
        key = f"{row['table_schema']}.{row['table_name']}"
        if key not in tables:
            short = row["table_name"]
            for prefix in ("flowapp_demo_", "flowapp_13d663_"):
                if short.lower().startswith(prefix):
                    short = short[len(prefix):]
                    break
            info = catalog_info(short)
            tables[key] = {
                "schema": row["table_schema"],
                "name": row["table_name"],
                "short": short,
                "qualified": key,
                "sandbox": "learn" if row["table_schema"] == "learn" else "wmx",
                "label": info.get("label") or {"orders": "Aufträge", "clients": "Kunden", "stock": "Bestand"}.get(short, short),
                "parent": info.get("parent") or "",
                "kind": info.get("kind") or ("Training" if row["table_schema"] == "learn" else ""),
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
    schema = data.get("schema", "")
    table = data.get("table", "")
    if schema not in ALLOWED_SCHEMAS or not SAFE_IDENT.match(table):
        return jsonify({"ok": False, "error": "Ungültige Tabelle."})
    sql = f'SELECT * FROM {schema}.{table} LIMIT 8'
    result = run_sql(sql, sandbox="learn" if schema == "learn" else "wmx")
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
        if item["type"] == "lektion":
            score += 3
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
    ensure_write_privileges()
    ensure_learn_schema()
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    host = os.environ.get("APP_HOST", "0.0.0.0")
    port = int(os.environ.get("APP_PORT", "8080"))
    app.run(host=host, port=port, debug=debug, use_reloader=debug)
