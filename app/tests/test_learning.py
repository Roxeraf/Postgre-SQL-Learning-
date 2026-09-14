"""Unit tests for learner feedback and academy metadata (no database)."""
from __future__ import annotations

import json
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import copy
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))

from lessons.academy_data import ACADEMY, CLIENTS, ORDERS, PATH_IDS, lesson_by_id  # noqa: E402
from lessons.academy_more import ORDER_ITEMS  # noqa: E402
from sql_coach import (  # noqa: E402
    diagnose_structure,
    explain_sql,
    friendly_sql_error,
    has_empty_select_list,
    uses_equals_null,
)

def claude_sandbox_env(tmp: str) -> dict:
    home = Path(tmp)
    user = home / "userhome"
    user.mkdir(exist_ok=True)
    local = home / "local"
    local.mkdir(exist_ok=True)
    (home / "mcp-status.json").write_text(
        json.dumps({"installed": False, "clients": []}),
        encoding="utf-8",
    )
    return {
        "APPDATA": tmp,
        "LOCALAPPDATA": str(local),
        "HOME": str(user),
        "USERPROFILE": str(user),
        "CLAUDE_CONFIG_DIR": "",
        "LEARN_SQL_HOME": tmp,
    }


def mcp_call(mcp, name, arguments, mid=1):
    return mcp.handle({
        "jsonrpc": "2.0",
        "id": mid,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })


def mcp_payload(reply):
    return json.loads(reply["result"]["content"][0]["text"])


def mcp_is_error(reply):
    return bool(reply["result"].get("isError"))


def ok_sandbox_sql(_sql="", allow_write=False, as_ids=None):
    if as_ids:
        return {
            "ok": True,
            "ids": [1, 3],
            "id_field": as_ids,
            "columns": [as_ids],
            "rows": None,
            "error": None,
            "pg_error": None,
        }
    return {
        "ok": True,
        "columns": ["id"],
        "rows": [{"id": 1}, {"id": 3}],
        "error": None,
        "pg_error": None,
        "note": None,
        "messages": [],
    }


def ok_sandbox_table(table, columns=None, where=None):
    cols = list(columns) if columns else ["id"]
    rows = [{c: (1 if n == 0 else 3) if c == "id" else "x" for c in cols} for n in range(2)]
    return {"ok": True, "name": table, "label": table, "columns": cols, "rows": rows}


VALID_PLAYGROUND_LESSON = {
    "id": "ws-mcp-del",
    "title": "Löschen",
    "goal": "Eine Karte anlegen und wieder entfernen.",
    "minutes": 8,
    "concepts": ["SELECT"],
    "model": ["SELECT", "FROM"],
    "steps": [
        {"type": "look", "title": "Frage", "text": "Schau dir die Aufträge an — jede Zeile ist ein Datensatz.", "cta": "Weiter"},
        {
            "type": "explain",
            "title": "SQL",
            "text": "COUNT zählt Zeilen. Tippe die Teile an.",
            "sql": "SELECT COUNT(*) FROM orders;",
            "plain": "Zähle alle Zeilen in der Auftragstabelle — jede Zeile zählt als eins.",
            "parts": [
                {
                    "match": "SELECT COUNT(*)",
                    "token": "SELECT",
                    "question": "Was möchte ich sehen?",
                    "answer": "Die Anzahl der Zeilen, nicht die einzelnen Aufträge.",
                },
                {
                    "match": "FROM orders",
                    "token": "FROM",
                    "question": "Woher kommen die Daten?",
                    "answer": "Aus der Auftragstabelle orders.",
                },
            ],
        },
        {
            "type": "write",
            "title": "Zählen",
            "prompt": "Wie viele offene Aufträge?",
            "solution": "SELECT COUNT(*) FROM orders WHERE status = 'offen';",
            "hints": ["COUNT(*)", "WHERE status = 'offen'"],
            "teach": (
                "COUNT(*) zählt Zeilen. WHERE filtert vorher auf status = 'offen', "
                "sonst würdest du alle Aufträge zählen, nicht nur die offenen."
            ),
        },
    ],
    "quiz": [
        {"q": "A?", "options": ["1", "2", "3", "4"], "correct": 1, "explain": "x"},
        {"q": "B?", "options": ["1", "2", "3", "4"], "correct": 0, "explain": "x"},
        {"q": "C?", "options": ["1", "2", "3", "4"], "correct": 2, "explain": "x"},
        {"q": "D?", "options": ["1", "2", "3", "4"], "correct": 3, "explain": "x"},
    ],
}

FORBIDDEN_SNIPPETS = (
    "Red Bull",
    "Nordlog",
    "13d663",
    "flowapp_13d663",
    "instance_1",
    "flowapp_demo_",
    "WMX",
    "FlowApp",
)
FORBIDDEN_CLIENT_TOKENS = (
    re.compile(r"['\"]ETE['\"]"),
    re.compile(r"\bRed-Bull\b", re.I),
)

SKIP_NAME = {"test_learning.py"}
SKIP_PARTS = {"vendor", ".git"}


class SqlCoachTests(unittest.TestCase):
    def test_missing_from_is_a_learning_message(self):
        msg = diagnose_structure("SELECT order_number", "SELECT order_number FROM orders")
        self.assertIn("FROM", msg)
        self.assertIn("woher", msg.lower())
        self.assertNotIn("SELECT SELECT", msg)

    def test_and_vs_or(self):
        msg = diagnose_structure(
            "SELECT * FROM orders WHERE client = 'Helio' OR status = 'offen'",
            "SELECT * FROM orders WHERE client = 'Helio' AND status = 'offen'",
        )
        self.assertIn("AND", msg)

    def test_equals_null(self):
        self.assertTrue(uses_equals_null("SELECT * FROM orders WHERE status = NULL"))
        msg = friendly_sql_error("syntax error", "SELECT * FROM stock WHERE weight = NULL")
        self.assertIn("IS NULL", msg)

    def test_empty_select(self):
        self.assertTrue(has_empty_select_list("SELECT FROM orders"))

    def test_explain_logical_order(self):
        parts = explain_sql(
            "SELECT client, COUNT(*) FROM orders WHERE status = 'offen' GROUP BY client ORDER BY COUNT(*) DESC"
        )["parts"]
        keys = [p["key"] for p in parts]
        self.assertLess(keys.index("FROM"), keys.index("WHERE"))
        self.assertLess(keys.index("WHERE"), keys.index("GROUP BY"))
        self.assertLess(keys.index("GROUP BY"), keys.index("SELECT"))

    def test_join_hint(self):
        msg = diagnose_structure(
            "SELECT o.order_number FROM orders o",
            "SELECT o.order_number, c.name FROM orders o JOIN clients c ON c.id = o.client_id",
        )
        self.assertIsNotNone(msg)
        self.assertIn("JOIN", msg)

    def test_having_hint(self):
        msg = diagnose_structure(
            "SELECT client, COUNT(*) FROM orders GROUP BY client",
            "SELECT client, COUNT(*) FROM orders GROUP BY client HAVING COUNT(*) > 4",
        )
        self.assertIn("HAVING", msg)

    def test_left_join_hint(self):
        msg = diagnose_structure(
            "SELECT o.order_number FROM orders o JOIN clients c ON c.id = o.client_id",
            "SELECT o.order_number FROM orders o LEFT JOIN clients c ON c.id = o.client_id",
        )
        self.assertIn("LEFT", msg)

    def test_update_without_where(self):
        msg = diagnose_structure(
            "UPDATE orders SET status = 'fertig'",
            "UPDATE orders SET status = 'fertig' WHERE order_number = 4714",
        )
        self.assertIn("WHERE", msg)

    def test_unknown_table_message_lists_learn_tables(self):
        msg = friendly_sql_error('relation "foo" does not exist', "SELECT * FROM foo")
        self.assertIn("order_items", msg)
        self.assertNotIn("instance_1", msg)


