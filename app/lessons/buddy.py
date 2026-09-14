"""Teaching copy, learner context for Claude, and in-app help packs.

The app has no model of its own. The in-app buddy runs the local Claude Code
CLI (see `app/claude_cli.py`); Claude Desktop reads the same context through
MCP (`buddy_context`, `help_with`, `coach_sql`).
"""

from __future__ import annotations

import copy
import json
import os
import re
import time
from pathlib import Path

from lessons.academy_data import ACADEMY, lesson_by_id
from lessons.knowledge import ARTICLES, articles_for_lesson, knowledge_cards
from lessons.workshop import learner_context_path, workshop_by_id, workshop_lessons

PAGES = {"home", "learn", "playground", "wissen", "cards"}

CONCEPT_TEACH = {
    "TABLE": (
        "Eine **Tabelle** ist eine Liste mit Überschriften. Jede **Zeile** ist ein Datensatz "
        "(ein Auftrag, ein Kunde), jede **Spalte** eine Art von Information. Die `id` macht "
        "eine Zeile eindeutig — Namen dürfen sich wiederholen."
    ),
    "SELECT": (
        "`SELECT` beantwortet: **Was will ich sehen?** Es wählt Spalten, nicht Zeilen. "
        "`*` holt alles, namentliche Spalten nur das, was die Frage braucht. "
        "Zu viele Zeilen löst du nicht mit SELECT, sondern mit `WHERE`."
    ),
    "FROM": (
        "`FROM` beantwortet: **Woher kommen die Daten?** Ohne FROM weiß SQL nicht, "
        "in welcher Tabelle es suchen soll. Bei uns heißen die Aufträge `orders`, "
        "die Kunden `clients`."
    ),
    "WHERE": (
        "`WHERE` filtert **Zeilen**. Nur Datensätze, für die die Bedingung wahr ist, bleiben. "
        "Text steht in einfachen Anführungszeichen: `status = 'offen'`. "
        "Zwei Bedingungen gleichzeitig: `AND`."
    ),
    "COMPARE": (
        "Vergleiche in `WHERE` sind Fragen an jede Zeile: gleich (`=`), ungleich (`<>`), "
        "größer, kleiner, `BETWEEN`, `IN`, `LIKE`. Das Ergebnis ist wahr oder falsch — "
        "nur wahre Zeilen bleiben."
    ),
    "AND": (
        "`AND` verlangt, dass **beide** Seiten stimmen. `OR` lässt eine von beiden reichen. "
        "„Helio und offen“ ist AND — sonst kämen alle Helio-Aufträge oder alle offenen."
    ),
    "ORDER BY": (
        "`ORDER BY` legt die Reihenfolge fest. Ohne ORDER BY ist die Reihenfolge kein Versprechen. "
        "`DESC` = größte bzw. neueste zuerst, `ASC` (Standard) = aufsteigend."
    ),
    "LIMIT": (
        "`LIMIT` schneidet das Ergebnis auf so viele Zeilen. Oft zusammen mit `ORDER BY`, "
        "sonst ist „die ersten fünf“ zufällig."
    ),
    "NULL": (
        "`NULL` heißt: **kein Wert** — nicht 0, nicht leerer Text. `= NULL` findet solche Zeilen nie. "
        "Suche mit `IS NULL` / `IS NOT NULL`. Bei LEFT JOIN bedeutet NULL oft: rechts kein Treffer."
    ),
    "GROUP BY": (
        "`GROUP BY` fasst gleichartige Zeilen zu **Gruppen** zusammen. "
        "`COUNT`/`SUM`/`AVG` rechnen dann pro Gruppe. Was in SELECT nicht aggregiert ist, "
        "muss gruppiert sein."
    ),
    "JOIN": (
        "Ein `JOIN` holt Infos aus einer **zweiten Tabelle**. `ON` ist die Naht "
        "(welche ids zusammengehören). `JOIN` (INNER) behält nur Paare; `LEFT JOIN` "
        "behält die linke Tabelle auch ohne Treffer — rechts dann NULL."
    ),
    "HAVING": (
        "`WHERE` filtert Zeilen **vor** dem Gruppieren. `HAVING` filtert **Gruppen danach** — "
        "zum Beispiel nur Kunden mit mehr als vier Aufträgen. Aggregate gehören nach HAVING, "
        "nicht nach WHERE."
    ),
    "CASE": (
        "`CASE` schreibt eine Regel in eine Spalte: WENN Status offen DANN … SONST …. "
        "Es ändert keine gespeicherten Daten, nur das, was die Abfrage zeigt."
    ),
    "SUBQUERY": (
        "Eine Unterabfrage ist eine Query in Klammern, die einen Wert oder eine Menge liefert. "
        "Typisch: „Kunden, deren id in (SELECT …) vorkommt“. Zuerst die innere Frage, dann die äußere."
    ),
    "DML": (
        "`INSERT`/`UPDATE`/`DELETE` ändern Daten — anders als SELECT, das nur liest. "
        "Immer mit `WHERE` bei UPDATE/DELETE, sonst trifft die Änderung die ganze Tabelle."
    ),
    "TX": (
        "Eine **Transaktion** bündelt Änderungen: `BEGIN` … `COMMIT` macht sie fest, "
        "`ROLLBACK` nimmt alles zurück. So bleibt der Bestand konsistent, wenn ein Schritt scheitert."
    ),
}

