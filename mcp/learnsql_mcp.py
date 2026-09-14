#!/usr/bin/env python3
"""stdio MCP server: schema, Wissen, Übungen in den SQL-Playground legen."""

from __future__ import annotations

import copy
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(APP))

from install_mcp import apply_runtime_env  # noqa: E402

apply_runtime_env()
os.environ.setdefault("DB_HOST", "127.0.0.1")

from learn_db import (  # noqa: E402
    CORE_SANDBOX,
    describe_target,
    run_sql,
    table_block,
)
from lessons.academy_data import ACADEMY, PATH_IDS, lesson_by_id  # noqa: E402
from lessons.knowledge import ARTICLES, article_by_slug, knowledge_cards  # noqa: E402
from lessons.buddy import (  # noqa: E402
    buddy_snapshot,
    enrich_lesson,
    help_pack,
    load_learner_context,
    resolve_lesson,
    search_learning,
    teach_for,
)
from lessons.workshop import (  # noqa: E402
    SAFE_ID,
    delete_workshop_lesson,
    save_workshop_lesson,
    workshop_by_id,
    workshop_dir,
    workshop_lessons,
)
from sql_coach import diagnose_structure, explain_sql, explain_step_parts  # noqa: E402

PROTOCOL = "2024-11-05"
BUILD = "1.2.0"

STEP_TYPES = [
    "look", "inspect", "explain", "demo", "predict", "predict-cols",
    "build", "fill", "write", "apply", "challenge", "mcq",
]

FIELD_SEMANTICS = {
    "ordered": (
        "true: die Prüfung ist sortierungssensitiv (ORDER BY muss zur Musterlösung passen). "
        "Ohne ordered darf die Zeilenreihenfolge abweichen."
    ),
    "strict_columns": (
        "true: Extra-Spalten in der Schüler-Abfrage sind falsch. "
        "Default: streng, außer die Musterlösung ist SELECT *."
    ),
    "visualize": (
        "Nur demo/predict: where (Zeilen abdunkeln, die nicht zu match_column/match_value passen), "
        "columns (nur keep_columns hell), inner (Aufträge ohne Kunde abdunkeln), all (nichts abdunkeln)."
    ),
    "execute": "Nach richtigem predict die SQL ausführen und das Ergebnis darunter zeigen.",
    "id_field": "Spalte, deren Werte Zeilenklicks und expected_ids identifizieren. Default: id.",
    "cta": "Beschriftung des Weiter-Knopfs im look-Step.",
    "teach": (
        "Alltags-Erklärung, WARUM die Query so gebaut wird. "
        "Pflicht an write/apply/challenge/build/fill. Nicht die volle Lösung."
    ),
    "plain": "Die Query in einem Satz auf Deutsch. Pflicht am explain-Step.",
    "parts": (
        "Antippbare SQL-Teile {token, match, question, answer}. "
        "Mindestens zwei am explain-Step."
    ),
    "expected_ids": (
        "Werte von id_field der Zeilen, die im predict-Step markiert werden müssen. "
        "Optional: validate_exercise / save_practice füllen sie aus sql + id_field."
    ),
    "match_column": "Zusammen mit visualize=where: Spalte, gegen die match_value verglichen wird.",
    "match_value": "Wert in match_column, der die passenden Zeilen markiert (visualize=where).",
    "keep_columns": "Spalten, die bei visualize=columns hell bleiben.",
    "table": "Eingebetteter Sandbox-Ausschnitt {name, label, columns, rows} — nicht das SQL-Ergebnis.",
}

STEP_SPECS = {
    "look": {
        "required": ["title", "text"],
        "optional": ["table", "tables", "note", "cta", "concepts", "teach"],
    },
    "inspect": {
        "required": ["title", "text", "table", "interaction", "answer"],
        "optional": ["feedback_ok", "feedback_bad", "concepts", "id_field"],
    },
    "explain": {
        "required": ["title", "text", "sql", "plain", "parts"],
        "optional": ["before_table", "after_table", "concepts", "teach"],
    },
    "demo": {
        "required": ["title", "text", "sql"],
        "optional": ["table", "visualize", "keep_columns", "match_column", "match_value", "id_field", "concepts"],
    },
    "predict": {
        "required": ["title", "text", "sql", "table"],
        "optional": ["expected_ids", "id_field", "execute", "feedback_ok", "feedback_bad", "concepts", "single"],
    },
    "predict-cols": {
        "required": ["title", "text", "sql", "expected_columns"],
        "optional": ["table", "feedback_ok", "feedback_bad", "concepts"],
    },
    "build": {
        "required": ["title", "prompt", "pieces", "solution", "teach"],
        "optional": ["distractors", "hints", "concepts"],
    },
    "fill": {
        "required": ["title", "template", "solution", "teach"],
        "optional": ["hints", "concepts"],
    },
    "write": {
        "required": ["title", "prompt", "solution", "teach"],
        "optional": ["placeholder", "hints", "concepts", "strict_columns", "ordered", "require", "forbid", "allow_write", "verify"],
    },
    "apply": {
        "required": ["title", "prompt", "solution", "teach"],
        "optional": ["placeholder", "hints", "concepts", "strict_columns", "ordered", "require", "forbid"],
    },
    "challenge": {
        "required": ["title", "prompt", "solution", "teach"],
        "optional": ["placeholder", "hints", "concepts", "strict_columns", "ordered"],
    },
    "mcq": {
        "required": ["title", "question", "options"],
        "optional": [],
    },
}

LESSON_ENVELOPE = {
    "id": {"required": True, "note": "ws-… (Buchstaben, Zahlen, Bindestrich). Nicht in PATH_IDS."},
    "title": {"required": True, "note": "Kurzer Titel wie ein Kapitel."},
    "goal": {"required": True, "note": "Ein Satz: was die Person danach kann."},
    "minutes": {"required": True, "note": "Ganze Zahl, typisch 8."},
    "concepts": {"required": True, "note": "SQL-Themen, z.B. SELECT, WHERE, JOIN."},
    "model": {"required": True, "note": "Klauseln der Musterlösung in Reihenfolge."},
    "steps": {
        "required": True,
        "note": (
            "Mindestens 3. Pflicht: look, explain (plain + mindestens zwei parts) "
            "und ein Schreib-Schritt mit teach (warum, nicht die Lösung)."
        ),
    },
    "quiz": {"required": True, "note": "Mindestens 4 Fachfragen. correct ist ein 0-basierter Index."},
}

TABLE_SHAPE = {
    "name": "orders",
    "label": "Aufträge",
    "columns": ["id", "status"],
    "rows": [{"id": 1, "status": "offen"}],
}

RESET_NOTE = (
    "Beim Zurücksetzen führt die App `DROP SCHEMA learn CASCADE` aus und baut "
    "clients, orders, stock und order_items neu auf. Zusätzliche Tabellen in learn "
    "sind danach weg."
)

INSTRUCTIONS = (
    "Du bist der Lern-Buddy für plx.learnSQL und der Autor zusätzlicher Playground-Übungen.\n"
    "Du hängst als Claude Code am MCP — aus dem Buddy-Drawer der App heraus oder direkt in deinem Client.\n"
    "\n"
    "Buddy (offizieller Lernpfad /wissen /Karten /Playground):\n"
    "Zuerst `buddy_context` (wo die Person gerade ist). "
    "Fragen mit `help_with` und `search_path` beantworten. "
    "SQL der Person mit `coach_sql` prüfen — Hinweise, nicht die volle Lösung, außer sie wird verlangt. "
    "Kapitel: `get_lesson` / `list_lessons`. Bibel: `search_wissen` / `get_article`.\n"
    "\n"
    "Playground-Übungen (neben dem Pfad, Form wie der Lernpfad):\n"
    "Ablauf: anschauen → verstehen (explain mit plain + parts) → vorhersagen → "
    "selbst schreiben (mit teach) → Kurzcheck.\n"
    "Jede Übung braucht: id (ws-…), title, goal, minutes, concepts, model, "
    "steps (mindestens look, explain, Schreib-Schritt) und quiz (mindestens 4 Fachfragen).\n"
    "Sandbox learn (Reset: DROP SCHEMA learn CASCADE — Extra-Tabellen verschwinden):\n"
    "  clients      id, name, country (~4 Zeilen)\n"
    "  orders       id, order_number, client_id, client, status, quantity, note, created_at (~24 Zeilen)\n"
    "  stock        id, item, quantity, weight (~7 Zeilen)\n"
    "  order_items  id, order_id, sku, qty (~28 Zeilen)\n"
    "Zuerst `exercise_context` (Step-Schema, Live-Sandbox, Beispiel, Ziel-URL). "
    "Tabellenzeilen für look/predict: `table_rows`. IDs: `run_sql` mit as_ids. "
    "Prüfen mit `validate_exercise`, speichern mit `save_practice`. "
    "`draft_exercise` ist nur ein Gerüst — nicht unverändert speichern. "
    "Step-Typen im Detail: `step_schema`. "
    "Vorbild über `get_lesson` (ch8 oder challenge-2). "
    "Alte Übungen entfernen über `delete_practice` (eine id oder eine Liste).\n"
    "Gespeicherte Übungen erscheinen im SQL-Playground unter /playground/{id} "
    "(eine aktive Installation; save_practice prüft, ob die laufende App die Datei liest).\n"
    "Hints und teach helfen, sind aber nicht die volle Lösung. Quiz fragt das SQL-Thema, nicht das MCP. "
    "Offizielle PATH_IDS nicht überschreiben."
)

