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
