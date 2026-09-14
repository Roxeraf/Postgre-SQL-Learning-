"""Load Claude-Code / MCP practice lessons from data/workshop."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{1,60}$")


def learner_context_path() -> Path:
    return workshop_dir() / ".learner-context.json"


def workshop_dir() -> Path:
    env = os.environ.get("WORKSHOP_DIR")
    if env:
        return Path(env)
    home = os.environ.get("LEARN_SQL_HOME")
    if home:
        return Path(home) / "workshop"
    here = Path(__file__).resolve()
    repo = here.parents[2] / "data" / "workshop"
    local = here.parents[1] / "data" / "workshop"
    if repo.is_dir():
        return repo
    if local.is_dir():
        return local
    return repo if (here.parents[2] / "data").is_dir() else local


def _read_lesson(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    lid = str(data.get("id") or path.stem)
    if not SAFE_ID.match(lid):
        return None
    steps = data.get("steps") or []
    if not steps:
        return None
    data["id"] = lid
    data.setdefault("title", lid)
    data.setdefault("goal", "Übung aus dem SQL-Playground.")
    data.setdefault("minutes", 8)
    data.setdefault("concepts", [])
    data.setdefault("model", ["SELECT", "FROM", "WHERE"])
    data.setdefault("quiz", [])
    data["workshop"] = True
    data["chapter"] = "W"
    return data


def workshop_lessons() -> list[dict]:
    folder = workshop_dir()
    if not folder.is_dir():
        return []
    lessons = []
    for path in sorted(folder.glob("*.json")):
        lesson = _read_lesson(path)
        if lesson:
            lessons.append(lesson)
    return lessons


def public_practice(item: dict) -> dict:
    concepts = item.get("concepts") or []
    lid = item["id"]
    return {
        "id": lid,
        "title": item.get("title") or lid,
        "goal": item.get("goal") or "",
        "minutes": item.get("minutes") or 8,
        "step_count": len(item.get("steps") or []),
        "concept": concepts[0] if concepts else None,
        "url": f"/playground/{lid}",
    }


def recent_workshop_lessons(limit: int = 3) -> list[dict]:
    folder = workshop_dir()
    if not folder.is_dir():
        return []
    ranked = []
    for path in folder.glob("*.json"):
        try:
            ranked.append((path.stat().st_mtime, path))
        except OSError:
            continue
    ranked.sort(reverse=True)
    out = []
    for _, path in ranked:
        lesson = _read_lesson(path)
        if not lesson:
            continue
        out.append(lesson)
        if len(out) >= limit:
            break
    return out


def workshop_by_id(lesson_id: str):
    for lesson in workshop_lessons():
        if lesson["id"] == lesson_id:
            return lesson
    return None


def save_workshop_lesson(data: dict, folder: Path | None = None) -> Path:
    from lessons.academy_data import PATH_IDS

    lid = str(data.get("id") or "").strip()
    if not SAFE_ID.match(lid):
        raise ValueError("id muss wie ws-having-1 aussehen (Buchstaben, Zahlen, Bindestrich).")
    if lid in PATH_IDS:
        raise ValueError("Offizielle Kapitel darf der Playground nicht überschreiben.")
    if not (data.get("steps") or []):
        raise ValueError("steps darf nicht leer sein.")
    folder = Path(folder) if folder is not None else workshop_dir()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{lid}.json"
    payload = dict(data)
    payload["id"] = lid
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def delete_workshop_lesson(lesson_id: str) -> bool:
    from lessons.academy_data import PATH_IDS

    lid = str(lesson_id or "").strip()
    if not SAFE_ID.match(lid):
        raise ValueError("id muss wie ws-having-1 aussehen (Buchstaben, Zahlen, Bindestrich).")
    if lid in PATH_IDS:
        raise ValueError("Offizielle Kapitel darf der Playground nicht löschen.")
    path = workshop_dir() / f"{lid}.json"
    if not path.is_file():
        return False
    path.unlink()
    return True