MINIMAL_LESSON = {
    "id": "ws-beispiel-offen",
    "title": "Offene Aufträge finden",
    "goal": "Du filterst Aufträge mit WHERE auf einen Status.",
    "minutes": 8,
    "concepts": ["SELECT", "WHERE"],
    "model": ["SELECT", "FROM", "WHERE"],
    "steps": [
        {
            "type": "look",
            "title": "Die Auftragsliste",
            "text": "Jede Zeile ist ein Auftrag. Offene erkennst du an status = 'offen'.",
            "table": {
                "name": "orders",
                "label": "Aufträge",
                "columns": ["id", "order_number", "client", "status"],
                "rows": [
                    {"id": 1, "order_number": 4711, "client": "Helio", "status": "offen"},
                    {"id": 2, "order_number": 4712, "client": "Alpin", "status": "fertig"},
                    {"id": 3, "order_number": 4713, "client": "Helio", "status": "offen"},
                ],
            },
            "cta": "SQL verstehen",
        },
        {
            "type": "explain",
            "title": "WHERE in Alltagssprache",
            "text": "Tippe die Satzteile an. Jeder Teil beantwortet eine Frage.",
            "sql": "SELECT id, status\nFROM orders\nWHERE status = 'offen'\nORDER BY id;",
            "plain": "Zeige id und status aus den Aufträgen, nur wo der Status offen ist, sortiert nach id.",
            "parts": [
                {
                    "match": "SELECT id, status",
                    "token": "SELECT",
                    "question": "Was möchte ich sehen?",
                    "answer": "Nur id und status — nicht die ganze Zeile.",
                },
                {
                    "match": "FROM orders",
                    "token": "FROM",
                    "question": "Woher kommen die Daten?",
                    "answer": "Aus der Auftragstabelle `orders`.",
                },
                {
                    "match": "WHERE status = 'offen'",
                    "token": "WHERE",
                    "question": "Welche Zeilen bleiben?",
                    "answer": "Nur Aufträge, deren Status genau offen ist. Text in Anführungszeichen.",
                },
                {
                    "match": "ORDER BY id",
                    "token": "ORDER BY",
                    "question": "In welcher Reihenfolge?",
                    "answer": "Aufsteigend nach id, damit das Ergebnis stabil vergleichbar ist.",
                },
            ],
            "concepts": ["SELECT", "WHERE"],
        },
        {
            "type": "predict",
            "title": "Welche Zeilen bleiben?",
            "text": "Markiere die Zeilen, die WHERE status = 'offen' behält.",
            "sql": "SELECT id, order_number, client, status FROM orders WHERE status = 'offen' ORDER BY id;",
            "table": {
                "name": "orders",
                "label": "Aufträge",
                "columns": ["id", "order_number", "client", "status"],
                "rows": [
                    {"id": 1, "order_number": 4711, "client": "Helio", "status": "offen"},
                    {"id": 2, "order_number": 4712, "client": "Alpin", "status": "fertig"},
                    {"id": 3, "order_number": 4713, "client": "Helio", "status": "offen"},
                ],
            },
            "id_field": "id",
            "execute": True,
            "feedback_ok": "Nur offene Aufträge bleiben.",
            "feedback_bad": "fertig fällt durch WHERE raus.",
        },
        {
            "type": "write",
            "title": "Schreib die Abfrage",
            "prompt": "Liste id und status aller offenen Aufträge, sortiert nach id.",
            "placeholder": "SELECT …",
            "solution": "SELECT id, status FROM orders WHERE status = 'offen' ORDER BY id;",
            "hints": [
                "Tabelle orders, Filter status = 'offen'.",
                "ORDER BY id — die Prüfung achtet auf die Reihenfolge.",
            ],
            "concepts": ["SELECT", "WHERE"],
            "strict_columns": True,
            "ordered": True,
            "teach": (
                "`WHERE` filtert Zeilen. Nur Datensätze, für die die Bedingung wahr ist, bleiben. "
                "Text steht in einfachen Anführungszeichen: status = 'offen'. "
                "SELECT wählt danach die Spalten, ORDER BY die Reihenfolge."
            ),
        },
    ],
    "quiz": [
        {
            "q": "Was macht WHERE?",
            "options": ["Spalten wählen", "Zeilen filtern", "Sortieren", "Tabellen verbinden"],
            "correct": 1,
            "explain": "WHERE entscheidet, welche Zeilen übrig bleiben.",
        },
        {
            "q": "Warum ORDER BY, wenn ordered true ist?",
            "options": [
                "Postgres verlangt es immer.",
                "Die Prüfung vergleicht dann die Reihenfolge.",
                "WHERE sortiert selbst.",
                "Es ersetzt SELECT.",
            ],
            "correct": 1,
            "explain": "ordered: true macht die Bewertung sortierungssensitiv.",
        },
        {
            "q": "Was passiert mit status = 'fertig'?",
            "options": [
                "Die Zeile bleibt.",
                "Die Zeile fällt durch WHERE raus.",
                "Sie wird NULL.",
                "Ein Fehler.",
            ],
            "correct": 1,
            "explain": "Der Filter behält nur 'offen'.",
        },
        {
            "q": "Woran merkst du, dass die Abfrage stimmt?",
            "options": [
                "Der Text ist identisch mit der Musterlösung.",
                "Das Ergebnis passt zur gestellten Frage.",
                "Die Abfrage enthält SELECT *.",
                "Es gibt kein WHERE.",
            ],
            "correct": 1,
            "explain": "Die App vergleicht das Ergebnis, nicht den Wortlaut.",
        },
    ],
}


def sandbox_sql(sql, allow_write=False, as_ids=None):
    """Patch point for tests — talks to Postgres, not Flask."""
    return run_sql(sql, allow_write=allow_write, as_ids=as_ids)


def sandbox_schema():
    return fetch_schema()


def sandbox_table(table, columns=None, where=None):
    return table_block(table, columns=columns, where=where)


def _ok_text(payload) -> dict:
    if isinstance(payload, dict):
        payload = dict(payload)
        payload.setdefault("build", BUILD)
    elif isinstance(payload, list):
        payload = {"items": payload, "build": BUILD}
    text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, indent=2)
    return {"content": [{"type": "text", "text": text}]}


def _err(message: str, extra: dict | None = None) -> dict:
    if extra is not None:
        payload = dict(extra)
        payload["error"] = message
        payload.setdefault("build", BUILD)
        text = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        text = f"{message}\nbuild = {BUILD}"
    return {"content": [{"type": "text", "text": text}], "isError": True}


def pid_alive(pid) -> bool:
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def http_get(url: str, timeout: float = 2.0):
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.geturl()
    except urllib.error.HTTPError as exc:
        return int(exc.code), url
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


