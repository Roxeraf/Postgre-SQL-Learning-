import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

import psycopg2
from flask import Flask, jsonify, redirect, render_template, request


def ensure_app_on_path() -> Path:
    """Keep `lessons` importable when cwd is not on sys.path.

    The Windows embeddable runtime ships a python*._pth file. That file
    replaces the normal path setup, so the working directory is not added
    and PYTHONPATH is ignored. Resolve the folder that actually contains
    the lesson package — either next to this file or in ./app.
    """
    here = Path(__file__).resolve().parent
    for candidate in (here, here / "app"):
        if (candidate / "lessons" / "academy_data.py").is_file():
            path = str(candidate)
            if path not in sys.path:
                sys.path.insert(0, path)
            return candidate
    path = str(here)
    if path not in sys.path:
        sys.path.insert(0, path)
    return here


ensure_app_on_path()


def ensure_mcp_on_path() -> Path | None:
    here = Path(__file__).resolve().parent
    for candidate in (here.parent / "mcp", here / "mcp"):
        if (candidate / "install_mcp.py").is_file():
            path = str(candidate)
            if path not in sys.path:
                sys.path.insert(0, path)
            return candidate
    return None


ensure_mcp_on_path()

from lessons.academy_data import ACADEMY, lesson_by_id as academy_lesson_by_id  # noqa: E402
from lessons.knowledge import (  # noqa: E402
    ARTICLES,
    article_by_slug,
    knowledge_cards,
    related_articles,
    sections as knowledge_sections,
)
from learn_db import (  # noqa: E402
    ALLOWED_SCHEMAS,
    SAFE_IDENT,
    ensure_app_database,
    fetch_schema,
    get_connection,
    is_missing_database_error as _is_missing_database_error,
    run_sql,
    _format_restore_error,
)
from lessons.workshop import delete_workshop_lesson, workshop_by_id, workshop_lessons  # noqa: E402
from sql_coach import (  # noqa: E402
    diagnose_structure,
    explain_sql as explain_sql_query,
    friendly_sql_error,
    has_empty_select_list,
    strip_sql_line_comments,
)

app = Flask(__name__)


def _load_mcp_status_file():
    homes = []
    env_home = os.environ.get("LEARN_SQL_HOME")
    if env_home:
        homes.append(Path(env_home))
    homes.append(Path(__file__).resolve().parent.parent)
    for home in homes:
        path = home / "mcp-status.json"
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            return data
    return None


def _install_mcp():
    ensure_mcp_on_path()
    try:
        import install_mcp
    except ImportError:
        return None
    return install_mcp


def load_mcp_status():
    helper = _install_mcp()
    if helper:
        return helper.probe_status(helper.resolve_home())
    return _load_mcp_status_file()

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


def find_lesson(lesson_id):
    return academy_lesson_by_id(lesson_id) or workshop_by_id(lesson_id)


def academy_nav(lesson_id):
    lesson = workshop_by_id(lesson_id)
    ids = [l["id"] for l in (workshop_lessons() if lesson else ACADEMY["lessons"])]
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
        "mcp_status": load_mcp_status(),
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
    lesson_obj = find_lesson(lesson_id)
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
    return render_template(
        "playground.html",
        active_tool="playground",
        practices=workshop_lessons(),
        mcp_status=load_mcp_status(),
    )


@app.route("/playground/<lesson_id>")
def playground_lesson(lesson_id):
    lesson_obj = workshop_by_id(lesson_id)
    if not lesson_obj:
        return "Übung nicht gefunden", 404
    prev_id, next_id = academy_nav(lesson_id)
    return render_template(
        "academy.html",
        lesson=lesson_obj,
        prev_id=prev_id,
        next_id=next_id,
        current_academy_id=lesson_id,
    )


@app.route("/werkstatt")
def werkstatt_redirect():
    target = "/playground"
    qs = request.query_string.decode() if request.query_string else ""
    if qs:
        target = f"{target}?{qs}"
    return redirect(target, 301)


@app.route("/werkstatt/<lesson_id>")
def werkstatt_lesson_redirect(lesson_id):
    return redirect(f"/playground/{lesson_id}", 301)


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
    lesson_obj = find_lesson(data.get("lesson_id"))
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
    return jsonify(fetch_schema())


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


@app.route("/api/playground/<lesson_id>/delete", methods=["POST"])
def api_playground_delete(lesson_id):
    try:
        deleted = delete_workshop_lesson(lesson_id)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    if not deleted:
        return jsonify({"ok": False, "error": "Übung nicht gefunden."}), 404
    return jsonify({"ok": True, "id": lesson_id})


@app.route("/api/mcp/connect", methods=["POST"])
def api_mcp_connect():
    helper = _install_mcp()
    if not helper:
        return jsonify({
            "ok": False,
            "error": "MCP-Einrichtung ist in diesem Paket nicht enthalten.",
            "status": {"installed": False, "clients": []},
        })
    home = helper.resolve_home()
    try:
        result = helper.install(home)
    except OSError as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
            "status": helper.probe_status(home),
        })
    status = helper.probe_status(home)
    if not result.get("installed") and not status.get("installed"):
        return jsonify({
            "ok": False,
            "error": (
                "Keine Claude-Konfiguration gefunden. "
                "Im Windows-Paket schreibt der Knopf die Dateien automatisch."
            ),
            "status": status,
        })
    return jsonify({
        "ok": True,
        "status": {
            "installed": bool(status.get("installed")),
            "clients": list(status.get("clients") or []),
            "detected": bool(status.get("detected")),
        },
    })


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