class AcademyContentTests(unittest.TestCase):
    def test_path_covers_fundamentals(self):
        ids = [l["id"] for l in ACADEMY["lessons"]]
        self.assertEqual(ids, PATH_IDS)
        for needed in (
            "ch0", "ch7", "ch-alias", "ch8", "ch-agg", "ch-having", "ch-keys",
            "ch9", "ch10", "ch-items", "ch-case", "ch-subq", "challenge-4",
            "ch-dml", "ch-tx", "ch-pg", "challenge-3",
        ):
            self.assertIn(needed, ids)
        self.assertLess(ids.index("ch8"), ids.index("ch-agg"))
        self.assertLess(ids.index("ch-agg"), ids.index("ch-having"))
        self.assertLess(ids.index("ch10"), ids.index("ch-items"))
        self.assertLess(ids.index("ch-items"), ids.index("ch-case"))
        self.assertLess(ids.index("challenge-2"), ids.index("ch-subq"))
        self.assertLess(ids.index("ch-subq"), ids.index("challenge-4"))
        self.assertLess(ids.index("challenge-4"), ids.index("ch-dml"))

    def test_every_lesson_has_goal_interaction_and_quiz(self):
        self.assertGreaterEqual(len(ACADEMY["lessons"]), 18)
        for lesson in ACADEMY["lessons"]:
            self.assertTrue(lesson["goal"], lesson["id"])
            self.assertTrue(lesson["steps"], lesson["id"])
            types = {s["type"] for s in lesson["steps"]}
            self.assertTrue(types - {"look"}, msg=f"{lesson['id']} needs an active step")
            quiz = lesson.get("quiz") or []
            self.assertGreaterEqual(len(quiz), 4, msg=f"{lesson['id']} needs a Kurzcheck")
            write_types = types & {"write", "apply", "challenge"}
            if lesson["id"] != "ch0":
                self.assertTrue(write_types, msg=f"{lesson['id']} needs a write/apply step")

    def test_sql_steps_have_solutions_and_no_pasted_solution_hint(self):
        for lesson in ACADEMY["lessons"]:
            for i, step in enumerate(lesson["steps"]):
                if step["type"] in {"write", "build", "fill", "apply", "challenge"}:
                    self.assertTrue(step.get("solution"), f"{lesson['id']} step {i}")
                    hints = step.get("hints") or []
                    self.assertTrue(hints, f"{lesson['id']} step {i} needs hints")
                    last = hints[-1].replace(";", "").replace("\n", " ")
                    sol = (step["solution"] or "").replace(";", "").replace("\n", " ")
                    self.assertNotEqual(
                        re.sub(r"\s+", " ", last).strip().lower(),
                        re.sub(r"\s+", " ", sol).strip().lower(),
                        msg=f"{lesson['id']} step {i} last hint is the full solution",
                    )

    def test_interactive_steps_have_clear_feedback_bad(self):
        banned = (
            "verwirft die linke Tabelle",
            "Versuch’s nochmal",
            "So liest du den Fehler",
        )
        for lesson in ACADEMY["lessons"]:
            for i, step in enumerate(lesson["steps"]):
                if step["type"] not in {"inspect", "predict", "predict-cols"}:
                    continue
                bad = (step.get("feedback_bad") or "").strip()
                self.assertTrue(bad, msg=f"{lesson['id']} step {i} needs feedback_bad")
                for phrase in banned:
                    self.assertNotIn(phrase, bad, msg=f"{lesson['id']} step {i}")

    def test_lookup(self):
        self.assertEqual(lesson_by_id("ch3")["title"], "WHERE")
        self.assertEqual(lesson_by_id("ch7")["title"], "NULL — fehlende Werte")
        self.assertEqual(lesson_by_id("ch-keys")["title"], "Schlüssel und Relationen")
        self.assertIsNone(lesson_by_id("missing"))

    def test_anonymized_clients(self):
        names = {c["name"] for c in CLIENTS}
        self.assertEqual(names, {"Helio", "Alpin", "Nordkai", "Westfeld"})
        self.assertTrue(any(r["client_id"] is None for r in ORDERS))
        self.assertTrue(any(r["quantity"] is None for r in ORDERS))
        self.assertGreaterEqual(len(ORDERS), 20)
        self.assertTrue(any(r["id"] not in {i["order_id"] for i in ORDER_ITEMS} for r in ORDERS))

    def test_glossary_and_flashcards(self):
        glossary = ACADEMY.get("glossary") or []
        self.assertGreaterEqual(len(glossary), 12)
        self.assertTrue(ACADEMY.get("flashcards"))
        labels = {g["id"] for g in glossary}
        for needed in ("NULL", "JOIN", "HAVING", "TX", "INDEX"):
            self.assertIn(needed, labels)

    def test_knowledge_bible_is_complete(self):
        from lessons.knowledge import ARTICLES, ARTICLES_BY_SLUG, knowledge_cards, sections

        self.assertGreaterEqual(len(ARTICLES), 40)
        self.assertEqual(len(ARTICLES_BY_SLUG), len(ARTICLES))
        self.assertGreaterEqual(len(sections()), 6)
        cards = knowledge_cards()
        self.assertGreaterEqual(len(cards), 120)
        for art in ARTICLES:
            self.assertTrue(art["slug"], art["title"])
            self.assertTrue(art["section"], art["slug"])
            self.assertTrue(art["summary"], art["slug"])
            self.assertTrue(art["body"], art["slug"])
            self.assertTrue(art.get("sql"), art["slug"])
            self.assertGreaterEqual(len(art.get("cards") or []), 3, art["slug"])
            for c in art["cards"]:
                self.assertTrue(c["front"] and c["back"], c.get("id"))

    def test_dml_steps_are_verified(self):
        dml = lesson_by_id("ch-dml")
        writes = [s for s in dml["steps"] if s.get("allow_write")]
        self.assertGreaterEqual(len(writes), 3)
        for step in writes:
            self.assertTrue(step.get("verify"), step["title"])


class AcademyCheckRestoreTests(unittest.TestCase):
    def test_failed_restore_blocks_write_check(self):
        import app as flask_app

        with patch.object(flask_app, "restore_learn_schema", return_value=(False, "kein Init-SQL")):
            result = flask_app.academy_write_check(
                "INSERT INTO stock (id, item, quantity, weight) VALUES (8, 'Karton H', 4, 18);",
                {
                    "solution": "INSERT INTO stock (id, item, quantity, weight) VALUES (8, 'Karton H', 4, 18);",
                    "verify": "SELECT * FROM stock WHERE id = 8",
                },
            )
        self.assertFalse(result["ok"])
        self.assertIn("kein Init-SQL", result["error"])

    def test_select_check_resets_schema_first(self):
        import app as flask_app

        client = flask_app.app.test_client()
        ok_result = {
            "ok": True,
            "columns": ["*"],
            "rows": [{"id": 1, "order_number": 4711, "client": "Helio", "status": "offen"}],
            "empty_select": False,
            "error": None,
            "messages": [],
        }
        calls = []

        def restore():
            calls.append("restore")
            return True, "ok"

        def run_sql(*_a, **_k):
            calls.append("run")
            return ok_result

        with patch.object(flask_app, "restore_learn_schema", side_effect=restore):
            with patch.object(flask_app, "run_sql", side_effect=run_sql):
                resp = client.post(
                    "/api/academy/check",
                    json={"lesson_id": "ch1", "step": 3, "sql": "SELECT * FROM orders"},
                )
        data = resp.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("restore", calls)
        self.assertEqual(calls[0], "restore")

    def test_select_check_surfaces_restore_failure(self):
        import app as flask_app

        client = flask_app.app.test_client()
        with patch.object(flask_app, "restore_learn_schema", return_value=(False, "boom")):
            resp = client.post(
                "/api/academy/check",
                json={"lesson_id": "ch1", "step": 3, "sql": "SELECT order_number FROM orders"},
            )
        data = resp.get_json()
        self.assertFalse(data["ok"])
        self.assertIn("boom", data["error"])