def _read_runtime(home: Path) -> dict | None:
    path = Path(home) / "runtime.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def candidate_homes() -> list[Path]:
    homes: list[Path] = []
    env = (os.environ.get("LEARN_SQL_HOME") or "").strip()
    if env:
        base = Path(env).expanduser()
        homes.append(base)
        nested = base / base.name
        if nested.is_dir():
            homes.append(nested)
    homes.append(ROOT)
    unique = []
    seen = set()
    for home in homes:
        try:
            key = str(home.resolve())
        except OSError:
            key = str(home)
        if key in seen:
            continue
        seen.add(key)
        unique.append(home)
    return unique


def live_install() -> dict | None:
    """Home + runtime of a Flask that is actually up. None if unknown."""
    ranked = []
    for home in candidate_homes():
        rt = _read_runtime(home)
        if not rt:
            continue
        port = rt.get("appPort") or rt.get("app_port")
        pid = rt.get("flaskPid") or rt.get("flask_pid")
        alive = pid_alive(pid)
        url = f"http://127.0.0.1:{port}" if port else None
        http_ok = False
        if url:
            status, _final = http_get(url)
            http_ok = status is not None and int(status) < 500
        ranked.append({
            "home": str(home),
            "workshop_dir": str(Path(home) / "workshop"),
            "runtime_path": str(Path(home) / "runtime.json"),
            "flaskPid": pid,
            "appPort": port,
            "pid_alive": alive,
            "http_ok": http_ok,
            "app_url": url,
        })
    live = [row for row in ranked if row["pid_alive"] or row["http_ok"]]
    if live:
        live.sort(key=lambda r: (not r["pid_alive"], not r["http_ok"]))
        return live[0]
    return ranked[0] if ranked else None


def resolve_workshop() -> dict:
    live = live_install()
    env_dir = os.environ.get("WORKSHOP_DIR")
    env_home = os.environ.get("LEARN_SQL_HOME")
    if live and (live.get("pid_alive") or live.get("http_ok")):
        return {
            **live,
            "source": "live-runtime",
            "env_workshop": env_dir,
            "env_home": env_home,
        }
    folder = Path(env_dir) if env_dir else workshop_dir()
    return {
        "home": str(Path(env_home).expanduser()) if env_home else str(ROOT),
        "workshop_dir": str(folder),
        "runtime_path": None,
        "flaskPid": None,
        "appPort": None,
        "pid_alive": False,
        "http_ok": False,
        "app_url": None,
        "source": "env" if env_dir else "default",
        "env_workshop": env_dir,
        "env_home": env_home,
    }


def environment_report(prefix: str, exc: BaseException | None = None) -> str:
    app_py = APP / "app.py"
    lessons_py = APP / "lessons" / "academy_data.py"
    learn_db_py = APP / "learn_db.py"
    env_home = os.environ.get("LEARN_SQL_HOME") or "(nicht gesetzt)"
    target = resolve_workshop()
    lines = [prefix]
    if exc is not None:
        name = getattr(exc, "name", "") or ""
        if isinstance(exc, ModuleNotFoundError) and (
            name == "app" or "named 'app'" in str(exc)
        ):
            lines.append("App-Modul nicht importierbar.")
        else:
            lines.append(f"{type(exc).__name__}: {exc}")
    lines.append(f"  LEARN_SQL_HOME = {env_home}")
    lines.append(f"  MCP_ROOT       = {ROOT}")
    lines.append(f"  erwartet       = {app_py}  → {'ok' if app_py.is_file() else 'fehlt'}")
    lines.append(f"  lessons        = {lessons_py}  → {'ok' if lessons_py.is_file() else 'fehlt'}")
    lines.append(f"  learn_db       = {learn_db_py}  → {'ok' if learn_db_py.is_file() else 'fehlt'}")
    lines.append(f"  WORKSHOP_DIR   = {target.get('workshop_dir')}")
    lines.append(f"  DB             = {describe_target()}")
    if target.get("app_url"):
        state = "lebt" if target.get("pid_alive") or target.get("http_ok") else "antwortet nicht"
        lines.append(
            f"  Flask          = {target['app_url']} "
            f"(PID {target.get('flaskPid')}, {state})"
        )
        env_home_raw = os.environ.get("LEARN_SQL_HOME")
        if env_home_raw and target.get("home"):
            try:
                if Path(env_home_raw).resolve() != Path(target["home"]).resolve():
                    lines.append(
                        f"  laufendes Home = {target['home']}  → Installation inkonsistent. "
                        "Konfiguration prüfen."
                    )
            except OSError:
                pass
    else:
        lines.append("  Flask          = keine runtime.json mit appPort")
    if not (APP / "app.py").is_file():
        lines.append("  → App-Dateien fehlen unter MCP_ROOT. Falsche Installation geladen?")
    return "\n".join(lines)


def _looks_like_connect_error(text: str) -> bool:
    t = (text or "").lower()
    needles = (
        "timeout expired",
        "could not connect",
        "connection refused",
        "connection to server",
        "no module named",
        "name or service not known",
        "temporär nicht verfügbar",
        "failed to resolve",
    )
    return any(n in t for n in needles)


def _sql_payload_or_err(result: dict, prefix: str):
    if result.get("ok"):
        return _ok_text(result)
    blob = " ".join(str(result.get(k) or "") for k in ("error", "pg_error"))
    if _looks_like_connect_error(blob):
        return _err(
            environment_report(f"{prefix}: {result.get('error') or 'keine Verbindung'}")
        )
    return _ok_text(result)


def tool_schema(_args):
    try:
        result = sandbox_schema()
    except Exception as exc:  # noqa: BLE001
        return _err(environment_report("Schema nicht erreichbar.", exc))
    return _sql_payload_or_err(result, "Schema nicht erreichbar")


def tool_sample_rows(args):
    table = str(args.get("table") or "orders")
    try:
        result = sandbox_table(table)
    except Exception as exc:  # noqa: BLE001
        return _err(environment_report("Vorschau fehlgeschlagen.", exc))
    if not result.get("ok"):
        return _sql_payload_or_err(result, "Vorschau fehlgeschlagen")
    return _ok_text({
        "ok": True,
        "columns": result.get("columns"),
        "rows": (result.get("rows") or [])[:8],
        "name": result.get("name"),
        "label": result.get("label"),
        "sql": f"SELECT * FROM learn.{table} LIMIT 8",
        "note": "Für den Step-table-Block table_rows verwenden — das ist copy-paste-fertig.",
    })


def tool_run_sql(args):
    sql = str(args.get("sql") or "")
    if not sql.strip():
        return _err("sql fehlt.")
    as_ids = args.get("as_ids")
    if as_ids is True:
        as_ids = "id"
    elif as_ids is False:
        as_ids = None
    elif as_ids is not None:
        as_ids = str(as_ids).strip() or None
    try:
        result = sandbox_sql(sql, allow_write=False, as_ids=as_ids)
    except Exception as exc:  # noqa: BLE001
        return _err(environment_report("SQL fehlgeschlagen.", exc))
    return _sql_payload_or_err(result, "SQL fehlgeschlagen")


def tool_table_rows(args):
    table = str(args.get("table") or "").strip()
    if not table:
        return _err("table fehlt.")
    try:
        result = sandbox_table(table, columns=args.get("columns"), where=args.get("where"))
    except Exception as exc:  # noqa: BLE001
        return _err(environment_report("table_rows fehlgeschlagen.", exc))
    if not result.get("ok"):
        return _sql_payload_or_err(result, "table_rows fehlgeschlagen")
    return _ok_text({
        "name": result.get("name"),
        "label": result.get("label"),
        "columns": result.get("columns"),
        "rows": result.get("rows"),
    })


def tool_search_wissen(args):
    q = (args.get("q") or "").strip().lower()
    if len(q) < 2:
        return _err("q braucht mindestens zwei Zeichen.")
    hits = []
    for art in ARTICLES:
        hay = " ".join([art["title"], art["summary"], art["body"]]).lower()
        if q in hay:
            hits.append({
                "slug": art["slug"],
                "title": art["title"],
                "section": art["section_label"],
                "summary": art["summary"],
            })
        if len(hits) >= 12:
            break
    return _ok_text({"results": hits})


def tool_get_article(args):
    art = article_by_slug(str(args.get("slug") or ""))
    if not art:
        return _err("Artikel nicht gefunden.")
    return _ok_text({
        "slug": art["slug"],
        "title": art["title"],
        "section": art["section_label"],
        "summary": art["summary"],
        "body": art["body"],
        "sql": art["sql"],
        "pitfalls": art["pitfalls"],
        "lesson_id": art.get("lesson_id"),
    })


