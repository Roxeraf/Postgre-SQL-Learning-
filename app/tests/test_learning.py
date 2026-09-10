"""Unit tests for learner feedback and academy metadata (no database)."""
from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lessons.academy_data import ACADEMY, lesson_by_id  # noqa: E402
from sql_coach import (  # noqa: E402
    diagnose_structure,
    explain_sql,
    friendly_sql_error,
    has_empty_select_list,
    uses_equals_null,
)


class SqlCoachTests(unittest.TestCase):
    def test_missing_from_is_a_learning_message(self):
        msg = diagnose_structure("SELECT order_number", "SELECT order_number FROM orders")
        self.assertIn("FROM", msg)
        self.assertIn("woher", msg.lower())
        self.assertNotIn("SELECT SELECT", msg)

    def test_and_vs_or(self):
        msg = diagnose_structure(
            "SELECT * FROM orders WHERE client = 'Red Bull' OR status = 'open'",
            "SELECT * FROM orders WHERE client = 'Red Bull' AND status = 'open'",
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
            "SELECT client, COUNT(*) FROM orders WHERE status = 'open' GROUP BY client ORDER BY COUNT(*) DESC"
        )["parts"]
        keys = [p["key"] for p in parts]
        self.assertLess(keys.index("FROM"), keys.index("WHERE"))
        self.assertLess(keys.index("WHERE"), keys.index("GROUP BY"))
        self.assertLess(keys.index("GROUP BY"), keys.index("SELECT"))


class AcademyContentTests(unittest.TestCase):
    def test_every_lesson_has_goal_and_interaction(self):
        self.assertGreaterEqual(len(ACADEMY["lessons"]), 7)
        for lesson in ACADEMY["lessons"]:
            self.assertTrue(lesson["goal"])
            self.assertTrue(lesson["steps"])
            types = {s["type"] for s in lesson["steps"]}
            self.assertTrue(types - {"look"}, msg=f"{lesson['id']} needs an active step")

    def test_sql_steps_have_solutions(self):
        for lesson in ACADEMY["lessons"]:
            for i, step in enumerate(lesson["steps"]):
                if step["type"] in {"write", "build", "fill", "apply", "challenge"}:
                    self.assertTrue(step.get("solution"), f"{lesson['id']} step {i}")
                    self.assertTrue(step.get("hints"), f"{lesson['id']} step {i} needs hints")

    def test_lookup(self):
        self.assertEqual(lesson_by_id("ch3")["title"], "WHERE")
        self.assertIsNone(lesson_by_id("missing"))


if __name__ == "__main__":
    unittest.main()