class ResultValidationTests(unittest.TestCase):
    def test_star_select_is_not_strict_by_default(self):
        import app as flask_app

        self.assertFalse(flask_app._wants_strict_columns({"solution": "SELECT * FROM orders;"}))
        self.assertTrue(flask_app._wants_strict_columns({"solution": "SELECT client, status FROM orders;"}))
        self.assertFalse(flask_app._wants_strict_columns({
            "solution": "SELECT client FROM orders;",
            "strict_columns": False,
        }))

    def test_column_lesson_rejects_star_shaped_result(self):
        import app as flask_app

        user_cols = ["id", "order_number", "client", "status"]
        user_rows = [{"id": 1, "order_number": 4711, "client": "Helio", "status": "offen"}]
        sol_cols = ["client", "status"]
        sol_rows = [{"client": "Helio", "status": "offen"}]
        ok, _missing, extra, *_rest = flask_app.compare_query_result(
            user_cols, user_rows, sol_cols, sol_rows, strict_columns=True
        )
        self.assertFalse(ok)
        self.assertTrue(extra)

    def test_matching_projection_still_passes(self):
        import app as flask_app

        cols = ["client", "status"]
        rows = [{"client": "Helio", "status": "offen"}]
        ok, *_rest = flask_app.compare_query_result(
            cols, rows, cols, rows, strict_columns=True
        )
        self.assertTrue(ok)


class EnsureAppDatabaseTests(unittest.TestCase):
    def test_missing_database_error_en_and_de(self):
        import app as flask_app

        en = flask_app.psycopg2.OperationalError(
            'connection to server at "db" (172.20.0.2), port 5432 failed: '
            'FATAL: database "learnsql" does not exist'
        )
        de = flask_app.psycopg2.OperationalError(
            'FATAL: Datenbank »learnsql« existiert nicht'
        )
        other = flask_app.psycopg2.OperationalError("password authentication failed")
        self.assertTrue(flask_app._is_missing_database_error(en, "learnsql"))
        self.assertTrue(flask_app._is_missing_database_error(de, "learnsql"))
        self.assertFalse(flask_app._is_missing_database_error(other, "learnsql"))

    def test_ensure_creates_database_when_missing(self):
        import app as flask_app

        created = []

        class Cur:
            def __enter__(self):
                return self

            def __exit__(self, *_a):
                return False

            def execute(self, sql, params=None):
                self.sql = sql
                if "CREATE DATABASE" in sql:
                    created.append(sql)

            def fetchone(self):
                if "pg_database" in getattr(self, "sql", ""):
                    return None
                return (1,)

        class Conn:
            def cursor(self):
                return Cur()

            def close(self):
                pass

        def fake_connect(**cfg):
            if cfg["dbname"] == "learnsql":
                raise flask_app.psycopg2.OperationalError(
                    'connection to server at "db" (172.20.0.2), port 5432 failed: '
                    'FATAL: database "learnsql" does not exist'
                )
            return Conn()

        with patch.object(flask_app.psycopg2, "connect", side_effect=fake_connect):
            ok, err = flask_app.ensure_app_database()
        self.assertTrue(ok)
        self.assertIsNone(err)
        self.assertTrue(any("learnsql" in sql for sql in created))

    def test_restore_reports_other_connection_errors(self):
        import app as flask_app

        with patch.object(
            flask_app,
            "ensure_app_database",
            return_value=(False, 'FATAL: database "learnsql" does not exist'),
        ):
            ok, message = flask_app.restore_learn_schema()
        self.assertFalse(ok)
        self.assertIn("learnsql", message)


class NoCustomerNamesTests(unittest.TestCase):
    def test_repo_has_no_wmx_or_customer_names(self):
        roots = [
            REPO / "app",
            REPO / "db",
            REPO / "README.md",
        ]
        hits = []
        for root in roots:
            paths = [root] if root.is_file() else root.rglob("*")
            for path in paths:
                if not path.is_file():
                    continue
                if path.name in SKIP_NAME or path.suffix in {".pyc", ".png", ".min.js"}:
                    continue
                if any(part in SKIP_PARTS for part in path.parts):
                    continue
                try:
                    text = path.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError):
                    continue
                for needle in FORBIDDEN_SNIPPETS:
                    if needle in text:
                        hits.append(f"{path}:{needle}")
                for rx in FORBIDDEN_CLIENT_TOKENS:
                    if rx.search(text):
                        hits.append(f"{path}:{rx.pattern}")
        self.assertEqual(hits, [], msg="WMX/Kundennamen im Repo:\n" + "\n".join(hits))


