"""PostgreSQL learner bible — articles and derived flashcards."""

from lessons.knowledge.aendern import articles as aendern_articles
from lessons.knowledge.filtern import articles as filtern_articles
from lessons.knowledge.lesen import articles as lesen_articles
from lessons.knowledge.nachbar import articles as nachbar_articles
from lessons.knowledge.postgres import articles as postgres_articles
from lessons.knowledge.rechnen import articles as rechnen_articles
from lessons.knowledge.schachteln import articles as schachteln_articles
from lessons.knowledge.schema import SECTIONS
from lessons.knowledge.verbinden import articles as verbinden_articles

ARTICLES = (
    lesen_articles()
    + filtern_articles()
    + verbinden_articles()
    + rechnen_articles()
    + schachteln_articles()
    + aendern_articles()
    + postgres_articles()
    + nachbar_articles()
)

ARTICLES_BY_SLUG = {a["slug"]: a for a in ARTICLES}


def sections():
    grouped = []
    for key, label in SECTIONS:
        items = [a for a in ARTICLES if a["section"] == key]
        if items:
            grouped.append({"id": key, "label": label, "articles": items})
    return grouped


def article_by_slug(slug):
    return ARTICLES_BY_SLUG.get(slug)


def knowledge_cards():
    cards = []
    for art in ARTICLES:
        for c in art.get("cards") or []:
            cards.append({
                "id": c["id"],
                "front": c["front"],
                "back": c["back"],
                "sql": c.get("sql") or "",
                "kind": c.get("kind") or "begriff",
                "lesson_id": art.get("lesson_id") or "",
                "lesson": art["title"],
                "topic": art["section"],
                "topic_label": art["section_label"],
                "slug": art["slug"],
                "source": "wissen",
            })
    return cards


def related_articles(art):
    out = []
    for slug in art.get("related") or []:
        other = ARTICLES_BY_SLUG.get(slug)
        if other:
            out.append(other)
    return out


CONCEPT_SLUGS = {
    "TABLE": "tabelle",
    "SELECT": "select",
    "FROM": "from",
    "WHERE": "where",
    "COMPARE": "vergleiche",
    "AND": "and-or",
    "ORDER BY": "order-by",
    "LIMIT": "limit",
    "NULL": "null",
    "GROUP BY": "group-by",
    "JOIN": "join-inner",
    "HAVING": "having",
    "CASE": "case",
    "SUBQUERY": "unterabfrage",
    "DML": "update",
    "TX": "transaktion",
}


def articles_for_lesson(lesson_id, concepts=None, limit=3):
    """Bible articles that belong to a chapter or its SQL concepts."""
    scored = []
    concepts = [str(c or "").strip() for c in (concepts or []) if str(c or "").strip()]
    wanted_slugs = {CONCEPT_SLUGS[c] for c in concepts if c in CONCEPT_SLUGS}
    for art in ARTICLES:
        score = 0
        if lesson_id and art.get("lesson_id") == lesson_id:
            score += 6
        if art.get("slug") in wanted_slugs:
            score += 5
        hay = f"{art.get('title') or ''} {art.get('summary') or ''} {art.get('slug') or ''}".lower()
        for concept in concepts:
            if concept.lower() in hay:
                score += 2
        if score:
            scored.append((score, art))
    scored.sort(key=lambda item: (-item[0], item[1]["title"]))
    out = []
    seen = set()
    for _score, art in scored:
        if art["slug"] in seen:
            continue
        seen.add(art["slug"])
        out.append({
            "slug": art["slug"],
            "title": art["title"],
            "summary": art["summary"],
            "section": art.get("section_label") or art.get("section"),
        })
        if len(out) >= limit:
            break
    return out