# Prefer the newest idea of a step (last matching id).
_TEACH_PRIORITY = [
    "TX", "DML", "SUBQUERY", "CASE", "HAVING", "GROUP BY", "JOIN",
    "NULL", "AND", "COMPARE", "WHERE", "ORDER BY", "LIMIT", "SELECT", "FROM", "TABLE",
]


def teach_for(concepts) -> str:
    ids = [str(c or "").strip() for c in (concepts or []) if str(c or "").strip()]
    for cid in _TEACH_PRIORITY:
        if cid in ids and cid in CONCEPT_TEACH:
            return CONCEPT_TEACH[cid]
    for cid in ids:
        if cid in CONCEPT_TEACH:
            return CONCEPT_TEACH[cid]
    gloss = {item["id"]: item for item in (ACADEMY.get("glossary") or [])}
    for cid in ids:
        text = (gloss.get(cid) or {}).get("text") or ""
        if text:
            return text
    return ""


def related_reading(lesson_id, concepts=None, limit=3):
    return articles_for_lesson(lesson_id, concepts, limit=limit)


def enrich_lesson(lesson: dict | None) -> dict | None:
    """Copy a lesson and fill `teach` + related bible links when missing."""
    if not lesson:
        return None
    data = copy.deepcopy(lesson)
    lesson_concepts = list(data.get("concepts") or [])
    data["related"] = list(data.get("related") or related_reading(data.get("id"), lesson_concepts))
    for step in data.get("steps") or []:
        if not isinstance(step, dict):
            continue
        step_concepts = list(step.get("concepts") or lesson_concepts)
        if not str(step.get("teach") or "").strip():
            taught = teach_for(step_concepts)
            if taught:
                step["teach"] = taught
        if not step.get("related"):
            step["related"] = related_reading(data.get("id"), step_concepts, limit=2)
    return data


def _clip(value, n: int) -> str:
    text = str(value or "").strip()
    return text[:n]