class WorkshopAndMcpTests(unittest.TestCase):
    def test_workshop_save_and_lookup(self):
        import tempfile
        from lessons import workshop as ws

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict("os.environ", {"WORKSHOP_DIR": tmp}):
                path = ws.save_workshop_lesson({
                    "id": "ws-test-open",
                    "title": "Offene zählen",
                    "goal": "Zähle offene Aufträge.",
                    "steps": [{
                        "type": "write",
                        "title": "Zählen",
                        "prompt": "Wie viele offene Aufträge?",
                        "solution": "SELECT COUNT(*) FROM orders WHERE status = 'offen';",
                        "hints": ["COUNT(*)", "WHERE status = 'offen'"],
                    }],
                    "quiz": [
                        {"q": "A?", "options": ["1", "2", "3", "4"], "correct": 1, "explain": "x"},
                    ],
                })
                self.assertTrue(path.is_file())
                found = ws.workshop_by_id("ws-test-open")
                self.assertEqual(found["title"], "Offene zählen")
                with self.assertRaises(ValueError):
                    ws.save_workshop_lesson({"id": "ch0", "steps": [{"type": "look", "title": "x"}]})
                self.assertTrue(ws.delete_workshop_lesson("ws-test-open"))
                self.assertIsNone(ws.workshop_by_id("ws-test-open"))
                self.assertFalse(ws.delete_workshop_lesson("ws-test-open"))
                with self.assertRaises(ValueError):
                    ws.delete_workshop_lesson("ch0")

    def test_mcp_lists_tools_and_drafts(self):
        sys.path.insert(0, str(REPO / "mcp"))
        import learnsql_mcp as mcp

        listed = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        names = {t["name"] for t in listed["result"]["tools"]}
        for needed in (
            "schema", "run_sql", "search_wissen", "draft_exercise",
            "save_practice", "get_lesson", "step_schema", "delete_practice",
            "exercise_context", "validate_exercise", "table_rows",
            "buddy_context", "help_with", "search_path", "coach_sql",
        ):
            self.assertIn(needed, names)

        init = mcp.handle({"jsonrpc": "2.0", "id": 10, "method": "initialize"})
        instructions = init["result"]["instructions"]
        self.assertIn("anschauen", instructions)
        self.assertIn("Kurzcheck", instructions)
        self.assertIn("exercise_context", instructions)
        self.assertIn("draft_exercise", instructions)
        self.assertIn("step_schema", instructions)
        self.assertIn("buddy_context", instructions)
        self.assertIn("help_with", instructions)
        self.assertIn("coach_sql", instructions)
        self.assertEqual(init["result"]["serverInfo"]["version"], mcp.BUILD)
        mentioned = set(re.findall(r"`([a-z][a-z0-9_]+)`", instructions))
        unknown = mentioned - names
        self.assertEqual(unknown, set())

        schema = mcp.handle({
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {"name": "step_schema", "arguments": {}},
        })
        schema_payload = json.loads(schema["result"]["content"][0]["text"])
        self.assertIn("anschauen", schema_payload["ablauf"])
        self.assertIn("steps", schema_payload["geruest"])
        self.assertGreaterEqual(len(schema_payload["geruest"]["steps"]), 3)
        self.assertIn("required", schema_payload["fields"]["write"])
        self.assertIn("teach", schema_payload["fields"]["write"]["required"])
        self.assertIn("plain", schema_payload["fields"]["explain"]["required"])
        self.assertIn("ordered", schema_payload["fields"]["write"]["optional"])
        self.assertIn("ordered", schema_payload["field_semantics"])
        self.assertEqual(schema_payload["build"], mcp.BUILD)
        save_spec = next(t for t in listed["result"]["tools"] if t["name"] == "save_practice")
        lesson_schema = save_spec["inputSchema"]["properties"]["lesson"]
        self.assertTrue(lesson_schema.get("description"))
        self.assertIn("id", lesson_schema["properties"])
        self.assertIn("enum", lesson_schema["properties"]["steps"]["items"]["properties"]["type"])
        for key, spec in save_spec["inputSchema"]["properties"].items():
            if isinstance(spec, dict):
                self.assertTrue(spec.get("description"), msg=key)

        lesson = mcp.handle({
            "jsonrpc": "2.0",
            "id": 12,
            "method": "tools/call",
            "params": {"name": "get_lesson", "arguments": {"id": "ch8"}},
        })
        ch8 = json.loads(lesson["result"]["content"][0]["text"])
        self.assertEqual(ch8["id"], "ch8")
        self.assertTrue(ch8["steps"])

        draft = mcp.handle({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "draft_exercise",
                "arguments": {
                    "id": "ws-mcp-draft",
                    "title": "Helio offen",
                    "prompt": "Offene Helio-Aufträge",
                    "solution": "SELECT * FROM orders WHERE client = 'Helio' AND status = 'offen';",
                },
            },
        })
        payload = json.loads(draft["result"]["content"][0]["text"])
        self.assertEqual(payload["id"], "ws-mcp-draft")
        types = [step["type"] for step in payload["steps"]]
        self.assertGreaterEqual(len(types), 3)
        self.assertIn("look", types)
        self.assertIn("explain", types)
        self.assertIn("write", types)
        explain = next(step for step in payload["steps"] if step["type"] == "explain")
        self.assertTrue(explain.get("plain"))
        self.assertGreaterEqual(len(explain.get("parts") or []), 2)
        write = next(step for step in payload["steps"] if step["type"] == "write")
        self.assertGreaterEqual(len(write.get("teach") or ""), 40)
        quiz_blob = json.dumps(payload["quiz"], ensure_ascii=False)
        self.assertNotIn("save_practice", quiz_blob)
        self.assertNotIn("PATH_IDS", quiz_blob)
        self.assertGreaterEqual(len(payload["quiz"]), 4)

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict("os.environ", {"WORKSHOP_DIR": tmp}):
                with patch.object(mcp, "sandbox_sql", side_effect=ok_sandbox_sql):
                    saved = mcp.handle({
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {
                            "name": "save_practice",
                            "arguments": {"lesson": VALID_PLAYGROUND_LESSON},
                        },
                    })
                saved_payload = json.loads(saved["result"]["content"][0]["text"])
                self.assertFalse(saved["result"].get("isError"))
                self.assertIn("/playground/ws-mcp-del", saved_payload.get("url", ""))
                self.assertEqual(saved_payload.get("reachable"), None)
                deleted = mcp.handle({
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {"name": "delete_practice", "arguments": {"id": ["ws-mcp-del"]}},
                })
                deleted_payload = json.loads(deleted["result"]["content"][0]["text"])
                self.assertEqual(deleted_payload.get("deleted"), ["ws-mcp-del"])

    def test_mcp_stdio_reads_ndjson_not_as_headers(self):
        import io

        sys.path.insert(0, str(REPO / "mcp"))
        import learnsql_mcp as mcp

        incoming = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n'
        msg, style = mcp._read_message(io.StringIO(incoming))
        self.assertEqual(style, "ndjson")
        self.assertEqual(msg["method"], "initialize")
        reply = mcp.handle(msg)
        out = io.StringIO()
        mcp._write_message(reply, style, stdout=out)
        line = out.getvalue()
        self.assertTrue(line.startswith("{"))
        self.assertNotIn("Content-Length", line)
        self.assertEqual(json.loads(line)["id"], 1)

        body = '{"jsonrpc":"2.0","id":2,"method":"ping"}'
        framed = f"Content-Length: {len(body.encode('utf-8'))}\r\n\r\n{body}"
        msg, style = mcp._read_message(io.StringIO(framed))
        self.assertEqual(style, "lsp")
        self.assertEqual(msg["method"], "ping")

    def test_mcp_stdio_initialize_roundtrip_subprocess(self):
        import subprocess

        script = REPO / "mcp" / "learnsql_mcp.py"
        payload = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1"},
            },
        }) + "\n"
        proc = subprocess.run(
            [sys.executable, "-u", str(script)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=15,
            env={**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"},
            cwd=str(REPO),
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        first = proc.stdout.strip().splitlines()[0]
        self.assertNotIn("Content-Length", first)
        data = json.loads(first)
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["result"]["serverInfo"]["name"], "learnsql")
        self.assertEqual(data["result"]["serverInfo"]["version"], "1.2.0")


class McpAgentWorkflowTests(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(REPO / "mcp"))
        import learnsql_mcp as mcp
        self.mcp = mcp

    def test_db_host_defaults_to_localhost(self):
        import learn_db
        env = {k: v for k, v in os.environ.items() if k != "DB_HOST"}
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(learn_db.db_config()["host"], "127.0.0.1")

    def test_environment_report_names_paths_and_flask(self):
        mcp = self.mcp
        exc = ModuleNotFoundError("No module named 'app'", name="app")
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "runtime.json").write_text(
                json.dumps({"flaskPid": 31512, "appPort": 8081}),
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"LEARN_SQL_HOME": str(home), "WORKSHOP_DIR": str(home / "workshop")}):
                with patch.object(mcp, "pid_alive", return_value=True):
                    with patch.object(mcp, "http_get", return_value=(200, "http://127.0.0.1:8081/")):
                        text = mcp.environment_report("Schema nicht erreichbar.", exc)
        self.assertIn("App-Modul nicht importierbar", text)
        self.assertIn("LEARN_SQL_HOME", text)
        self.assertIn(str(home), text)
        self.assertIn("app.py", text)
        self.assertIn("8081", text)
        self.assertIn("31512", text)

    def test_run_sql_as_ids_is_compact(self):
        mcp = self.mcp
        with patch.object(mcp, "sandbox_sql", side_effect=ok_sandbox_sql) as mocked:
            reply = mcp_call(mcp, "run_sql", {"sql": "SELECT id FROM orders", "as_ids": "id"})
        self.assertFalse(mcp_is_error(reply))
        payload = mcp_payload(reply)
        self.assertEqual(payload["ids"], [1, 3])
        self.assertIsNone(payload.get("rows"))
        self.assertEqual(mocked.call_args.kwargs.get("as_ids") or mocked.call_args[1].get("as_ids"), "id")

    def test_table_rows_shape(self):
        mcp = self.mcp
        with patch.object(mcp, "sandbox_table", side_effect=ok_sandbox_table):
            reply = mcp_call(mcp, "table_rows", {"table": "orders", "columns": ["id"]})
        payload = mcp_payload(reply)
        self.assertEqual(payload["name"], "orders")
        self.assertEqual(payload["columns"], ["id"])
        self.assertTrue(payload["rows"])
        self.assertEqual(payload["build"], mcp.BUILD)

    def test_exercise_context_has_contract(self):
        mcp = self.mcp
        with patch.object(mcp, "sandbox_schema", return_value={"ok": False, "error": "offline"}):
            reply = mcp_call(mcp, "exercise_context", {"example": "challenge-2"})
        payload = mcp_payload(reply)
        self.assertIn("challenge-2", (payload.get("example_lesson") or {}).get("id", "challenge-2"))
        self.assertGreaterEqual(len(payload["minimal_valid"]["steps"]), 3)
        self.assertGreaterEqual(len(payload["minimal_valid"]["quiz"]), 4)
        self.assertTrue(any(s.get("type") == "explain" for s in payload["minimal_valid"]["steps"]))
        self.assertIn("buddy_tools", payload)
        self.assertIn("buddy_context", payload["buddy_tools"])
        self.assertIn("required", payload["step_types"]["predict"])
        self.assertIn("ordered", payload["field_semantics"])
        self.assertEqual(payload["table"]["columns"], ["id", "status"])
        self.assertIn("ch8", payload["path_ids"])
        self.assertIn("DROP SCHEMA", payload["reset"])
        self.assertIn("learn CASCADE", payload["reset"])

    def test_validate_rejects_unknown_type_and_bad_quiz(self):
        mcp = self.mcp
        lesson = copy.deepcopy(VALID_PLAYGROUND_LESSON)
        lesson["id"] = "ws-bad-type"
        lesson["steps"][2]["type"] = "challengee"
        lesson["quiz"][0]["correct"] = 4
        with patch.object(mcp, "sandbox_sql", side_effect=ok_sandbox_sql):
            reply = mcp_call(mcp, "validate_exercise", {"lesson": lesson})
        self.assertTrue(mcp_is_error(reply))
        payload = mcp_payload(reply)
        blob = " ".join(payload.get("errors") or [])
        self.assertIn("unbekannter type", blob)
        self.assertIn("correct=4", blob)

    def test_validate_reports_expected_ids(self):
        mcp = self.mcp
        lesson = copy.deepcopy(VALID_PLAYGROUND_LESSON)
        lesson["id"] = "ws-predict-ids"
        lesson["steps"][1] = {
            "type": "predict",
            "title": "Welche id?",
            "text": "Markiere.",
            "sql": "SELECT id FROM orders WHERE status = 'offen'",
            "table": {
                "name": "orders",
                "label": "Aufträge",
                "columns": ["id"],
                "rows": [{"id": 1}, {"id": 3}],
            },
            "id_field": "id",
            "expected_ids": [9, 9],
        }
        with patch.object(mcp, "sandbox_sql", side_effect=ok_sandbox_sql):
            with patch.object(mcp, "sandbox_table", side_effect=ok_sandbox_table):
                reply = mcp_call(mcp, "validate_exercise", {"lesson": lesson})
        self.assertTrue(mcp_is_error(reply))
        payload = mcp_payload(reply)
        blob = " ".join(payload.get("errors") or [])
        self.assertIn("richtig=[1, 3]", blob)

    def test_save_practice_reachable_true(self):
        mcp = self.mcp
        live = {
            "home": "/tmp/live",
            "workshop_dir": None,
            "flaskPid": 31512,
            "appPort": 8081,
            "pid_alive": True,
            "http_ok": True,
            "app_url": "http://127.0.0.1:8081",
        }
        with tempfile.TemporaryDirectory() as tmp:
            live["home"] = tmp
            live["workshop_dir"] = tmp
            with patch.object(mcp, "live_install", return_value=live):
                with patch.object(mcp, "sandbox_sql", side_effect=ok_sandbox_sql):
                    with patch.object(mcp, "http_get", return_value=(200, "http://127.0.0.1:8081/playground/ws-mcp-del")):
                        reply = mcp_call(mcp, "save_practice", {"lesson": VALID_PLAYGROUND_LESSON})
            self.assertFalse(mcp_is_error(reply))
            payload = mcp_payload(reply)
            self.assertTrue(payload["reachable"])
            self.assertIn("http://127.0.0.1:8081/playground/ws-mcp-del", payload["url"])
            self.assertTrue((Path(tmp) / "ws-mcp-del.json").is_file())

    def test_save_practice_unreachable_is_error(self):
        mcp = self.mcp
        with tempfile.TemporaryDirectory() as tmp:
            live = {
                "home": tmp,
                "workshop_dir": tmp,
                "flaskPid": 31512,
                "appPort": 8081,
                "pid_alive": True,
                "http_ok": True,
                "app_url": "http://127.0.0.1:8081",
            }
            with patch.object(mcp, "live_install", return_value=live):
                with patch.object(mcp, "sandbox_sql", side_effect=ok_sandbox_sql):
                    with patch.object(mcp, "http_get", return_value=(404, "http://127.0.0.1:8081/playground/ws-mcp-del")):
                        reply = mcp_call(mcp, "save_practice", {"lesson": VALID_PLAYGROUND_LESSON})
            self.assertTrue(mcp_is_error(reply))
            payload = mcp_payload(reply)
            self.assertEqual(payload.get("reachable"), False)
            self.assertIn("31512", payload.get("error") or "")

    def test_connect_error_is_actionable(self):
        mcp = self.mcp
        failed = {
            "ok": False,
            "error": "Verbindung fehlgeschlagen",
            "pg_error": 'connection to server at "db" (13.248.169.48), port 5432 failed: timeout expired',
        }
        with patch.object(mcp, "sandbox_sql", return_value=failed):
            reply = mcp_call(mcp, "run_sql", {"sql": "SELECT 1"})
        self.assertTrue(mcp_is_error(reply))
        text = reply["result"]["content"][0]["text"]
        self.assertIn("LEARN_SQL_HOME", text)
        self.assertIn("DB", text)

    def test_sql_tools_do_not_import_flask(self):
        src = (REPO / "mcp" / "learnsql_mcp.py").read_text(encoding="utf-8")
        self.assertNotIn("import app as flask_app", src)
        self.assertNotIn("test_client", src)
        listed = self.mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        names = {t["name"]: t for t in listed["result"]["tools"]}
        for tool in ("sample_rows", "table_rows"):
            table = names[tool]["inputSchema"]["properties"]["table"]
            self.assertNotIn("enum", table, msg=tool)
            self.assertIn("orders", table["description"])