def tool_list_lessons(_args):
    rows = [
        {"id": l["id"], "title": l["title"], "chapter": l.get("chapter"), "goal": l.get("goal")}
        for l in ACADEMY["lessons"]
    ]
    extra = [
        {"id": l["id"], "title": l["title"], "chapter": "W", "goal": l.get("goal")}
        for l in workshop_lessons()
    ]
    return _ok_text({"path": rows, "workshop": extra})


def _step_schema_payload():
    return {
        "ablauf": "anschauen → verstehen (explain) → vorhersagen → selbst schreiben → Kurzcheck",
        "rule": (
            "Inhalt selbst ausdenken, Form wie der Lernpfad. "
            "Pflicht: look, explain (plain+parts), Schreib-Schritt mit teach. "
            "Roh-Entwurf von draft_exercise nicht unverändert speichern."
        ),
        "lesson_fields": LESSON_ENVELOPE,
        "sequence": [
            {"phase": "anschauen", "types": ["look", "inspect"], "why": "Daten und Frage zeigen, bevor jemand SQL schreibt."},
            {"phase": "verstehen", "types": ["explain", "demo", "predict", "predict-cols"], "why": "SQL vorhersagen oder erklären, nicht nur abtippen."},
            {"phase": "schreiben", "types": ["build", "fill", "write", "apply", "challenge"], "why": "Selbst formulieren, dann übertragen."},
            {"phase": "kurzcheck", "types": ["mcq"], "why": "Quiz-Tab: vier Fachfragen, kein MCP."},
        ],
        "types": STEP_TYPES,
        "fields": {
            name: {
                "required": spec["required"],
                "optional": spec["optional"],
            }
            for name, spec in STEP_SPECS.items()
        },
        "field_semantics": FIELD_SEMANTICS,
        "table": TABLE_SHAPE,
        "quiz_item": {"q": "Frage", "options": ["A", "B", "C", "D"], "correct": 1, "explain": "Warum"},
        "hints": "Mindestens zwei. Der letzte Hint ist nicht die volle Lösung.",
        "geruest": _draft_payload({
            "id": "ws-beispiel",
            "title": "Offene zählen",
            "prompt": "Wie viele offene Aufträge gibt es? Nur die Anzahl.",
            "solution": "SELECT COUNT(*) FROM orders WHERE status = 'offen';",
            "concepts": ["GROUP BY"],
        }),
        "minimal_valid": MINIMAL_LESSON,
        "id_prefix": "ws-",
        "path_ids": list(PATH_IDS),
        "note": (
            "Offizielle PATH_IDS nicht überschreiben. Speichern nur über save_practice. "
            "Vorbild: get_lesson mit ch8 oder challenge-2. "
            + RESET_NOTE
        ),
    }


def tool_step_schema(_args):
    return _ok_text(_step_schema_payload())


def _live_sandbox():
    try:
        result = sandbox_schema()
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": str(exc),
            "tables": CORE_SANDBOX,
            "source": "fallback-core",
        }
    if result.get("ok"):
        tables = []
        for tbl in result.get("tables") or []:
            tables.append({
                "name": tbl.get("name"),
                "label": tbl.get("label"),
                "row_count": tbl.get("row_count"),
                "columns": [c.get("name") for c in (tbl.get("columns") or [])],
            })
        return {"ok": True, "tables": tables, "source": "live"}
    return {
        "ok": False,
        "error": result.get("error"),
        "tables": CORE_SANDBOX,
        "source": "fallback-core",
    }


def tool_exercise_context(args):
    example_id = str(args.get("example") or "challenge-2").strip()
    example = lesson_by_id(example_id) or workshop_by_id(example_id)
    target = resolve_workshop()
    return _ok_text({
        "ablauf": "exercise_context → table_rows → run_sql(as_ids) → validate_exercise → save_practice",
        "terminology": {
            "name": "SQL-Playground",
            "url_prefix": "/playground/",
            "tool": "save_practice",
            "folder": "workshop",
            "legacy_redirect": "/werkstatt/ → /playground/",
        },
        "step_types": STEP_SPECS,
        "field_semantics": FIELD_SEMANTICS,
        "table": TABLE_SHAPE,
        "lesson_envelope": LESSON_ENVELOPE,
        "sandbox": _live_sandbox(),
        "core_sandbox": CORE_SANDBOX,
        "reset": RESET_NOTE,
        "path_ids": list(PATH_IDS),
        "workshop": {
            "dir": target.get("workshop_dir"),
            "app_url": target.get("app_url"),
            "source": target.get("source"),
            "pid_alive": target.get("pid_alive"),
        },
        "example_id": example_id,
        "example_lesson": example,
        "minimal_valid": MINIMAL_LESSON,
        "tools": [
            "exercise_context", "table_rows", "run_sql", "validate_exercise",
            "save_practice", "get_lesson", "draft_exercise", "delete_practice",
            "step_schema", "list_workshop",
        ],
        "buddy_tools": [
            "buddy_context", "help_with", "search_path", "coach_sql",
            "get_lesson", "search_wissen", "get_article",
        ],
    })


def tool_get_lesson(args):
    lid = str(args.get("id") or "").strip()
    if not lid:
        return _err("id fehlt. Offizielle IDs über list_lessons, zum Beispiel ch8 oder challenge-2.")
    lesson = lesson_by_id(lid) or workshop_by_id(lid)
    if not lesson:
        return _err(f"Übung {lid} nicht gefunden.")
    return _ok_text(enrich_lesson(lesson))


def _topic_quiz(concepts, prompt):
    topic = (concepts[0] if concepts else "SELECT")
    return [
        {
            "q": f"Was leistet {topic} in dieser Übung?",
            "options": [
                "Es sortiert nur die Ausgabe.",
                f"Es hilft, die Frage zu beantworten: {prompt}",
                "Es ersetzt FROM.",
                "Es löscht Zeilen.",
            ],
            "correct": 1,
            "explain": f"{topic} ist das Werkzeug für genau diese Lagerfrage.",
        },
        {
            "q": "Was filtert WHERE?",
            "options": [
                "Die Spalten in der Ausgabe.",
                "Die Zeilen, die übrig bleiben.",
                "Die Sortierreihenfolge.",
                "Den Namen der Tabelle.",
            ],
            "correct": 1,
            "explain": "WHERE entscheidet, welche Zeilen bleiben. SELECT entscheidet, welche Spalten du siehst.",
        },
        {
            "q": "Wann brauchst du GROUP BY?",
            "options": [
                "Immer, sobald ein WHERE steht.",
                "Wenn du eine Zahl oder Summe pro Gruppe willst, nicht eine Zeile pro Auftrag.",
                "Nur beim JOIN.",
                "Statt ORDER BY.",
            ],
            "correct": 1,
            "explain": "GROUP BY fasst gleichartige Zeilen zusammen, danach zählst oder summierst du.",
        },
        {
            "q": "Woran merkst du, dass die Abfrage stimmt?",
            "options": [
                "Der Text ist identisch mit der Musterlösung.",
                "Das Ergebnis passt zur gestellten Frage.",
                "Die Abfrage enthält SELECT *.",
                "Es gibt kein WHERE.",
            ],
            "correct": 1,
            "explain": "Die App vergleicht das Ergebnis, nicht den Wortlaut.",
        },
    ]


