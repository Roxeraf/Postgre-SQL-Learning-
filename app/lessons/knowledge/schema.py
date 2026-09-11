"""Shared article and card helpers for the knowledge bible."""


SECTIONS = [
    ("lesen", "Lesen"),
    ("filtern", "Filtern"),
    ("verbinden", "Verbinden"),
    ("rechnen", "Rechnen"),
    ("schachteln", "Schachteln"),
    ("aendern", "Ändern"),
    ("postgres", "Postgres"),
    ("nachbar", "Nachbar"),
]


def card(cid, kind, front, back, sql=""):
    return {"id": cid, "kind": kind, "front": front, "back": back, "sql": sql}


def article(
    slug,
    title,
    section,
    summary,
    body,
    sql=None,
    pitfalls=None,
    related=None,
    lesson_id="",
    lookup_only=False,
    cards=None,
):
    labels = dict(SECTIONS)
    return {
        "slug": slug,
        "title": title,
        "section": section,
        "section_label": labels[section],
        "summary": summary,
        "body": body.strip(),
        "sql": sql or [],
        "pitfalls": pitfalls or [],
        "related": related or [],
        "lesson_id": lesson_id,
        "lookup_only": lookup_only,
        "cards": cards or [],
    }