class WorkshopRuntimeTests(unittest.TestCase):
    def test_sitecustomize_adds_app_dir(self):
        import importlib.util

        src = REPO / "installer" / "runtime" / "sitecustomize.py"
        self.assertTrue(src.is_file())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            python_dir = root / "python"
            app_dir = root / "app"
            python_dir.mkdir()
            app_dir.mkdir()
            dest = python_dir / "sitecustomize.py"
            dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            spec = importlib.util.spec_from_file_location("sitecustomize_bundled", dest)
            mod = importlib.util.module_from_spec(spec)
            saved = list(sys.path)
            try:
                spec.loader.exec_module(mod)
                self.assertEqual(Path(sys.path[0]).resolve(), app_dir.resolve())
            finally:
                sys.path[:] = saved

    def test_ensure_app_on_path_recovers_lessons(self):
        import app as flask_app

        app_dir = Path(flask_app.__file__).resolve().parent
        saved = list(sys.path)
        popped = {}
        try:
            sys.path[:] = [p for p in sys.path if Path(p).resolve() != app_dir]
            for name in list(sys.modules):
                if name == "lessons" or name.startswith("lessons."):
                    popped[name] = sys.modules.pop(name)
            flask_app.ensure_app_on_path()
            self.assertEqual(Path(sys.path[0]).resolve(), app_dir)
            from lessons.academy_data import ACADEMY
            self.assertTrue(ACADEMY["lessons"])
        finally:
            sys.path[:] = saved
            sys.modules.update(popped)

    def test_mcp_install_merges_and_reads_runtime_port(self):
        sys.path.insert(0, str(REPO / "mcp"))
        import install_mcp

        existing = {"mcpServers": {"other": {"command": "keep-me"}}}
        entry = {"command": "py", "args": ["mcp.py"]}
        merged = install_mcp.merge_mcp_config(existing, "learnsql", entry)
        self.assertEqual(merged["mcpServers"]["other"]["command"], "keep-me")
        self.assertEqual(merged["mcpServers"]["learnsql"]["command"], "py")

        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            user_home = home / "userhome"
            user_home.mkdir()
            (home / "mcp").mkdir()
            claude_dir = home / "Claude"
            claude_dir.mkdir()
            (claude_dir / "claude_desktop_config.json").write_text(
                json.dumps(existing), encoding="utf-8"
            )
            env = {
                "APPDATA": tmp,
                "LOCALAPPDATA": str(home / "local"),
                "HOME": str(user_home),
                "USERPROFILE": str(user_home),
                "CLAUDE_CONFIG_DIR": "",
            }
            with patch.dict("os.environ", env, clear=False):
                status = install_mcp.install(home)
            desktop = Path(tmp) / "Claude" / "claude_desktop_config.json"
            code = user_home / ".claude.json"
            self.assertIn(str(desktop), status["targets"])
            self.assertIn(str(code), status["targets"])
            self.assertIn("Claude Desktop", status["clients"])
            self.assertIn("Claude Code", status["clients"])
            self.assertTrue(desktop.is_file())
            self.assertTrue((desktop.parent / (desktop.name + ".bak")).is_file())
            saved = json.loads(desktop.read_text(encoding="utf-8"))
            self.assertEqual(saved["mcpServers"]["other"]["command"], "keep-me")
            self.assertEqual(saved["mcpServers"]["learnsql"]["env"]["LEARN_SQL_HOME"], str(home.resolve()))
            code_saved = json.loads(code.read_text(encoding="utf-8"))
            self.assertEqual(code_saved["mcpServers"]["learnsql"]["env"]["LEARN_SQL_HOME"], str(home.resolve()))
            self.assertTrue((home / "workshop").is_dir())
            self.assertTrue((home / "mcp-status.json").is_file())

            (home / "runtime.json").write_text(json.dumps({"dbPort": 15432}), encoding="utf-8")
            with patch.dict("os.environ", {"LEARN_SQL_HOME": str(home)}, clear=False):
                os.environ.pop("DB_PORT", None)
                os.environ.pop("WORKSHOP_DIR", None)
                applied = install_mcp.apply_runtime_env(home)
                self.assertEqual(os.environ.get("DB_PORT"), "15432")
                self.assertTrue(str(applied["workshop"]).endswith("workshop"))
            entry_with_port = install_mcp.learnsql_server_entry(home)
            self.assertEqual(entry_with_port["env"]["DB_PORT"], "15432")
            self.assertEqual(entry_with_port["args"][0], "-u")
            self.assertEqual(entry_with_port["env"]["PYTHONUNBUFFERED"], "1")

            with patch.dict("os.environ", env, clear=False):
                gone = install_mcp.uninstall(home)
            after = json.loads(desktop.read_text(encoding="utf-8"))
            self.assertNotIn("learnsql", after.get("mcpServers") or {})
            self.assertIn("other", after["mcpServers"])
            code_after = json.loads(code.read_text(encoding="utf-8"))
            self.assertNotIn("learnsql", code_after.get("mcpServers") or {})
            self.assertTrue(gone["removed"])

    def test_mcp_install_skips_invalid_json(self):
        sys.path.insert(0, str(REPO / "mcp"))
        import install_mcp

        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            user_home = home / "userhome"
            user_home.mkdir()
            claude_dir = home / "Claude"
            claude_dir.mkdir()
            broken = claude_dir / "claude_desktop_config.json"
            broken.write_text("{not-json", encoding="utf-8")
            env = {
                "APPDATA": tmp,
                "LOCALAPPDATA": str(home / "local"),
                "HOME": str(user_home),
                "USERPROFILE": str(user_home),
                "CLAUDE_CONFIG_DIR": "",
            }
            with patch.dict("os.environ", env, clear=False):
                status = install_mcp.install(home)
            self.assertIn(str(broken), status["skipped"])
            self.assertEqual(broken.read_text(encoding="utf-8"), "{not-json")
            self.assertTrue((user_home / ".claude.json").is_file())

    def test_wissen_cards_and_playground_routes(self):
        import app as flask_app

        client = flask_app.app.test_client()
        wissen = client.get("/wissen")
        self.assertEqual(wissen.status_code, 200)
        self.assertIn("PostgreSQL-Bibel".encode("utf-8"), wissen.data)
        article = client.get("/wissen/select")
        self.assertEqual(article.status_code, 200)
        self.assertIn(b"SELECT", article.data)
        cards = client.get("/cards")
        self.assertEqual(cards.status_code, 200)
        self.assertIn("Nur fällige".encode("utf-8"), cards.data)
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict("os.environ", claude_sandbox_env(tmp), clear=False):
                shop = client.get("/playground")
                wissen_nav = client.get("/wissen")
                old = client.get("/werkstatt")
        self.assertEqual(shop.status_code, 200)
        self.assertEqual(old.status_code, 301)
        self.assertIn("/playground", old.headers.get("Location", ""))
        self.assertIn("SQL-Playground".encode("utf-8"), shop.data)
        self.assertNotIn("Werkstatt".encode("utf-8"), shop.data)
        self.assertNotIn(b"pg-editor", shop.data)
        self.assertIn("offenen Aufträgen".encode("utf-8"), shop.data)
        self.assertIn("Claude Desktop".encode("utf-8"), shop.data)
        self.assertIn("Claude Code".encode("utf-8"), shop.data)
        self.assertNotIn("Cursor".encode("utf-8"), shop.data)
        shop_html = shop.data.decode("utf-8")
        self.assertIn("Mit Claude verbinden", shop_html)
        self.assertIn("MCP · nicht installiert", shop_html)
        self.assertLess(shop_html.find("Noch keine Übungen"), shop_html.find("Einrichten"))
        self.assertIn('<details class="card mcp-help mcp-setup">', shop_html)
        self.assertNotIn('<details class="card mcp-help mcp-setup" open>', shop_html)
        self.assertIn("MCP · nicht installiert", wissen_nav.data.decode("utf-8"))
        self.assertIn("Claude-Buddy", shop_html)
        self.assertIn("buddy-panel", shop_html)
        self.assertIn('id="buddy-fab"', shop_html)
        with tempfile.TemporaryDirectory() as tmp:
            env = claude_sandbox_env(tmp)
            desktop = Path(tmp) / "Claude"
            desktop.mkdir()
            (desktop / "claude_desktop_config.json").write_text(
                json.dumps({"mcpServers": {"learnsql": {"command": "py"}}}),
                encoding="utf-8",
            )
            with patch.dict("os.environ", env, clear=False):
                flagged = client.get("/playground")
                nav = client.get("/")
        flagged_html = flagged.data.decode("utf-8")
        self.assertIn("verbunden mit Claude", flagged_html)
        self.assertNotIn("Einrichten", flagged_html)
        self.assertNotIn("Mit Claude verbinden", flagged_html)
        self.assertIn("MCP · verbunden mit Claude", nav.data.decode("utf-8"))
        lesson = client.get("/learn/ch-agg")
        self.assertEqual(lesson.status_code, 200)
        self.assertIn("Summen".encode("utf-8"), lesson.data)
        lesson_html = lesson.data.decode("utf-8")
        self.assertIn("Claude-Buddy", lesson_html)
        self.assertIn("Claude erklärt mit", lesson_html)
        self.assertIn("gleichartige Zeilen", lesson_html)
        self.assertIn("buddy-panel", lesson_html)
        missing = client.get("/wissen/gibt-es-nicht")
        self.assertEqual(missing.status_code, 404)

    def test_playground_player_and_delete(self):
        import app as flask_app
        from lessons import workshop as ws

        client = flask_app.app.test_client()
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict("os.environ", {"WORKSHOP_DIR": tmp}):
                ws.save_workshop_lesson({
                    "id": "ws-player-label",
                    "title": "Offene zählen",
                    "goal": "Zähle offene Aufträge.",
                    "steps": [{
                        "type": "write",
                        "title": "Zählen",
                        "prompt": "Wie viele offene Aufträge?",
                        "solution": "SELECT COUNT(*) FROM orders WHERE status = 'offen';",
                        "hints": ["COUNT(*)", "WHERE status = 'offen'"],
                    }],
                })
                listing = client.get("/playground")
                listing_html = listing.data.decode("utf-8")
                self.assertIn("Deine Übungen", listing_html)
                self.assertIn("path-card", listing_html)
                self.assertIn("path-playground", listing_html)
                self.assertIn("Löschen", listing_html)
                if "Einrichten" in listing_html:
                    self.assertLess(listing_html.find("Deine Übungen"), listing_html.find("Einrichten"))
                page = client.get("/playground/ws-player-label")
                old = client.get("/werkstatt/ws-player-label")
                blocked = client.post("/api/playground/ch0/delete")
                gone = client.post("/api/playground/ws-player-label/delete")
                missing = client.post("/api/playground/ws-player-label/delete")
        self.assertEqual(page.status_code, 200)
        html = page.data.decode("utf-8")
        self.assertIn("SQL-Playground", html)
        self.assertNotIn("Kapitel W", html)
        self.assertIn("Zum Playground", html)
        self.assertIn('data-workshop="1"', html)
        self.assertEqual(old.status_code, 301)
        self.assertIn("/playground/ws-player-label", old.headers.get("Location", ""))
        self.assertEqual(blocked.status_code, 400)
        self.assertFalse(blocked.get_json().get("ok"))
        self.assertEqual(gone.status_code, 200)
        self.assertTrue(gone.get_json().get("ok"))
        self.assertEqual(missing.status_code, 404)

    def test_mcp_probe_and_connect_from_app(self):
        sys.path.insert(0, str(REPO / "mcp"))
        import install_mcp
        import app as flask_app

        with tempfile.TemporaryDirectory() as tmp:
            env = claude_sandbox_env(tmp)
            with patch.dict("os.environ", env, clear=False):
                empty = install_mcp.probe_status(Path(tmp))
                self.assertFalse(empty["installed"])
                desktop = Path(tmp) / "Claude"
                desktop.mkdir()
                (desktop / "claude_desktop_config.json").write_text(
                    json.dumps({"mcpServers": {"learnsql": {"command": "py"}}}),
                    encoding="utf-8",
                )
                found = install_mcp.probe_status(Path(tmp))
                self.assertTrue(found["installed"])
                self.assertIn("Claude Desktop", found["clients"])

        with tempfile.TemporaryDirectory() as tmp:
            env = claude_sandbox_env(tmp)
            client = flask_app.app.test_client()
            with patch.dict("os.environ", env, clear=False):
                res = client.post("/api/mcp/connect")
                payload = res.get_json()
                self.assertTrue(payload["ok"], msg=payload)
                self.assertTrue(payload["status"]["installed"])
                code = Path(tmp) / "userhome" / ".claude.json"
                self.assertTrue(code.is_file())
                saved = json.loads(code.read_text(encoding="utf-8"))
                self.assertIn("learnsql", saved.get("mcpServers") or {})
                page = client.get("/playground")
            html = page.data.decode("utf-8")
            self.assertIn("verbunden mit Claude", html)
            self.assertNotIn("Einrichten", html)