def _draft_payload(args) -> dict:
    lid = str(args.get("id") or "ws-draft")
    title = str(args.get("title") or "Playground-Übung")
    prompt = str(args.get("prompt") or "Schreibe die Abfrage.")
    solution = str(args.get("solution") or "SELECT * FROM orders;")
    look = str(args.get("look") or prompt)
    concepts = args.get("concepts") or ["SELECT"]
    hints = args.get("hints") or [
        "Welche Tabelle, welche Spalten, welcher Filter?",
        "Vergleich das Ergebnis mit der Frage, nicht mit einem auswendig gelernten Satz.",
    ]
    apply_prompt = args.get("apply") or f"Gleiche Idee, leicht versetzt: {prompt}"
    taught = str(args.get("teach") or teach_for(concepts) or (
        "Zerlege die Frage: Welche Tabelle? Welche Spalten? Welche Zeilen? "
        "Schreib das als SELECT … FROM … WHERE …"
    ))
    plain, parts = explain_step_parts(solution)
    return {
        "id": lid,
        "title": title,
        "goal": args.get("goal") or "Eine zusätzliche Übung neben dem Pfad — Inhalt ersetzen, Form behalten.",
        "minutes": int(args.get("minutes") or 8),
        "concepts": concepts,
        "model": args.get("model") or ["SELECT", "FROM", "WHERE"],
        "steps": [
            {
                "type": "look",
                "title": "Die Frage",
                "text": look,
                "teach": taught,
                "cta": "SQL verstehen",
            },
            {
                "type": "explain",
                "title": "Die Query in Teilen",
                "text": "Tippe die Satzteile an. Ersetze die Standard-Erklärungen durch die Fachfrage dieser Übung.",
                "sql": solution,
                "plain": plain,
                "parts": parts,
                "concepts": concepts,
                "teach": taught,
            },
            {
                "type": "predict",
                "title": "Was bleibt übrig?",
                "text": "Markiere im Kopf, welche Zeilen die Abfrage behält — bevor du selbst schreibst.",
                "sql": solution,
                "feedback_ok": "Die passenden Zeilen bleiben.",
                "feedback_bad": "Schau nochmal auf Filter und Tabelle, nicht auf den ganzen Bestand.",
            },
            {
                "type": args.get("step_type") or "write",
                "title": title,
                "prompt": prompt,
                "placeholder": "SELECT …",
                "solution": solution,
                "hints": hints,
                "concepts": concepts,
                "teach": taught,
            },
            {
                "type": "apply",
                "title": "Noch einmal, leicht anders",
                "prompt": apply_prompt,
                "placeholder": "SELECT …",
                "solution": solution,
                "hints": hints,
                "concepts": concepts,
                "teach": taught,
            },
        ],
        "quiz": args.get("quiz") or _topic_quiz(concepts, prompt),
    }


def tool_draft_exercise(args):
    return _ok_text(_draft_payload(args))


def _ids_equal(left, right) -> bool:
    def norm(seq):
        return ["" if v is None else str(v) for v in (seq or [])]
    return norm(left) == norm(right)


def _row_cells(row: dict, columns: list[str]) -> dict:
    return {c: row.get(c) for c in columns}


def _embedded_tables(step: dict) -> list[dict]:
    if isinstance(step.get("tables"), list) and step["tables"]:
        return [t for t in step["tables"] if isinstance(t, dict)]
    if isinstance(step.get("table"), dict):
        return [step["table"]]
    return []


def _sql_fields(step: dict) -> list[tuple[str, str]]:
    found = []
    for key in ("sql", "solution", "verify"):
        raw = step.get(key)
        if isinstance(raw, str) and raw.strip():
            found.append((key, raw))
    return found


def validate_lesson(lesson: dict, *, fill_ids: bool = False) -> dict:
    """Structural + optional SQL checks. Mutates a copy when fill_ids is True."""
    data = copy.deepcopy(lesson) if fill_ids else lesson
    errors = []
    warnings = []
    steps_out = []
    sql_checked = True

    lid = str(data.get("id") or "").strip()
    if not SAFE_ID.match(lid):
        errors.append("id muss wie ws-having-1 aussehen (Buchstaben, Zahlen, Bindestrich).")
    elif lid in PATH_IDS:
        errors.append(f"{lid} ist eine offizielle PATH_ID und darf nicht überschrieben werden.")

    steps = data.get("steps") or []
    if not isinstance(steps, list) or len(steps) < 3:
        errors.append("steps: mindestens 3 Schritte.")
    elif all(str((s or {}).get("type") or "") == "look" for s in steps):
        errors.append("steps: nicht nur look — es braucht verstehen/schreiben.")
    if isinstance(steps, list):
        types = [str((s or {}).get("type") or "") for s in steps if isinstance(s, dict)]
        if "explain" not in types:
            errors.append(
                "steps: mindestens ein explain-Schritt mit Alltagssprache (plain) "
                "und antippenbaren SQL-Teilen (parts)."
            )
        if not any(t in {"write", "apply", "challenge", "build", "fill"} for t in types):
            errors.append(
                "steps: mindestens ein Schreib-Schritt (write/apply/challenge/build/fill) mit teach."
            )

    quiz = data.get("quiz") or []
    if not isinstance(quiz, list) or len(quiz) < 4:
        errors.append("quiz: mindestens 4 Fachfragen.")
    else:
        for qi, item in enumerate(quiz):
            if not isinstance(item, dict):
                errors.append(f"quiz[{qi}]: kein Objekt.")
                continue
            options = item.get("options") or []
            correct = item.get("correct")
            if not isinstance(correct, int) or correct < 0 or correct >= len(options):
                errors.append(
                    f"quiz[{qi}]: correct={correct} liegt außerhalb von 0..{max(0, len(options) - 1)}."
                )

    for idx, step in enumerate(steps):
        info = {"index": idx, "type": None, "ok": True, "notes": []}
        if not isinstance(step, dict):
            errors.append(f"steps[{idx}]: kein Objekt.")
            info["ok"] = False
            steps_out.append(info)
            continue
        stype = str(step.get("type") or "")
        info["type"] = stype
        if stype not in STEP_TYPES:
            errors.append(
                f"steps[{idx}]: unbekannter type {stype!r}. Erlaubt: {', '.join(STEP_TYPES)}."
            )
            info["ok"] = False
            steps_out.append(info)
            continue
        spec = STEP_SPECS[stype]
        missing = [f for f in spec["required"] if step.get(f) in (None, "", [])]
        if missing:
            errors.append(f"steps[{idx}] ({stype}): Pflichtfelder fehlen: {', '.join(missing)}.")
            info["ok"] = False

        if stype == "explain":
            plain = str(step.get("plain") or "").strip()
            parts = step.get("parts") if isinstance(step.get("parts"), list) else []
            if len(plain) < 40:
                errors.append(
                    f"steps[{idx}] (explain): plain muss die Query in einem Satz erklären."
                )
                info["ok"] = False
            if len(parts) < 2:
                errors.append(
                    f"steps[{idx}] (explain): parts braucht mindestens zwei SQL-Teile zum Antippen."
                )
                info["ok"] = False
            else:
                for pi, part in enumerate(parts):
                    if not isinstance(part, dict):
                        errors.append(f"steps[{idx}].parts[{pi}]: kein Objekt.")
                        info["ok"] = False
                        continue
                    missing_part = [
                        key for key in ("token", "match", "question", "answer")
                        if not str(part.get(key) or "").strip()
                    ]
                    if missing_part:
                        errors.append(
                            f"steps[{idx}].parts[{pi}]: es fehlen {', '.join(missing_part)}."
                        )
                        info["ok"] = False
                    elif len(str(part.get("answer") or "").strip()) < 20:
                        errors.append(
                            f"steps[{idx}].parts[{pi}]: answer muss den Teil wirklich erklären."
                        )
                        info["ok"] = False

        if stype in {"write", "apply", "challenge", "build", "fill"}:
            taught = str(step.get("teach") or "").strip()
            if len(taught) < 40:
                errors.append(
                    f"steps[{idx}] ({stype}): teach muss erklären, WARUM die Query so gebaut wird "
                    "— nicht nur die Aufgabe und nicht die volle Lösung."
                )
                info["ok"] = False

        for key, sql in _sql_fields(step):
            try:
                result = sandbox_sql(sql, allow_write=False)
            except Exception as exc:  # noqa: BLE001
                sql_checked = False
                warnings.append(f"steps[{idx}].{key}: SQL nicht prüfbar ({exc}).")
                info["notes"].append("sql_skipped")
                continue
            if not result.get("ok") and _looks_like_connect_error(
                " ".join(str(result.get(k) or "") for k in ("error", "pg_error"))
            ):
                sql_checked = False
                warnings.append(f"steps[{idx}].{key}: Datenbank nicht erreichbar.")
                info["notes"].append("sql_skipped")
                continue
            if not result.get("ok"):
                errors.append(f"steps[{idx}].{key}: {result.get('error') or 'SQL fehlgeschlagen'}.")
                info["ok"] = False
            else:
                info["notes"].append(f"{key}_ok")
                info[f"{key}_columns"] = result.get("columns")
                info[f"{key}_row_count"] = len(result.get("rows") or [])

            if stype == "predict" and key == "sql" and result.get("ok"):
                id_field = str(step.get("id_field") or "id")
                id_result = sandbox_sql(sql, allow_write=False, as_ids=id_field)
                if id_result.get("ok"):
                    actual = id_result.get("ids") or []
                    expected = step.get("expected_ids")
                    if expected is None:
                        if fill_ids:
                            step["expected_ids"] = actual
                            info["notes"].append("expected_ids_filled")
                        else:
                            warnings.append(
                                f"steps[{idx}]: expected_ids fehlt — wären {actual}."
                            )
                    elif not _ids_equal(expected, actual):
                        errors.append(
                            f"steps[{idx}]: expected_ids stimmen nicht. "
                            f"angegeben={list(expected)} richtig={actual}."
                        )
                        info["ok"] = False
                        info["actual_ids"] = actual
                        info["given_ids"] = list(expected)
                    else:
                        info["notes"].append("expected_ids_ok")
                        info["actual_ids"] = actual

        for table in _embedded_tables(step):
            name = str(table.get("name") or "").strip()
            cols = list(table.get("columns") or [])
            rows = list(table.get("rows") or [])
            if not name:
                errors.append(f"steps[{idx}]: table.name fehlt.")
                info["ok"] = False
                continue
            try:
                live = sandbox_table(name, columns=cols or None)
            except Exception as exc:  # noqa: BLE001
                sql_checked = False
                warnings.append(f"steps[{idx}].table: nicht prüfbar ({exc}).")
                continue
            if not live.get("ok"):
                if _looks_like_connect_error(str(live.get("error") or "")):
                    sql_checked = False
                    warnings.append(f"steps[{idx}].table: Datenbank nicht erreichbar.")
                else:
                    errors.append(f"steps[{idx}].table: {live.get('error')}.")
                    info["ok"] = False
                continue
            live_rows = live.get("rows") or []
            compare_cols = cols or list(live.get("columns") or [])
            if len(rows) != len(live_rows):
                errors.append(
                    f"steps[{idx}].table {name}: {len(rows)} Zeilen eingebettet, "
                    f"{len(live_rows)} in der DB."
                )
                info["ok"] = False
                continue
            diffs = []
            for i, (emb, dbrow) in enumerate(zip(rows, live_rows)):
                a = _row_cells(emb, compare_cols)
                b = _row_cells(dbrow, compare_cols)
                if a != b:
                    diffs.append({"index": i, "embedded": a, "db": b})
                if len(diffs) >= 5:
                    break
            if diffs:
                errors.append(f"steps[{idx}].table {name}: Zeilen weichen von der DB ab.")
                info["ok"] = False
                info["table_diffs"] = diffs
            else:
                info["notes"].append("table_ok")

        steps_out.append(info)

    if fill_ids:
        data["steps"] = steps
    return {
        "ok": not errors,
        "sql_checked": sql_checked,
        "errors": errors,
        "warnings": warnings,
        "steps": steps_out,
        "lesson": data if fill_ids else None,
        "id": lid,
    }


