#!/usr/bin/env python3
"""stdio MCP server: schema, Wissen, Übungen in den SQL-Playground legen."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(APP))

from install_mcp import apply_runtime_env  # noqa: E402

apply_runtime_env()
os.environ.setdefault("DB_HOST", os.environ.get("DB_HOST", "127.0.0.1"))

from lessons.academy_data import ACADEMY, lesson_by_id  # noqa: E402
from lessons.knowledge import ARTICLES, article_by_slug, knowledge_cards  # noqa: E402
from lessons.workshop import (  # noqa: E402
    delete_workshop_lesson,
    save_workshop_lesson,
    workshop_by_id,
    workshop_lessons,
)

PROTOCOL = "2024-11-05"

STEP_TYPES = [
    "look", "inspect", "explain", "demo", "predict", "predict-cols",
    "build", "fill", "write", "apply", "challenge", "mcq",
]

INSTRUCTIONS = (
    "Playground-Übungen folgen dem gleichen Schema wie der Lernpfad. "
    "Den Inhalt denkst du dir aus — die Form bleibt.\n"
    "Ablauf: anschauen → verstehen/vorhersagen → selbst schreiben → Kurzcheck.\n"
    "Jede Übung braucht: id (ws-…), title, goal, minutes, concepts, model, "
    "steps (mindestens 3, nicht nur look) und quiz (mindestens 4 Fachfragen zum SQL-Thema).\n"
    "Vor save_practice: step_schema lesen, bei Bedarf get_lesson als Vorbild "
    "(zum Beispiel ch8 oder challenge-2), die Musterlösung mit run_sql prüfen.\n"
    "Alte Übungen entfernen über delete_practice (eine id oder eine Liste).\n"
    "Hints helfen, sind aber nicht die volle Lösung. Quiz fragt das SQL-Thema, nicht das MCP. "
    "Offizielle PATH_IDS nicht überschreiben."
)


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
        "ablauf": "anschauen → verstehen/vorhersagen → selbst schreiben → Kurzcheck",
        "rule": (
            "Inhalt selbst ausdenken, Form wie der Lernpfad. "
            "Roh-Entwurf von draft_exercise nicht unverändert speichern."
        ),
        "lesson_fields": {
            "id": "ws-… (Buchstaben, Zahlen, Bindestrich)",
            "title": "Kurzer Titel wie ein Kapitel",
            "goal": "Ein Satz: was die Person danach kann",
            "minutes": 8,
            "concepts": ["SELECT", "WHERE", "GROUP BY", "JOIN"],
            "model": ["SELECT", "FROM", "WHERE"],
            "steps": "mindestens 3, nicht nur look",
            "quiz": "mindestens 4 Fachfragen zum SQL-Thema",
        },
        "sequence": [
            {"phase": "anschauen", "types": ["look", "inspect"], "why": "Daten und Frage zeigen, bevor jemand SQL schreibt."},
            {"phase": "verstehen", "types": ["explain", "demo", "predict", "predict-cols"], "why": "SQL vorhersagen oder erklären, nicht nur abtippen."},
            {"phase": "schreiben", "types": ["build", "fill", "write", "apply", "challenge"], "why": "Selbst formulieren, dann übertragen."},
            {"phase": "kurzcheck", "types": ["mcq"], "why": "Quiz-Tab: vier Fachfragen, kein MCP."},
        ],
        "types": STEP_TYPES,
        "fields": {
            "look": ["title", "text", "table", "tables", "note", "cta", "concepts"],
            "inspect": ["title", "text", "table", "interaction", "answer", "feedback_ok", "feedback_bad", "concepts"],
            "explain": ["title", "text", "sql", "plain", "parts", "before_table", "after_table", "concepts"],
            "demo": ["title", "text", "sql", "table", "visualize", "keep_columns", "concepts"],
            "predict": ["title", "text", "sql", "table", "expected_ids", "id_field", "feedback_ok", "feedback_bad", "concepts"],
            "predict-cols": ["title", "text", "sql", "table", "expected_columns", "feedback_ok", "feedback_bad", "concepts"],
            "build": ["title", "prompt", "pieces", "distractors", "solution", "hints", "concepts"],
            "fill": ["title", "template", "solution", "hints", "concepts"],
            "write": ["title", "prompt", "placeholder", "solution", "hints", "concepts", "strict_columns", "ordered", "require", "forbid", "allow_write", "verify"],
            "apply": ["title", "prompt", "placeholder", "solution", "hints", "concepts", "strict_columns", "ordered"],
            "challenge": ["title", "prompt", "placeholder", "solution", "hints", "concepts", "strict_columns", "ordered"],
            "mcq": ["title", "question", "options"],
        },
        "table": {
            "name": "orders",
            "label": "Aufträge",
            "columns": ["id", "status"],
            "rows": [{"id": 1, "status": "offen"}],
        },
        "quiz_item": {"q": "Frage", "options": ["A", "B", "C", "D"], "correct": 1, "explain": "Warum"},
        "hints": "Mindestens zwei. Der letzte Hint ist nicht die volle Lösung.",
        "geruest": _draft_payload({
            "id": "ws-beispiel",
            "title": "Offene zählen",
            "prompt": "Wie viele offene Aufträge gibt es? Nur die Anzahl.",
            "solution": "SELECT COUNT(*) FROM orders WHERE status = 'offen';",
            "concepts": ["GROUP BY"],
        }),
        "id_prefix": "ws-",
        "note": "Offizielle PATH_IDS nicht überschreiben. Speichern nur über save_practice. Vorbild: get_lesson mit ch8 oder challenge-2.",
    })


def tool_get_lesson(args):
    lid = str(args.get("id") or "").strip()
    if not lid:
        return _err("id fehlt. Offizielle IDs über list_lessons, zum Beispiel ch8 oder challenge-2.")
    lesson = lesson_by_id(lid) or workshop_by_id(lid)
    if not lesson:
        return _err(f"Übung {lid} nicht gefunden.")
    return _ok_text(lesson)


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
                "cta": "Vorhersagen",
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
            },
            {
                "type": "apply",
                "title": "Noch einmal, leicht anders",
                "prompt": apply_prompt,
                "placeholder": "SELECT …",
                "solution": solution,
                "hints": hints,
                "concepts": concepts,
            },
        ],
        "quiz": args.get("quiz") or _topic_quiz(concepts, prompt),
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
    return _ok_text({"saved": str(path), "id": data.get("id"), "url": f"/playground/{data.get('id')}"})


def tool_list_workshop(_args):
    return _ok_text([
        {"id": l["id"], "title": l["title"], "steps": len(l.get("steps") or [])}
        for l in workshop_lessons()
    ])


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
        "description": "Offizielle Kapitel und SQL-Playground-Übungen.",
        "inputSchema": {"type": "object", "properties": {}},
        "fn": tool_list_lessons,
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
        "description": "Entwurf im Übungsdesign (anschauen → verstehen → schreiben → Kurzcheck). Inhalt selbst wählen, Form aus step_schema. Nicht unverändert speichern.",
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
        "description": "Übung in den SQL-Playground schreiben (data/workshop). lesson folgt dem Übungsdesign aus step_schema. Vorher run_sql auf die Lösung. Nicht in den offiziellen Pfad.",
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
                "instructions": INSTRUCTIONS,
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
