"""Unit tests for learner feedback and academy metadata (no database)."""
from __future__ import annotations

import json
import os
import re
import tempfile
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

    def test_mcp_lists_tools_and_drafts(self):
        sys.path.insert(0, str(REPO / "mcp"))
        import learnsql_mcp as mcp

        listed = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        names = {t["name"] for t in listed["result"]["tools"]}
        for needed in ("schema", "run_sql", "search_wissen", "draft_exercise", "save_practice"):
            self.assertIn(needed, names)
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
        self.assertTrue(payload["steps"])

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

    def test_wissen_cards_and_werkstatt_routes(self):
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
        shop = client.get("/werkstatt")
        self.assertEqual(shop.status_code, 200)
        self.assertIn("Werkstatt".encode("utf-8"), shop.data)
        self.assertIn("offenen Aufträgen".encode("utf-8"), shop.data)
        self.assertIn("Claude Desktop".encode("utf-8"), shop.data)
        self.assertIn("Claude Code".encode("utf-8"), shop.data)
        self.assertIn("Cursor".encode("utf-8"), shop.data)
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "mcp-status.json").write_text(
                json.dumps({"installed": True, "targets": ["x"]}), encoding="utf-8"
            )
            with patch.dict("os.environ", {"LEARN_SQL_HOME": tmp}, clear=False):
                flagged = client.get("/werkstatt")
        self.assertIn("learnsql ist in Claude eingetragen".encode("utf-8"), flagged.data)
        lesson = client.get("/learn/ch-agg")
        self.assertEqual(lesson.status_code, 200)
        self.assertIn("Summen".encode("utf-8"), lesson.data)
        missing = client.get("/wissen/gibt-es-nicht")
        self.assertEqual(missing.status_code, 404)


if __name__ == "__main__":
    unittest.main()