def _parse_lesson_args(args):
    data = args.get("lesson")
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as exc:
            return None, _err(f"lesson ist kein JSON: {exc}")
    if not data:
        data = _draft_payload(args)
    if not isinstance(data, dict):
        return None, _err("lesson muss ein Objekt sein.")
    return data, None


def tool_validate_exercise(args):
    data, err = _parse_lesson_args(args)
    if err:
        return err
    report = validate_lesson(data, fill_ids=True)
    payload = {
        "ok": report["ok"],
        "sql_checked": report["sql_checked"],
        "errors": report["errors"],
        "warnings": report["warnings"],
        "steps": report["steps"],
        "id": report["id"],
        "filled_expected_ids": bool(
            report.get("lesson")
            and any("expected_ids_filled" in (s.get("notes") or []) for s in report["steps"])
        ),
    }
    if not report["sql_checked"] and not report["errors"]:
        payload["ok"] = False
        payload["errors"] = [
            environment_report("validate_exercise: SQL nicht prüfbar. Datenbank prüfen.")
        ]
        return _err(payload["errors"][0], extra=payload)
    if not report["ok"]:
        return _err("Übung ist ungültig.", extra=payload)
    return _ok_text(payload)


def _absolute_url(app_url: str | None, lid: str) -> str:
    path = f"/playground/{lid}"
    if app_url:
        return app_url.rstrip("/") + path
    return path


def tool_save_practice(args):
    data, err = _parse_lesson_args(args)
    if err:
        return err
    report = validate_lesson(data, fill_ids=True)
    if report["errors"]:
        return _err("Übung nicht gespeichert — validate_exercise ist rot.", extra={
            "ok": False,
            "errors": report["errors"],
            "warnings": report["warnings"],
            "steps": report["steps"],
        })
    data = report["lesson"] or data
    target = resolve_workshop()
    folder = Path(target["workshop_dir"])
    try:
        path = save_workshop_lesson(data, folder=folder)
    except ValueError as exc:
        return _err(str(exc))
    lid = str(data.get("id") or "")
    url = _absolute_url(target.get("app_url"), lid)
    reachable = None
    http_status = None
    if target.get("app_url") and (target.get("pid_alive") or target.get("http_ok") or target.get("appPort")):
        http_status, _final = http_get(url)
        reachable = http_status == 200
        if not reachable:
            return _err(
                "Übung gespeichert, aber die laufende App liest sie nicht. "
                f"geschrieben = {path}  "
                f"App = {target.get('app_url')} (PID {target.get('flaskPid')})  "
                f"HTTP = {http_status!r}  "
                f"workshop der App = {target.get('workshop_dir')}  "
                f"LEARN_SQL_HOME = {os.environ.get('LEARN_SQL_HOME') or '(nicht gesetzt)'}. "
                "Installation inkonsistent — die Datei liegt nicht dort, wo Flask liest.",
                extra={
                    "saved": str(path),
                    "id": lid,
                    "url": url,
                    "reachable": False,
                    "http_status": http_status,
                    "workshop_dir": str(folder),
                    "app_url": target.get("app_url"),
                    "flaskPid": target.get("flaskPid"),
                },
            )
    return _ok_text({
        "saved": str(path),
        "id": lid,
        "url": url,
        "reachable": reachable,
        "http_status": http_status,
        "workshop_dir": str(folder),
        "app_url": target.get("app_url"),
        "sql_checked": report["sql_checked"],
        "warnings": report["warnings"],
    })


def tool_list_workshop(_args):
    return _ok_text({
        "exercises": [
            {"id": l["id"], "title": l["title"], "steps": len(l.get("steps") or [])}
            for l in workshop_lessons()
        ]
    })


def tool_delete_practice(args):
    raw = args.get("id")
    if raw is None:
        raw = args.get("ids")
    if isinstance(raw, str):
        ids = [raw]
    elif isinstance(raw, list):
        ids = [str(item) for item in raw]
    else:
        return _err("id fehlt (eine ws-…-id oder eine Liste).")
    deleted = []
    missing = []
    errors = []
    for lid in ids:
        lid = str(lid).strip()
        if not lid:
            continue
        try:
            if delete_workshop_lesson(lid):
                deleted.append(lid)
            else:
                missing.append(lid)
        except ValueError as exc:
            errors.append({"id": lid, "error": str(exc)})
    if not deleted and not missing and not errors:
        return _err("id fehlt (eine ws-…-id oder eine Liste).")
    return _ok_text({"deleted": deleted, "missing": missing, "errors": errors})


def tool_list_cards(args):
    topic = str(args.get("topic") or "")
    cards = knowledge_cards()
    if topic:
        cards = [c for c in cards if c.get("topic") == topic or c.get("slug") == topic]
    return _ok_text({"cards": cards[:40]})


def tool_buddy_context(_args):
    return _ok_text(buddy_snapshot())


def tool_search_path(args):
    q = str(args.get("q") or "").strip()
    if len(q) < 2:
        return _err("q braucht mindestens zwei Zeichen.")
    return _ok_text({"results": search_learning(q)})