def save_learner_context(data: dict) -> dict:
    progress = data.get("progress") if isinstance(data.get("progress"), dict) else {}
    completed = progress.get("completed") or []
    if not isinstance(completed, list):
        completed = []
    payload = {
        "page": data.get("page") if data.get("page") in PAGES else "home",
        "url": _clip(data.get("url"), 200),
        "lesson_id": _clip(data.get("lesson_id"), 80),
        "lesson_title": _clip(data.get("lesson_title"), 120),
        "chapter": data.get("chapter"),
        "workshop": bool(data.get("workshop")),
        "step": data.get("step"),
        "step_type": _clip(data.get("step_type"), 40),
        "step_title": _clip(data.get("step_title"), 160),
        "prompt": _clip(data.get("prompt"), 400),
        "last_sql": _clip(data.get("last_sql"), 2000),
        "last_coach": _clip(data.get("last_coach"), 500),
        "last_ok": data.get("last_ok"),
        "question": _clip(data.get("question"), 400),
        "progress": {
            "completed": [str(x)[:40] for x in completed[:40]],
            "current": _clip(progress.get("current"), 80),
            "chapters_done": progress.get("chapters_done"),
            "chapters_total": progress.get("chapters_total"),
        },
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    path = learner_context_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write atomically: the debounced browser sync and the chat request both
    # land here, and the MCP server reads the file concurrently. A torn read
    # makes load_learner_context() return None and the buddy loses the learner.
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return payload


def load_learner_context() -> dict | None:
    path = learner_context_path()
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def public_step(step: dict | None) -> dict | None:
    """Step payload for Claude — no muster solution unless coach asks later."""
    if not step:
        return None
    return {
        "type": step.get("type"),
        "title": step.get("title"),
        "text": step.get("text"),
        "prompt": step.get("prompt"),
        "teach": step.get("teach"),
        "plain": step.get("plain"),
        "hints": list(step.get("hints") or []),
        "concepts": list(step.get("concepts") or []),
        "has_solution": bool(step.get("solution") or step.get("sql")),
        "related": list(step.get("related") or []),
    }


def resolve_lesson(lesson_id: str | None):
    lid = str(lesson_id or "").strip()
    if not lid:
        return None
    return lesson_by_id(lid) or workshop_by_id(lid)


def current_step(lesson: dict | None, index) -> dict | None:
    if not lesson:
        return None
    try:
        idx = int(index)
        step = (lesson.get("steps") or [])[idx]
    except (TypeError, ValueError, IndexError):
        return None
    return step if isinstance(step, dict) else None


def search_learning(query: str, limit: int = 12) -> list[dict]:
    q = re.sub(r"[#*_`>|]+", " ", query or "").lower().strip()
    terms = [t for t in q.split() if len(t) >= 2]
    if not terms:
        return []
    index = []
    for lesson in ACADEMY["lessons"]:
        hay = " ".join([
            lesson["title"],
            lesson.get("goal") or "",
            " ".join(
                " ".join([
                    s.get("title") or "",
                    s.get("text") or "",
                    s.get("prompt") or "",
                    s.get("teach") or "",
                    s.get("plain") or "",
                ])
                for s in lesson.get("steps") or []
            ),
        ]).lower()
        index.append({
            "kind": "kapitel",
            "id": lesson["id"],
            "title": lesson["title"],
            "url": f"/learn/{lesson['id']}",
            "preview": lesson.get("goal") or "",
            "text": hay,
        })
        for i, step in enumerate(lesson.get("steps") or []):
            step_hay = " ".join([
                step.get("title") or "",
                step.get("text") or "",
                step.get("prompt") or "",
                step.get("teach") or "",
                step.get("plain") or "",
            ]).lower()
            index.append({
                "kind": "schritt",
                "id": lesson["id"],
                "title": f"{lesson['title']} · {step.get('title') or step.get('type')}",
                "url": f"/learn/{lesson['id']}",
                "preview": (step.get("text") or step.get("prompt") or step.get("teach") or "")[:220],
                "text": step_hay,
                "step": i,
            })
    for art in ARTICLES:
        index.append({
            "kind": "artikel",
            "id": art["slug"],
            "title": art["title"],
            "url": f"/wissen/{art['slug']}",
            "preview": art.get("summary") or "",
            "text": " ".join([
                art["title"], art.get("summary") or "", art.get("body") or "",
            ]).lower(),
        })
    for item in workshop_lessons():
        index.append({
            "kind": "playground",
            "id": item["id"],
            "title": item["title"],
            "url": f"/playground/{item['id']}",
            "preview": item.get("goal") or "",
            "text": " ".join([item["title"], item.get("goal") or ""]).lower(),
        })
    scored = []
    for item in index:
        hay = item["text"]
        if not all(t in hay for t in terms):
            continue
        score = sum(hay.count(t) for t in terms)
        title_l = item["title"].lower()
        score += 8 * sum(1 for t in terms if t in title_l)
        if item["kind"] in {"kapitel", "artikel"}:
            score += 3
        scored.append((score, item))
    scored.sort(key=lambda pair: -pair[0])
    out = []
    seen = set()
    for _score, item in scored:
        key = (item["kind"], item["id"], item.get("step"))
        if key in seen:
            continue
        seen.add(key)
        out.append({k: item[k] for k in item if k != "text"})
        if len(out) >= limit:
            break
    return out


def help_pack(question: str, *, lesson_id=None, step=None) -> dict:
    ctx = load_learner_context() or {}
    lid = str(lesson_id or ctx.get("lesson_id") or "").strip()
    idx = step if step is not None else ctx.get("step")
    raw = resolve_lesson(lid)
    lesson = enrich_lesson(raw) if raw else None
    current = current_step(lesson, idx)
    concepts = list((current or {}).get("concepts") or (lesson or {}).get("concepts") or [])
    q = (question or ctx.get("question") or "").strip()
    hits = search_learning(q or " ".join(concepts) or (lesson or {}).get("title") or "", limit=8)
    cards = []
    if concepts:
        for card in knowledge_cards():
            hay = f"{card.get('front') or ''} {card.get('back') or ''} {card.get('topic_label') or ''}".lower()
            if any(c.lower() in hay for c in concepts):
                cards.append({
                    "front": card.get("front"),
                    "back": card.get("back"),
                    "lesson_id": card.get("lesson_id"),
                    "slug": card.get("slug"),
                })
            if len(cards) >= 4:
                break
    return {
        "question": q,
        "here": {
            "page": ctx.get("page"),
            "url": ctx.get("url"),
            "lesson_id": lid or None,
            "lesson_title": (lesson or {}).get("title") or ctx.get("lesson_title"),
            "workshop": bool((lesson or {}).get("workshop") or ctx.get("workshop")),
            "step": idx,
        },
        "teach": (current or {}).get("teach") or teach_for(concepts),
        "step": public_step(current),
        "articles": related_reading(lid, concepts, limit=4),
        "hits": hits,
        "cards": cards,
        "last_sql": ctx.get("last_sql") or "",
        "last_coach": ctx.get("last_coach") or "",
        "how_to_answer": (
            "Erkläre das Konzept an der Lager-Tabelle (orders, clients, stock). "
            "Gib den nächsten Denkschritt, nicht die volle Musterlösung — "
            "außer die Person verlangt ausdrücklich die Lösung."
        ),
    }


def buddy_snapshot() -> dict:
    ctx = load_learner_context()
    lid = (ctx or {}).get("lesson_id")
    raw = resolve_lesson(lid)
    lesson = enrich_lesson(raw) if raw else None
    step = current_step(lesson, (ctx or {}).get("step"))
    path = [
        {
            "id": item["id"],
            "title": item["title"],
            "goal": item.get("goal"),
            "chapter": item.get("chapter"),
        }
        for item in ACADEMY["lessons"]
    ]
    return {
        "role": (
            "Du bist der Lern-Buddy für plx.learnSQL. "
            "Die Person übt in der App; du erklärst, fragst nach und hilfst beim Denken. "
            "Lösung nicht vorgeben, außer sie wird verlangt."
        ),
        "here": ctx,
        "lesson": None if not lesson else {
            "id": lesson.get("id"),
            "title": lesson.get("title"),
            "goal": lesson.get("goal"),
            "chapter": lesson.get("chapter"),
            "workshop": bool(lesson.get("workshop")),
            "concepts": list(lesson.get("concepts") or []),
            "url": (
                f"/playground/{lesson['id']}" if lesson.get("workshop")
                else f"/learn/{lesson['id']}"
            ),
        },
        "step": public_step(step),
        "related": (lesson or {}).get("related") or related_reading(lid, (lesson or {}).get("concepts")),
        "path": path,
        "playground": [
            {"id": item["id"], "title": item["title"], "goal": item.get("goal")}
            for item in workshop_lessons()
        ],
        "context_file": str(learner_context_path()),
        "how_to_help": (
            "1. `buddy_context` ist der Standort. "
            "2. Fragen mit `help_with` und `search_path` / `search_wissen` beantworten. "
            "3. SQL der Person mit `coach_sql` prüfen. "
            "4. Kapitel: `get_lesson`. Bibel: `get_article`. "
            "5. Zusatzübungen nur auf Wunsch in den Playground (`exercise_context` → `save_practice`). "
            "Die App aktualisiert den Playground selbst — nicht zum Neuladen auffordern."
        ),
        "tools": [
            "buddy_context", "help_with", "search_path", "coach_sql",
            "get_lesson", "list_lessons", "search_wissen", "get_article",
        ],
    }


def context_path() -> Path:
    return learner_context_path()
