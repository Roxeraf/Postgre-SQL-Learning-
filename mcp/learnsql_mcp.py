#!/usr/bin/env python3
"""stdio MCP server: schema, Wissen, Übungen in die Werkstatt legen."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
sys.path.insert(0, str(APP))

os.environ.setdefault("DB_HOST", os.environ.get("DB_HOST", "127.0.0.1"))

from lessons.academy_data import ACADEMY  # noqa: E402
from lessons.knowledge import ARTICLES, article_by_slug, knowledge_cards  # noqa: E402
from lessons.workshop import save_workshop_lesson, workshop_lessons  # noqa: E402

PROTOCOL = "2024-11-05"

STEP_TYPES = [
    "look", "inspect", "explain", "demo", "predict", "predict-cols",
    "build", "fill", "write", "apply", "challenge", "mcq",
]


def _ok_text(payload) -> dict:
    text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, indent=2)
    return {"content": [{"type": "text", "text": text}]}


def _err(message: str) -> dict:
    return {"content": [{"type": "text", "text": message}], "isError": True}


def tool_schema(_args):
    try:
        import app as flask_app
        from flask import Flask
        client = flask_app.app.test_client() if isinstance(flask_app.app, Flask) else None
        if client:
            res = client.get("/api/schema")
            return _ok_text(res.get_json())
    except Exception as exc:  # noqa: BLE001
        return _err(f"Schema nicht erreichbar: {exc}")
    return _err("Schema nicht erreichbar.")


def tool_sample_rows(args):
    table = str(args.get("table") or "orders")
    try:
        import app as flask_app
        res = flask_app.app.test_client().post(
            "/api/preview",
            json={"schema": "learn", "table": table},
        )
        return _ok_text(res.get_json())
    except Exception as exc:  # noqa: BLE001
        return _err(f"Vorschau fehlgeschlagen: {exc}")


def tool_run_sql(args):
    sql = str(args.get("sql") or "")
    if not sql.strip():
        return _err("sql fehlt.")
    try:
        import app as flask_app
        result = flask_app.run_sql(sql, allow_write=False)
        return _ok_text(result)
    except Exception as exc:  # noqa: BLE001
        return _err(f"SQL fehlgeschlagen: {exc}")


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


def tool_step_schema(_args):
    return _ok_text({
        "types": STEP_TYPES,
        "write_fields": ["title", "prompt", "placeholder", "solution", "hints", "concepts", "strict_columns"],
        "predict_fields": ["title", "text", "sql", "table", "expected_ids", "feedback_ok", "feedback_bad"],
        "quiz_item": {"q": "Frage", "options": ["A", "B", "C", "D"], "correct": 1, "explain": "Warum"},
        "id_prefix": "ws-",
        "note": "Offizielle PATH_IDS nicht überschreiben. Speichern nur über save_practice.",
    })


def _draft_payload(args) -> dict:
    lid = str(args.get("id") or "ws-draft")
    title = str(args.get("title") or "Werkstatt-Übung")
    prompt = str(args.get("prompt") or "Schreibe die Abfrage.")
    solution = str(args.get("solution") or "SELECT * FROM orders;")
    hints = args.get("hints") or [
        "Welche Tabelle, welche Spalten, welcher Filter?",
        "Vergleich das Ergebnis mit der Frage, nicht mit einem auswendig gelernten Satz.",
    ]
    return {
        "id": lid,
        "title": title,
        "goal": args.get("goal") or "Eine zusätzliche Übung neben dem Pfad.",
        "minutes": int(args.get("minutes") or 8),
        "concepts": args.get("concepts") or ["SELECT"],
        "model": args.get("model") or ["SELECT", "FROM", "WHERE"],
        "steps": [
            {
                "type": "look",
                "title": "Die Frage",
                "text": args.get("look") or prompt,
                "cta": "Selbst schreiben",
            },
            {
                "type": args.get("step_type") or "write",
                "title": title,
                "prompt": prompt,
                "placeholder": "SELECT …",
                "solution": solution,
                "hints": hints,
                "concepts": args.get("concepts") or ["SELECT"],
            },
        ],
        "quiz": args.get("quiz") or [
            {"q": "Woran erkennst du, dass die Übung sitzt?", "options": ["Musterstring", "Das Ergebnis passt zur Frage", "SELECT *", "Kein WHERE"], "correct": 1, "explain": "Die App prüft das Ergebnis."},
            {"q": "Darf diese Übung ein offizielles Kapitel ersetzen?", "options": ["Ja", "Nein, Werkstatt bleibt daneben", "Nur samstags", "Nur ohne JOIN"], "correct": 1, "explain": "Der Pfad bleibt kuratiert."},
            {"q": "Wohin speichert save_practice?", "options": ["PATH_IDS", "data/workshop", "Postgres-Systemkatalog", "localStorage"], "correct": 1, "explain": "JSON-Dateien in der Werkstatt."},
            {"q": "Welche Tabellen nutzt das Lager?", "options": ["nur pg_stat", "orders, clients, stock, order_items", "nur json", "information_schema allein"], "correct": 1, "explain": "Schema learn."},
        ],
    }


def tool_draft_exercise(args):
    return _ok_text(_draft_payload(args))


def tool_save_practice(args):
    data = args.get("lesson")
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as exc:
            return _err(f"lesson ist kein JSON: {exc}")
    if not data:
        data = _draft_payload(args)
    try:
        path = save_workshop_lesson(data)
    except ValueError as exc:
        return _err(str(exc))
    return _ok_text({"saved": str(path), "id": data.get("id"), "url": f"/werkstatt/{data.get('id')}"})


def tool_list_workshop(_args):
    return _ok_text([
        {"id": l["id"], "title": l["title"], "steps": len(l.get("steps") or [])}
        for l in workshop_lessons()
    ])


def tool_list_cards(args):
    topic = str(args.get("topic") or "")
    cards = knowledge_cards()
    if topic:
        cards = [c for c in cards if c.get("topic") == topic or c.get("slug") == topic]
    return _ok_text(cards[:40])


TOOLS = {
    "schema": {
        "description": "Tabellen und Spalten im Schema learn.",
        "inputSchema": {"type": "object", "properties": {}},
        "fn": tool_schema,
    },
    "sample_rows": {
        "description": "Erste Zeilen einer learn-Tabelle.",
        "inputSchema": {
            "type": "object",
            "properties": {"table": {"type": "string", "description": "orders, clients, stock oder order_items"}},
        },
        "fn": tool_sample_rows,
    },
    "run_sql": {
        "description": "SELECT/WITH/EXPLAIN gegen learn, damit erwartete Ergebnisse stimmen.",
        "inputSchema": {
            "type": "object",
            "properties": {"sql": {"type": "string"}},
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
        "description": "Offizielle Kapitel und Werkstatt-Übungen.",
        "inputSchema": {"type": "object", "properties": {}},
        "fn": tool_list_lessons,
    },
    "step_schema": {
        "description": "JSON-Form der Übungs-Schritte in der App.",
        "inputSchema": {"type": "object", "properties": {}},
        "fn": tool_step_schema,
    },
    "draft_exercise": {
        "description": "Eine Werkstatt-Übung im App-JSON entwerfen (noch nicht speichern).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
                "prompt": {"type": "string"},
                "solution": {"type": "string"},
                "goal": {"type": "string"},
                "look": {"type": "string"},
                "hints": {"type": "array", "items": {"type": "string"}},
                "concepts": {"type": "array", "items": {"type": "string"}},
            },
        },
        "fn": tool_draft_exercise,
    },
    "save_practice": {
        "description": "Übung nach data/workshop schreiben, nicht in den offiziellen Pfad.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lesson": {"type": "object"},
                "id": {"type": "string"},
                "title": {"type": "string"},
                "prompt": {"type": "string"},
                "solution": {"type": "string"},
            },
        },
        "fn": tool_save_practice,
    },
    "list_workshop": {
        "description": "Gespeicherte Werkstatt-Übungen.",
        "inputSchema": {"type": "object", "properties": {}},
        "fn": tool_list_workshop,
    },
    "list_cards": {
        "description": "Karteikarten der Bibel, optional nach Thema (lesen, filtern, …).",
        "inputSchema": {
            "type": "object",
            "properties": {"topic": {"type": "string"}},
        },
        "fn": tool_list_cards,
    },
}


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
                "serverInfo": {"name": "learnsql", "version": "1.0.0"},
            },
        }
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        tools = []
        for name, spec in TOOLS.items():
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
        spec = TOOLS.get(name)
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


def _read_stdio():
    headers = {}
    while True:
        line = sys.stdin.readline()
        if line == "":
            return None
        if line in ("\r\n", "\n"):
            break
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()
    length = int(headers.get("content-length") or "0")
    if length <= 0:
        return None
    body = sys.stdin.read(length)
    return json.loads(body)


def _write_stdio(msg: dict):
    raw = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(raw)}\r\n\r\n".encode("ascii")
    sys.stdout.buffer.write(header + raw)
    sys.stdout.buffer.flush()


def main():
    while True:
        try:
            msg = _read_stdio()
        except Exception:  # noqa: BLE001
            return
        if msg is None:
            return
        reply = handle(msg)
        if reply is None:
            continue
        _write_stdio(reply)


if __name__ == "__main__":
    main()
