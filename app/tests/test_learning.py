"""Unit tests for learner feedback and academy metadata (no database)."""
from __future__ import annotations

import re
import unittest
from pathlib import Path
from unittest.mock import patch
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
            "ch0", "ch7", "ch-alias", "ch8", "ch-having", "ch-keys",
            "ch9", "ch10", "ch-dml", "ch-tx", "ch-pg", "challenge-3",
        ):
            self.assertIn(needed, ids)

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


if __name__ == "__main__":
    unittest.main()