class BuddyAndExplainTests(unittest.TestCase):
    def test_enrich_lesson_adds_teach_and_related(self):
        from lessons.buddy import enrich_lesson

        ch3 = enrich_lesson(lesson_by_id("ch3"))
        writes = [s for s in ch3["steps"] if s["type"] == "write"]
        self.assertTrue(writes)
        self.assertGreaterEqual(len(writes[0].get("teach") or ""), 40)
        self.assertTrue(ch3.get("related"))
        self.assertTrue(any(s.get("related") for s in writes))

    def test_buddy_context_roundtrip(self):
        import app as flask_app

        client = flask_app.app.test_client()
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict("os.environ", {"WORKSHOP_DIR": tmp}):
                posted = client.post("/api/buddy/context", json={
                    "page": "learn",
                    "url": "/learn/ch3",
                    "lesson_id": "ch3",
                    "lesson_title": "WHERE",
                    "step": 2,
                    "step_type": "write",
                    "step_title": "Offene Aufträge",
                    "last_sql": "SELECT * FROM orders WHERE status = offen",
                    "last_coach": "Textwerte brauchen Anführungszeichen.",
                    "progress": {"completed": ["ch0"], "current": "ch3", "chapters_done": 1, "chapters_total": 20},
                })
                self.assertTrue(posted.get_json()["ok"])
                got = client.get("/api/buddy/context")
        payload = got.get_json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["context"]["lesson_id"], "ch3")
        self.assertIn("status = offen", payload["context"]["last_sql"])
        self.assertEqual(payload["context"]["progress"]["completed"], ["ch0"])

    def test_mcp_buddy_tools_and_explain_required(self):
        sys.path.insert(0, str(REPO / "mcp"))
        import learnsql_mcp as mcp
        from lessons.buddy import save_learner_context

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict("os.environ", {"WORKSHOP_DIR": tmp}):
                save_learner_context({
                    "page": "learn",
                    "lesson_id": "ch3",
                    "lesson_title": "WHERE",
                    "step": 0,
                    "step_type": "look",
                    "step_title": "Filter",
                })
                with patch.object(mcp, "sandbox_sql", side_effect=ok_sandbox_sql):
                    buddy = mcp_call(mcp, "buddy_context", {})
                    help_reply = mcp_call(mcp, "help_with", {"q": "Was macht WHERE?"})
                    search = mcp_call(mcp, "search_path", {"q": "WHERE"})
                    coach = mcp_call(mcp, "coach_sql", {"sql": "SELECT * FROM orders WHERE status = offen"})
                    thin = copy.deepcopy(VALID_PLAYGROUND_LESSON)
                    thin["id"] = "ws-no-explain"
                    thin["steps"] = [
                        {"type": "look", "title": "Frage", "text": "Nur schauen, keine Erklärung."},
                        {
                            "type": "write",
                            "title": "Zählen",
                            "prompt": "Wie viele offene Aufträge?",
                            "solution": "SELECT COUNT(*) FROM orders WHERE status = 'offen';",
                            "teach": "WHERE filtert Zeilen, COUNT zählt danach die übrig gebliebenen.",
                        },
                    ]
                    rejected = mcp_call(mcp, "validate_exercise", {"lesson": thin})
        self.assertFalse(mcp_is_error(buddy))
        snap = mcp_payload(buddy)
        self.assertEqual(snap["lesson"]["id"], "ch3")
        self.assertIn("buddy_context", snap["how_to_help"])
        self.assertFalse(mcp_is_error(help_reply))
        pack = mcp_payload(help_reply)
        self.assertTrue(pack.get("teach") or pack.get("hits") or pack.get("articles"))
        self.assertFalse(mcp_is_error(search))
        self.assertTrue(mcp_payload(search)["results"])
        self.assertFalse(mcp_is_error(coach))
        coach_payload = mcp_payload(coach)
        self.assertTrue(coach_payload.get("plain") or coach_payload.get("coach"))
        self.assertIsNone(coach_payload.get("solution"))
        self.assertTrue(mcp_is_error(rejected))
        blob = " ".join(mcp_payload(rejected).get("errors") or [])
        self.assertIn("explain", blob)

    def test_sql_coach_explain_parts(self):
        from sql_coach import explain_step_parts

        plain, parts = explain_step_parts("SELECT id FROM orders WHERE status = 'offen'")
        self.assertIn("orders", plain.lower())
        self.assertGreaterEqual(len(parts), 2)
        tokens = {p["token"] for p in parts}
        self.assertIn("SELECT", tokens)
        self.assertIn("FROM", tokens)