def tool_help_with(args):
    q = str(args.get("q") or "").strip()
    if len(q) < 2:
        ctx = load_learner_context() or {}
        q = str(
            ctx.get("question") or ctx.get("step_title") or ctx.get("prompt") or ""
        ).strip()
    if len(q) < 2:
        return _err("q fehlt. Formuliere die Frage der Person.")
    return _ok_text(help_pack(
        q,
        lesson_id=args.get("lesson_id"),
        step=args.get("step"),
    ))


def tool_coach_sql(args):
    ctx = load_learner_context() or {}
    sql = str(args.get("sql") or ctx.get("last_sql") or "").strip()
    if not sql:
        return _err("sql fehlt.")
    lid = str(args.get("lesson_id") or ctx.get("lesson_id") or "").strip()
    idx = args.get("step")
    if idx is None:
        idx = ctx.get("step")
    lesson = resolve_lesson(lid)
    step = None
    if lesson:
        try:
            step = (lesson.get("steps") or [])[int(idx)]
        except (TypeError, ValueError, IndexError):
            step = None
        if not isinstance(step, dict):
            step = None
    solution = str((step or {}).get("solution") or "")
    reveal = bool(args.get("reveal_solution"))
    coach = diagnose_structure(sql, solution, step or {})
    explained = explain_sql(sql)
    try:
        result = sandbox_sql(sql, allow_write=False)
    except Exception as exc:  # noqa: BLE001
        return _err(environment_report("SQL fehlgeschlagen.", exc))
    if not result.get("ok") and _looks_like_connect_error(
        " ".join(str(result.get(k) or "") for k in ("error", "pg_error"))
    ):
        return _sql_payload_or_err(result, "SQL fehlgeschlagen")
    rows = result.get("rows") or []
    payload = {
        "ok": bool(result.get("ok")),
        "coach": coach or ctx.get("last_coach"),
        "plain": explained.get("plain"),
        "parts": [
            {
                "token": part.get("key"),
                "sql": part.get("sql"),
                "question": part.get("question"),
                "blurb": part.get("blurb"),
            }
            for part in (explained.get("parts") or [])
        ],
        "run": {
            "ok": bool(result.get("ok")),
            "error": result.get("error"),
            "columns": result.get("columns"),
            "row_count": len(rows),
            "rows": rows[:6],
        },
        "lesson_id": lid or None,
        "step": idx,
        "has_solution": bool(solution),
        "solution": solution if reveal else None,
        "how_to_answer": (
            "Sag, was an der Query hakt, anhand von SELECT/FROM/WHERE/JOIN. "
            "Die Musterlösung nur nennen, wenn reveal_solution true ist oder die Person sie verlangt."
        ),
    }
    if not result.get("ok"):
        payload["ok"] = True
        payload["run"]["ok"] = False
    return _ok_text(payload)


LESSON_OBJECT_SCHEMA = {
    "type": "object",
    "description": (
        "Vollständige Playground-Übung. Wenn gesetzt, werden id/title/prompt/solution ignoriert. "
        "Form: exercise_context / step_schema."
    ),
    "properties": {
        "id": {"type": "string", "description": "ws-… Slug, wird zu /playground/{id}."},
        "title": {"type": "string", "description": "Kurzer Titel wie ein Kapitel."},
        "goal": {"type": "string", "description": "Ein Satz: was die Person danach kann."},
        "minutes": {"type": "integer", "description": "Dauer in Minuten."},
        "concepts": {"type": "array", "items": {"type": "string"}},
        "model": {"type": "array", "items": {"type": "string"}},
        "steps": {
            "type": "array",
            "description": "Mindestens look, explain (plain+parts) und ein Schreib-Schritt mit teach.",
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": STEP_TYPES,
                        "description": "Schritttyp. Unbekannte Typen rendert das Frontend nicht.",
                    }
                },
            },
        },
        "quiz": {
            "type": "array",
            "description": "Mindestens 4 Fachfragen. correct ist 0-basiert.",
            "items": {"type": "object"},
        },
    },
}


def _table_names() -> list[str]:
    return [t["name"] for t in CORE_SANDBOX]


