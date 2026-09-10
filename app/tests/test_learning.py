"""Unit tests for learner feedback and academy metadata (no database)."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))

from lessons.academy_data import ACADEMY, CLIENTS, ORDERS, lesson_by_id  # noqa: E402
from lessons.generate import LESSONS as GENERATED_LESSONS  # noqa: E402
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
)
FORBIDDEN_CLIENT_TOKENS = (
    re.compile(r"['\"]ETE['\"]"),
    re.compile(r"\bRed-Bull\b", re.I),
)

SKIP_NAME = {"test_learning.py"}


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
        msg = friendly_sql_error("syntax error", "SELECT * FROM stock WHERE weight = NULL", sandbox="learn")
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


class AcademyContentTests(unittest.TestCase):
    def test_every_lesson_has_goal_interaction_and_quiz(self):
        self.assertGreaterEqual(len(ACADEMY["lessons"]), 12)
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

    def test_lookup(self):
        self.assertEqual(lesson_by_id("ch3")["title"], "WHERE")
        self.assertEqual(lesson_by_id("ch7")["title"], "NULL — fehlende Werte")
        self.assertIsNone(lesson_by_id("missing"))

    def test_anonymized_clients(self):
        names = {c["name"] for c in CLIENTS}
        self.assertEqual(names, {"Helio", "Alpin", "Nordkai", "Westfeld"})
        self.assertTrue(any(r["client_id"] is None for r in ORDERS))
        self.assertTrue(any(r["quantity"] is None for r in ORDERS))
        self.assertGreaterEqual(len(ORDERS), 20)

    def test_join_and_null_chapters_exist(self):
        ids = [l["id"] for l in ACADEMY["lessons"]]
        for needed in ("ch7", "ch8", "ch9", "ch10", "challenge-1", "challenge-2"):
            self.assertIn(needed, ids)


class NoCustomerNamesTests(unittest.TestCase):
    def test_repo_has_no_customer_names(self):
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
                if "vendor" in path.parts:
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
        self.assertEqual(hits, [], msg="Echte Kundennamen/Hashes im Repo:\n" + "\n".join(hits))


class WmxLessonsTests(unittest.TestCase):
    def test_generate_matches_lessons_json(self):
        path = ROOT / "lessons" / "lessons.json"
        on_disk = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(
            on_disk,
            GENERATED_LESSONS,
            msg="lessons.json weicht von generate.py ab — generate.py ausführen.",
        )

    def test_required_quizzes_and_transfer_exercises(self):
        by_id = {lesson["id"]: lesson for lesson in GENERATED_LESSONS}
        for needed in ("sql", "a", "d", "e", "f", "i"):
            quiz = by_id[needed].get("quiz") or []
            self.assertGreaterEqual(len(quiz), 4, msg=f"{needed} needs a Kurzcheck")
        self.assertTrue(by_id["b"].get("exercises"), msg="B braucht eine Mini-Übung")
        self.assertGreaterEqual(len(by_id["sql"].get("exercises") or []), 4)
        self.assertGreaterEqual(len(by_id["i"].get("exercises") or []), 2)
        self.assertGreaterEqual(len(by_id["n"].get("exercises") or []), 2)

    def test_cte_exercises_are_written_not_filled(self):
        by_id = {lesson["id"]: lesson for lesson in GENERATED_LESSONS}
        exercises = {
            ex["id"]: ex
            for lesson in by_id.values()
            for ex in (lesson.get("exercises") or [])
        }
        for ex_id in ("a-ex3", "k-ex2", "o-ex1"):
            starter = exercises[ex_id].get("starter") or ""
            self.assertNotIn("WHERE rn", starter)
            self.assertNotIn("ROW_NUMBER", starter)
            self.assertIn("ROW_NUMBER", exercises[ex_id]["solution"])

    def test_wmx_last_hint_is_not_the_solution(self):
        for lesson in GENERATED_LESSONS:
            for ex in lesson.get("exercises") or []:
                hints = ex.get("hints") or []
                self.assertTrue(hints, msg=f"{ex['id']} needs hints")
                last = re.sub(r"\s+", " ", hints[-1].replace(";", "")).strip().lower()
                sol = re.sub(r"\s+", " ", (ex["solution"] or "").replace(";", "")).strip().lower()
                self.assertNotEqual(last, sol, msg=f"{ex['id']} last hint is the full solution")


if __name__ == "__main__":
    unittest.main()