class ClaudeBuddyChatTests(unittest.TestCase):
    """The in-app buddy runs the local `claude` CLI; none of this needs one."""

    CANNED = [
        json.dumps({"type": "active_goal", "value": None}),
        # ~25 KB of housekeeping the CLI emits before anything useful.
        json.dumps({"type": "system", "subtype": "commands_changed", "commands": ["x" * 400]}),
        json.dumps({
            "type": "system", "subtype": "init", "session_id": "sess-1",
            "model": "claude-sonnet-5",
            "mcp_servers": [{"name": "learnsql", "status": "connected"}],
        }),
        json.dumps({"type": "stream_event", "event": {
            "type": "content_block_delta",
            "delta": {"type": "text_delta", "text": "Weil WHERE "}}}),
        json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "ToolSearch"},
            {"type": "tool_use", "name": "mcp__learnsql__buddy_context"}]}}),
        # subagent chatter must not reach the learner
        json.dumps({"type": "assistant", "parent_tool_use_id": "t1", "message": {"content": [
            {"type": "tool_use", "name": "mcp__learnsql__run_sql"}]}}),
        "das ist kein json",
        json.dumps({"type": "stream_event", "event": {
            "type": "content_block_delta",
            "delta": {"type": "text_delta", "text": "filtert."}}}),
        json.dumps({
            "type": "result", "subtype": "success", "is_error": False,
            "result": "Weil WHERE filtert.", "session_id": "sess-1",
            "total_cost_usd": 0.01, "permission_denials": [],
        }),
    ]

    def _fake_proc(self, lines, rc=0, stderr=""):
        import io

        class FakeProc:
            pid = 4242

            def __init__(self):
                self.stdout = io.StringIO("".join(line + "\n" for line in lines))
                self.stderr = io.StringIO(stderr)
                self.returncode = rc

            def poll(self):
                return self.returncode

            def wait(self, timeout=None):
                return self.returncode

        return FakeProc()

    def test_iter_events_keeps_only_what_the_drawer_needs(self):
        import claude_cli

        events = list(claude_cli.iter_events(self.CANNED))
        names = [name for name, _ in events]
        self.assertEqual(names, ["init", "delta", "tool", "delta", "done"])

        payloads = dict(zip(names, [p for _, p in events]))
        self.assertTrue(payloads["init"]["mcp_ok"])
        self.assertEqual(payloads["init"]["session_id"], "sess-1")
        # ToolSearch is Claude Code plumbing, not buddy progress.
        self.assertEqual([p["name"] for n, p in events if n == "tool"], ["buddy_context"])
        self.assertEqual(payloads["done"]["session_id"], "sess-1")
        self.assertTrue(payloads["done"]["ok"])

    def test_allowed_tools_match_the_mcp_server(self):
        """Adding a 21st MCP tool must not silently stay unreachable."""
        import claude_cli

        sys.path.insert(0, str(REPO / "mcp"))
        import learnsql_mcp as mcp

        listed = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        names = {t["name"] for t in listed["result"]["tools"]}
        self.assertEqual(set(claude_cli.ALLOWED_TOOLS), names)

    def test_argv_is_locked_down(self):
        import claude_cli

        argv = claude_cli.build_argv(
            "Frage", mcp_path="/tmp/m.json", cli_path="/x/claude", version=(2, 1, 270)
        )
        self.assertEqual(argv[0], "/x/claude")
        self.assertEqual(argv[argv.index("-p") + 1], "Frage")
        self.assertEqual(argv[argv.index("--output-format") + 1], "stream-json")
        for flag in ("--verbose", "--include-partial-messages", "--strict-mcp-config"):
            self.assertIn(flag, argv)
        # --bare would refuse the OAuth login and demand an API key.
        self.assertNotIn("--bare", argv)
        self.assertNotIn("--resume", argv)

        allowed = argv[argv.index("--allowedTools") + 1:argv.index("--disallowedTools")]
        self.assertIn("mcp__learnsql__buddy_context", allowed)
        self.assertIn("mcp__learnsql__save_practice", allowed)
        self.assertNotIn("Bash", allowed)
        self.assertIn("Bash", argv)  # ...but it is explicitly denied
        self.assertIn("Write", argv)

        resumed = claude_cli.build_argv(
            "Frage", mcp_path="/tmp/m.json", session_id="abc-123",
            cli_path="/x/claude", version=(2, 1, 270),
        )
        self.assertEqual(resumed[resumed.index("--resume") + 1], "abc-123")

    def test_old_cli_does_not_get_unknown_flags(self):
        """An unknown option makes the CLI exit before emitting any JSON."""
        import claude_cli

        old = claude_cli.build_argv("F", cli_path="/x/claude", version=(2, 1, 100))
        self.assertNotIn("--permission-prompts", old)
        new = claude_cli.build_argv("F", cli_path="/x/claude", version=(2, 1, 270))
        self.assertIn("--permission-prompts", new)

    def test_child_env_drops_inherited_claude_and_api_keys(self):
        import claude_cli

        dirty = {
            "CLAUDE_CODE_SESSION_ID": "parent-session",
            "CLAUDECODE": "1",
            "ANTHROPIC_API_KEY": "sk-should-not-survive",
            "PATH": os.environ.get("PATH", ""),
        }
        with patch.dict(os.environ, dirty, clear=False):
            env = claude_cli.build_env()
        self.assertEqual([k for k in env if k.startswith("CLAUDE")], [])
        # The point of the feature is the subscription, not a billed API key.
        self.assertNotIn("ANTHROPIC_API_KEY", env)
        self.assertEqual(env.get("MCP_TIMEOUT"), "60000")

    def test_mcp_config_points_at_the_apps_own_workshop(self):
        """Otherwise buddy_context reads a different .learner-context.json."""
        import claude_cli
        from lessons.workshop import workshop_dir

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"WORKSHOP_DIR": tmp}, clear=False):
                path = claude_cli.mcp_config_path(Path(tmp))
                self.assertIsNotNone(path)
                data = json.loads(Path(path).read_text(encoding="utf-8"))
                entry = data["mcpServers"]["learnsql"]
                self.assertTrue(entry["args"][-1].endswith("learnsql_mcp.py"))
                self.assertEqual(entry["env"]["WORKSHOP_DIR"], str(workshop_dir()))

    def test_mcp_child_runs_on_this_interpreter(self):
        """A venv's python symlinks out to the system one.

        install_mcp does Path(sys.executable).resolve(), which follows that
        symlink to an interpreter without psycopg2 — every run_sql then dies
        with "psycopg2 ist nicht installiert".
        """
        import claude_cli

        with tempfile.TemporaryDirectory() as tmp:
            path = claude_cli.mcp_config_path(Path(tmp))
            entry = json.loads(Path(path).read_text(encoding="utf-8"))["mcpServers"]["learnsql"]
        self.assertEqual(entry["command"], sys.executable)

    def test_chat_route_streams_sse(self):
        import app as flask_app
        import claude_cli

        status = {"available": True, "path": "/x/claude", "version": "2.1.270", "parsed": (2, 1, 270)}
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"WORKSHOP_DIR": tmp}, clear=False):
                with patch.object(flask_app, "claude_status", return_value=status):
                    with patch.object(flask_app, "spawn", return_value=self._fake_proc(self.CANNED)):
                        with patch.object(flask_app, "terminate", return_value=None):
                            client = flask_app.app.test_client()
                            res = client.post("/api/buddy/chat", json={
                                "question": "Warum WHERE?",
                                "chat_id": "testchat1234",
                                "context": {"page": "learn", "lesson_id": "ch3", "step": 2},
                            })
                            body = res.get_data(as_text=True)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["Content-Type"].split(";")[0], "text/event-stream")
        for marker in ("event: start", "event: init", "event: delta", "event: done"):
            self.assertIn(marker, body)
        self.assertIn("Weil WHERE ", body)
        # None of the CLI's housekeeping may reach the browser.
        self.assertNotIn("commands_changed", body)
        self.assertNotIn("ToolSearch", body)
        self.assertNotIn("das ist kein json", body)

    def test_chat_without_cli_is_a_clean_503(self):
        import app as flask_app

        with patch.object(flask_app, "claude_status", return_value={"available": False}):
            client = flask_app.app.test_client()
            res = client.post("/api/buddy/chat", json={
                "question": "Hallo", "chat_id": "testchat1234",
            })
        self.assertEqual(res.status_code, 503)
        self.assertEqual(res.get_json()["code"], "no_cli")

    def test_chat_rejects_a_bogus_chat_id(self):
        import app as flask_app

        client = flask_app.app.test_client()
        res = client.post("/api/buddy/chat", json={"question": "Hi", "chat_id": "../../etc"})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json()["code"], "bad_id")

    def test_stale_session_is_explained_not_dumped(self):
        import claude_cli

        info = claude_cli.explain_failure(1, "No conversation found with session ID: dead", resumed=True)
        self.assertEqual(info["code"], "stale_session")
        auth = claude_cli.explain_failure(1, "Invalid API key · Please run /login", resumed=False)
        self.assertEqual(auth["code"], "auth")
        self.assertIn("anmelden", auth["text"])
        old = claude_cli.explain_failure(1, "error: unknown option '--permission-prompts'", resumed=False)
        self.assertEqual(old["code"], "old_cli")

    def test_drawer_shows_chat_or_install_hint_and_never_the_clipboard(self):
        import app as flask_app

        client = flask_app.app.test_client()
        for available, present, absent in (
            (True, "buddy-send", "Claude Code nicht gefunden"),
            (False, "Claude Code nicht gefunden", "buddy-send"),
        ):
            with patch.object(flask_app, "claude_status", return_value={"available": available}):
                html = client.get("/learn/ch0").get_data(as_text=True)
            self.assertIn(present, html)
            self.assertNotIn(absent, html)
            # The copy-the-prompt workaround is gone for good.
            self.assertNotIn("Prompt für Claude kopieren", html)
            self.assertNotIn("buddy-preview", html)
            self.assertNotIn("buddy-copy", html)


class DocsMatchRealityTests(unittest.TestCase):
    """The app used to call no model at all. It does now — say so."""

    STALE = (
        "Die App ruft kein LLM auf",
        "Die App ruft kein Sprachmodell auf",
        "Prompt für Claude kopieren",
    )

    def test_docs_do_not_claim_the_app_calls_no_model(self):
        for name in ("README.md", "mcp/ANLEITUNG.md"):
            text = (REPO / name).read_text(encoding="utf-8")
            for phrase in self.STALE:
                self.assertNotIn(phrase, text, f"{name} still claims: {phrase}")


if __name__ == "__main__":
    unittest.main()