def _tools():
    tables = _table_names()
    table_desc = ", ".join(tables)
    sample_table = {
        "type": "string",
        "description": (
            f"Tabelle in learn, z.B. {table_desc}. "
            "Weitere Namen stehen in schema / exercise_context (kein festes Enum — Extra-Tabellen sind erlaubt)."
        ),
    }
    return {
        "schema": {
            "description": "Tabellen, Spalten und Zeilenzahlen im Schema learn (live).",
            "inputSchema": {"type": "object", "properties": {}},
            "fn": tool_schema,
        },
        "sample_rows": {
            "description": (
                f"Erste Zeilen einer learn-Tabelle ({table_desc}). "
                "Für den Step-table-Block lieber table_rows nutzen."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {"table": sample_table},
            },
            "fn": tool_sample_rows,
        },
        "table_rows": {
            "description": (
                "Zeilen einer learn-Tabelle im Step-table-Format "
                "{name, label, columns, rows} — copy-paste in look/predict."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "table": {**sample_table, "description": (
                        f"Tabellenname in learn, z.B. {table_desc}. "
                        "Live-Liste: schema oder exercise_context."
                    )},
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optionale Spaltenliste. Default: alle.",
                    },
                    "where": {
                        "type": "string",
                        "description": "Optionale WHERE-Klausel ohne das Wort WHERE, z.B. status = 'offen'.",
                    },
                },
                "required": ["table"],
            },
            "fn": tool_table_rows,
        },
        "run_sql": {
            "description": (
                "SELECT/WITH/EXPLAIN gegen learn, damit erwartete Ergebnisse stimmen. "
                "as_ids: Spaltenname — Antwort ist eine flache ID-Liste für expected_ids."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "Lesende Abfrage gegen learn."},
                    "as_ids": {
                        "description": (
                            "Spaltenname (z.B. id). Liefert ids: [1,3,4] statt Zeilenobjekte. "
                            "true steht für die Spalte id."
                        )
                    },
                },
                "required": ["sql"],
            },
            "fn": tool_run_sql,
        },
        "search_wissen": {
            "description": "Artikel der PostgreSQL-Bibel suchen.",
            "inputSchema": {
                "type": "object",
                "properties": {"q": {"type": "string"}},
                "required": ["q"],
            },
            "fn": tool_search_wissen,
        },
        "get_article": {
            "description": "Einen Bibel-Artikel vollständig lesen.",
            "inputSchema": {
                "type": "object",
                "properties": {"slug": {"type": "string"}},
                "required": ["slug"],
            },
            "fn": tool_get_article,
        },
        "list_lessons": {
            "description": "Offizielle Kapitel und SQL-Playground-Übungen (Lernpfad + Buddy).",
            "inputSchema": {"type": "object", "properties": {}},
            "fn": tool_list_lessons,
        },
        "exercise_context": {
            "description": (
                "Alles zum Schreiben einer Playground-Übung in einem Call: "
                "Step-Typen mit Pflicht/Optional und Feldsemantik, table-Struktur, "
                "Live-Sandbox, PATH_IDS, Reset, Ziel-URL, Beispiel-Lesson."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "example": {
                        "type": "string",
                        "description": "Vorbild-id, Standard challenge-2.",
                    }
                },
            },
            "fn": tool_exercise_context,
        },
        "step_schema": {
            "description": "Übungsdesign und JSON-Form der Schritte — vor dem Anlegen lesen.",
            "inputSchema": {"type": "object", "properties": {}},
            "fn": tool_step_schema,
        },
        "get_lesson": {
            "description": "Eine offizielle oder Playground-Übung als Vorbild laden (z.B. ch8).",
            "inputSchema": {
                "type": "object",
                "properties": {"id": {"type": "string", "description": "ch8, challenge-2 oder eine ws-…-id"}},
                "required": ["id"],
            },
            "fn": tool_get_lesson,
        },
        "draft_exercise": {
            "description": (
                "Entwurf im Übungsdesign (anschauen → verstehen → schreiben → Kurzcheck). "
                "Inhalt selbst wählen. Nicht unverändert speichern — validate_exercise nutzen."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "ws-… Slug für den Entwurf."},
                    "title": {"type": "string", "description": "Titel der Übung."},
                    "prompt": {"type": "string", "description": "Aufgabenstellung für den write-Step."},
                    "solution": {"type": "string", "description": "Muster-SQL."},
                    "goal": {"type": "string"},
                    "look": {"type": "string", "description": "Text für den look-Step."},
                    "hints": {"type": "array", "items": {"type": "string"}},
                    "concepts": {"type": "array", "items": {"type": "string"}},
                },
            },
            "fn": tool_draft_exercise,
        },
        "validate_exercise": {
            "description": (
                "Dry-Run: SQL, expected_ids, eingebettete table-Blöcke, id, PATH_IDS, "
                "Step-/Quiz-Mindestzahl. Schreibt nichts."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "lesson": LESSON_OBJECT_SCHEMA,
                    "id": {"type": "string", "description": "Nur wenn lesson fehlt: Draft-Felder wie bei save_practice."},
                    "title": {"type": "string"},
                    "prompt": {"type": "string"},
                    "solution": {"type": "string"},
                },
            },
            "fn": tool_validate_exercise,
        },
        "save_practice": {
            "description": (
                "Übung in den SQL-Playground schreiben (workshop/). "
                "Entweder vollständige lesson oder Draft-Felder id/title/prompt/solution — "
                "lesson gewinnt. Validiert intern. Erfolg nur, wenn die laufende App die URL sieht."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "lesson": LESSON_OBJECT_SCHEMA,
                    "id": {
                        "type": "string",
                        "description": "Nur ohne lesson: ws-… für den Draft. Wird ignoriert, wenn lesson gesetzt ist.",
                    },
                    "title": {
                        "type": "string",
                        "description": "Nur ohne lesson. Wird ignoriert, wenn lesson gesetzt ist.",
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Nur ohne lesson: Aufgabenstellung. Wird ignoriert, wenn lesson gesetzt ist.",
                    },
                    "solution": {
                        "type": "string",
                        "description": "Nur ohne lesson: Muster-SQL. Wird ignoriert, wenn lesson gesetzt ist.",
                    },
                },
            },
            "fn": tool_save_practice,
        },
        "list_workshop": {
            "description": "Gespeicherte SQL-Playground-Übungen.",
            "inputSchema": {"type": "object", "properties": {}},
            "fn": tool_list_workshop,
        },
        "delete_practice": {
            "description": "Eine oder mehrere Playground-Übungen löschen. id ist eine ws-…-id oder eine Liste. Offizielle Kapitel bleiben.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "id": {
                        "description": "Eine ws-…-id oder eine Liste von ids.",
                    },
                    "ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Mehrere ws-…-ids auf einmal.",
                    },
                },
            },
            "fn": tool_delete_practice,
        },
        "list_cards": {
            "description": "Karteikarten der Bibel, optional nach Thema (lesen, filtern, …).",
            "inputSchema": {
                "type": "object",
                "properties": {"topic": {"type": "string"}},
            },
            "fn": tool_list_cards,
        },
        "buddy_context": {
            "description": (
                "Standort der Person in der App (Kapitel, Schritt, letzte Query) "
                "plus offizieller Pfad. Zuerst lesen, bevor du als Lern-Buddy antwortest."
            ),
            "inputSchema": {"type": "object", "properties": {}},
            "fn": tool_buddy_context,
        },
        "search_path": {
            "description": "Offiziellen Lernpfad, Playground und Bibel durchsuchen.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "q": {"type": "string", "description": "Suchbegriff, z.B. LEFT JOIN oder NULL."},
                },
                "required": ["q"],
            },
            "fn": tool_search_path,
        },
        "help_with": {
            "description": (
                "Frage zum aktuellen (oder angegebenen) Kapitel beantworten: "
                "Konzepttext, passende Bibel-Artikel, Schritte — ohne Musterlösung."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "q": {"type": "string", "description": "Frage der lernenden Person."},
                    "lesson_id": {
                        "type": "string",
                        "description": "ch3, challenge-2 oder ws-… — sonst der Standort aus buddy_context.",
                    },
                    "step": {
                        "type": "integer",
                        "description": "0-basierter Schrittindex. Default: Standort aus buddy_context.",
                    },
                },
                "required": ["q"],
            },
            "fn": tool_help_with,
        },
        "coach_sql": {
            "description": (
                "SQL der Person gegen den aktuellen Schritt prüfen. "
                "Liefert Coach-Text und Alltags-Erklärung, nicht die Musterlösung "
                "(außer reveal_solution)."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "Query der Person. Default: last_sql aus buddy_context.",
                    },
                    "lesson_id": {"type": "string", "description": "Kapitel- oder Playground-id."},
                    "step": {"type": "integer", "description": "Schrittindex."},
                    "reveal_solution": {
                        "type": "boolean",
                        "description": "true nur wenn die Person die Musterlösung verlangt.",
                    },
                },
            },
            "fn": tool_coach_sql,
        },
    }


TOOLS = _tools()


def instruction_tool_names() -> list[str]:
    return sorted({
        name for name in re.findall(r"`([a-z][a-z0-9_]+)`", INSTRUCTIONS)
        if name in TOOLS
    })


def handle(msg: dict):
    mid = msg.get("id")
    method = msg.get("method")
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": mid,
            "result": {
                "protocolVersion": PROTOCOL,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "learnsql", "version": BUILD},
                "instructions": INSTRUCTIONS,
            },
        }
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        specs = _tools()
        tools = []
        for name, spec in specs.items():
            tools.append({
                "name": name,
                "description": spec["description"],
                "inputSchema": spec["inputSchema"],
            })
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": tools}}
    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        spec = _tools().get(name)
        if not spec:
            return {
                "jsonrpc": "2.0",
                "id": mid,
                "error": {"code": -32601, "message": f"Unbekanntes Werkzeug: {name}"},
            }
        result = spec["fn"](args)
        return {"jsonrpc": "2.0", "id": mid, "result": result}
    if method in {"ping", "notifications/cancelled"}:
        if mid is None:
            return None
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if mid is None:
        return None
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": method or "no method"}}


def _read_message(stdin=None):
    """Read one JSON-RPC message.

    Claude Desktop / Code send newline-delimited JSON (MCP stdio spec).
    Older LSP-style clients send Content-Length headers. A JSON line
    contains colons, so treating every colon as a header deadlocks
    initialize and Claude reports "Request timed out".
    """
    stream = stdin if stdin is not None else sys.stdin
    line = stream.readline()
    if line == "":
        return None, None
    if line.lower().startswith("content-length:"):
        headers = {"content-length": line.split(":", 1)[1].strip()}
        while True:
            rest = stream.readline()
            if rest == "":
                return None, None
            if rest in ("\r\n", "\n"):
                break
            if ":" in rest:
                key, value = rest.split(":", 1)
                headers[key.strip().lower()] = value.strip()
        length = int(headers.get("content-length") or "0")
        if length <= 0:
            return None, None
        body = stream.read(length)
        return json.loads(body), "lsp"
    stripped = line.strip()
    if not stripped:
        return _read_message(stream)
    return json.loads(stripped), "ndjson"


def _write_message(msg: dict, style: str = "ndjson", stdout=None):
    raw = json.dumps(msg, ensure_ascii=False)
    out = stdout if stdout is not None else sys.stdout
    if style == "lsp":
        data = raw.encode("utf-8")
        header = f"Content-Length: {len(data)}\r\n\r\n".encode("ascii")
        buffer = getattr(out, "buffer", None)
        if buffer is not None:
            buffer.write(header + data)
            buffer.flush()
        else:
            out.write(header.decode("ascii") + raw)
            out.flush()
        return
    out.write(raw + "\n")
    out.flush()


def _read_stdio():
    msg, _style = _read_message()
    return msg


def _write_stdio(msg: dict):
    _write_message(msg, "ndjson")


def main():
    if hasattr(sys.stdin, "reconfigure"):
        try:
            sys.stdin.reconfigure(encoding="utf-8")
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    while True:
        try:
            msg, style = _read_message()
        except Exception:  # noqa: BLE001
            return
        if msg is None:
            return
        reply = handle(msg)
        if reply is None:
            continue
        _write_message(reply, style or "ndjson")


if __name__ == "__main__":
    main()
