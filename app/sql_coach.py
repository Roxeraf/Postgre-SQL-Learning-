"""Learner-facing SQL feedback and a lightweight logical explainer."""
from __future__ import annotations

import re

CLAUSE_ORDER = (
    ("WITH", "WITH"),
    ("FROM", "FROM"),
    ("JOIN", "JOIN"),
    ("LEFT JOIN", "LEFT JOIN"),
    ("RIGHT JOIN", "RIGHT JOIN"),
    ("INNER JOIN", "INNER JOIN"),
    ("ON", "ON"),
    ("WHERE", "WHERE"),
    ("GROUP BY", "GROUP BY"),
    ("HAVING", "HAVING"),
    ("SELECT", "SELECT"),
    ("ORDER BY", "ORDER BY"),
    ("LIMIT", "LIMIT"),
)

MENTAL = {
    "SELECT": ("Was?", "Welche Informationen sollen im Ergebnis erscheinen?"),
    "FROM": ("Woher?", "Aus welcher Tabelle kommen die Daten?"),
    "JOIN": ("Welche zusätzlichen Infos?", "Welche weitere Tabelle wird dazugenommen?"),
    "LEFT JOIN": ("Welche zusätzlichen Infos?", "Linke Tabelle bleibt vollständig, rechte Infos kommen dazu."),
    "RIGHT JOIN": ("Welche zusätzlichen Infos?", "Rechte Tabelle bleibt vollständig."),
    "INNER JOIN": ("Welche zusätzlichen Infos?", "Nur Zeilen, die in beiden Tabellen zusammenpassen."),
    "ON": ("Wie gehören sie zusammen?", "Über welche Spalten werden die Tabellen verknüpft?"),
    "WHERE": ("Welche?", "Welche Datensätze sollen übrig bleiben?"),
    "GROUP BY": ("Nach was zusammenfassen?", "Welche Gruppen sollen gebildet werden?"),
    "HAVING": ("Welche Gruppen?", "Welche Gruppen sollen übrig bleiben?"),
    "ORDER BY": ("Sortierung?", "In welcher Reihenfolge sollen die Zeilen erscheinen?"),
    "LIMIT": ("Wie viele?", "Wie viele Ergebniszeilen sollen angezeigt werden?"),
    "WITH": ("Zwischenergebnis?", "Eine Hilfsabfrage, auf die danach zugegriffen wird."),
}

KEYWORD_RE = re.compile(
    r"\b(SELECT|FROM|WHERE|JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|INNER\s+JOIN|ON|AND|OR|NOT|"
    r"NULL|AS|WITH|INSERT|UPDATE|DELETE|BEGIN|COMMIT|ROLLBACK|LIMIT|ORDER\s+BY|"
    r"GROUP\s+BY|HAVING|DISTINCT|CASE|WHEN|THEN|ELSE|END|UNION|ALL|IN|IS|"
    r"BETWEEN|EXISTS|LIKE|ILIKE)\b",
    re.I,
)


def strip_sql_line_comments(sql: str) -> str:
    lines = []
    for line in (sql or "").splitlines():
        i = 0
        in_single = False
        cut = len(line)
        while i < len(line):
            ch = line[i]
            if in_single:
                if ch == "'" and i + 1 < len(line) and line[i + 1] == "'":
                    i += 2
                    continue
                if ch == "'":
                    in_single = False
                i += 1
                continue
            if ch == "'":
                in_single = True
                i += 1
                continue
            if ch == "-" and i + 1 < len(line) and line[i + 1] == "-":
                cut = i
                break
            i += 1
        lines.append(line[:cut])
    return "\n".join(lines)


def compact_sql(sql: str) -> str:
    return re.sub(r"\s+", " ", strip_sql_line_comments(sql or "")).strip()


def has_clause(sql: str, keyword: str) -> bool:
    blob = compact_sql(sql)
    return bool(re.search(rf"\b{keyword}\b", blob, re.I))


def select_list_text(sql: str) -> str:
    blob = compact_sql(sql)
    match = re.search(r"\bSELECT\b\s+(.*?)\s+\bFROM\b", blob, re.I)
    return (match.group(1) if match else "").strip()


def has_empty_select_list(sql: str) -> bool:
    blob = compact_sql(sql)
    if re.search(r"\bSELECT(\s+(DISTINCT|ALL))?\s+FROM\b", blob, re.I):
        return True
    listed = select_list_text(sql)
    return has_clause(sql, "SELECT") and has_clause(sql, "FROM") and listed == ""


def uses_equals_null(sql: str) -> bool:
    blob = compact_sql(sql)
    return bool(re.search(r"(?<!IS\s)(?<!IS NOT\s)(<>|!=|=)\s*NULL\b", blob, re.I)) or bool(
        re.search(r"\bNULL\s*(<>|!=|=)", blob, re.I)
    )


def uses_or(sql: str) -> bool:
    return bool(re.search(r"\bOR\b", compact_sql(sql), re.I))


def uses_and(sql: str) -> bool:
    return bool(re.search(r"\bAND\b", compact_sql(sql), re.I))


def clause_snippets(sql: str) -> list[dict]:
    """Split a query into mental-model parts in logical processing order."""
    raw = strip_sql_line_comments(sql or "").strip().rstrip(";")
    if not raw:
        return []
    pattern = re.compile(
        r"\b(SELECT|FROM|WHERE|LEFT\s+JOIN|RIGHT\s+JOIN|INNER\s+JOIN|JOIN|"
        r"GROUP\s+BY|ORDER\s+BY|HAVING|LIMIT|WITH|ON)\b",
        re.I,
    )
    matches = list(pattern.finditer(raw))
    if not matches:
        return [{"key": "SQL", "sql": raw, "title": "Abfrage", "question": "Was macht diese Query?", "blurb": raw}]

    parts = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        key = re.sub(r"\s+", " ", match.group(1).upper())
        body = raw[match.start() : end].strip()
        title, question = MENTAL.get(key, (key, "Was passiert in diesem Schritt?"))
        parts.append({"key": key, "sql": body, "title": title, "question": question, "blurb": ""})

    logical = ["WITH", "FROM", "JOIN", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN", "ON", "WHERE", "GROUP BY", "HAVING", "SELECT", "ORDER BY", "LIMIT"]
    rank = {k: i for i, k in enumerate(logical)}
    parts.sort(key=lambda p: (rank.get(p["key"], 50), 0))

    blurbs = {
        "FROM": "Wir starten mit dieser Tabelle.",
        "JOIN": "Zusätzlich brauchen wir Daten aus einer anderen Tabelle.",
        "LEFT JOIN": "Zusätzlich brauchen wir Daten aus einer anderen Tabelle. Zeilen links bleiben auch ohne Treffer.",
        "INNER JOIN": "Zusätzlich brauchen wir Daten aus einer anderen Tabelle — nur passende Paare bleiben.",
        "ON": "So findet SQL heraus, welche Zeilen zusammengehören.",
        "WHERE": "Nur Datensätze, die diese Bedingung erfüllen, bleiben übrig.",
        "GROUP BY": "Gleichartige Zeilen werden zu Gruppen zusammengefasst.",
        "HAVING": "Danach werden Gruppen gefiltert — nicht einzelne Zeilen.",
        "SELECT": "Im Ergebnis sollen genau diese Informationen erscheinen.",
        "ORDER BY": "Das Ergebnis wird sortiert.",
        "LIMIT": "Es werden nur so viele Zeilen zurückgegeben.",
        "WITH": "Zuerst wird ein Zwischenergebnis berechnet.",
    }
    for part in parts:
        part["blurb"] = blurbs.get(part["key"], part["question"])
    return parts


def explain_sql(sql: str) -> dict:
    parts = clause_snippets(sql)
    plain_bits = []
    for part in parts:
        if part["key"] == "SELECT":
            cols = part["sql"]
            cols = re.sub(r"^SELECT\s+", "", cols, flags=re.I).strip()
            if cols == "*":
                plain_bits.append("zeige alle Spalten")
            else:
                plain_bits.append(f"zeige {cols}")
        elif part["key"] == "FROM":
            table = re.sub(r"^FROM\s+", "", part["sql"], flags=re.I).split()[0]
            plain_bits.append(f"aus {table}")
        elif part["key"] == "WHERE":
            cond = re.sub(r"^WHERE\s+", "", part["sql"], flags=re.I)
            plain_bits.append(f"nur wo {cond}")
        elif part["key"] in ("ORDER BY",):
            spec = re.sub(r"^ORDER BY\s+", "", part["sql"], flags=re.I)
            direction = "absteigend" if re.search(r"\bDESC\b", spec, re.I) else "aufsteigend"
            plain_bits.append(
                f"sortiert {direction} nach {re.sub(r'\b(ASC|DESC)\b', '', spec, flags=re.I).strip()}"
            )
        elif part["key"] == "LIMIT":
            n = re.sub(r"^LIMIT\s+", "", part["sql"], flags=re.I)
            plain_bits.append(f"höchstens {n} Zeilen")
        elif part["key"] in ("JOIN", "LEFT JOIN", "INNER JOIN"):
            rest = re.sub(r"^(LEFT\s+JOIN|INNER\s+JOIN|JOIN)\s+", "", part["sql"], flags=re.I)
            table = rest.split()[0] if rest else "einer weiteren Tabelle"
            plain_bits.append(f"verbunden mit {table}")
    plain = " → ".join(plain_bits) if plain_bits else "Diese Abfrage liest Daten."
    sentences = []
    if plain_bits:
        sentences.append(plain[0].upper() + plain[1:] + ".")
    return {"parts": parts, "plain": sentences[0] if sentences else plain, "ok": True}


def diagnose_structure(user_sql: str, solution_sql: str, step: dict | None = None) -> str | None:
    """Why a query is likely wrong — concepts, not PostgreSQL jargon."""
    step = step or {}
    user = compact_sql(user_sql)
    sol = compact_sql(solution_sql)
    if not user:
        return "Schreibe oder baue zuerst eine Abfrage."

    if uses_equals_null(user):
        return (
            "NULL bedeutet: für dieses Feld ist kein Wert vorhanden. "
            "`= NULL` findet solche Zeilen nicht. Verwende `IS NULL` oder `IS NOT NULL`."
        )

    if has_empty_select_list(user_sql):
        return (
            "Du hast SQL schon gesagt, **woher** die Daten kommen — nach `SELECT` fehlt noch, "
            "**was** du sehen möchtest. Zum Beispiel `*` für alle Spalten oder Spaltennamen."
        )

    if has_clause(user, "SELECT") and not has_clause(user, "FROM"):
        listed = select_list_text(user_sql)
        if not listed:
            listed = re.sub(r"^SELECT\s+", "", compact_sql(user_sql), flags=re.I)
        return (
            "Deine Abfrage ist noch nicht vollständig.\n\n"
            "Du hast SQL bereits gesagt, **was** du sehen möchtest:\n"
            f"`SELECT {listed}`\n\n"
            "Jetzt fehlt noch, **woher** die Daten kommen.\n"
            "Dafür verwenden wir `FROM`."
        )

    if has_clause(sol, "WHERE") and not has_clause(user, "WHERE"):
        return (
            "Du möchtest nicht alle Zeilen. Dafür filterst du mit `WHERE` — "
            "das entscheidet, welche Datensätze übrig bleiben."
        )

    if has_clause(sol, "GROUP BY") and not has_clause(user, "GROUP BY"):
        return (
            "Die Aufgabe fasst mehrere Zeilen zusammen (zum Beispiel „pro Kunde“). "
            "Dafür brauchst du `GROUP BY`."
        )

    if has_clause(sol, "JOIN") and not has_clause(user, "JOIN"):
        return (
            "Die benötigten Informationen liegen in mehr als einer Tabelle. "
            "Mit `JOIN` nimmst du die zweite Tabelle hinzu, mit `ON` sagst du, wie sie zusammenhängen."
        )

    if has_clause(sol, "ORDER BY") and not has_clause(user, "ORDER BY") and step.get("ordered"):
        return "Das Ergebnis soll in einer bestimmten Reihenfolge kommen. Dafür ist `ORDER BY` zuständig."

    if has_clause(sol, "LIMIT") and not has_clause(user, "LIMIT") and step.get("expect_limit"):
        return "Du sollst nur einen Teil der Zeilen sehen. Das begrenzt `LIMIT`."

    if uses_and(sol) and uses_or(user) and not uses_and(user):
        return (
            "Du hast `OR` verwendet. `OR` bedeutet: **mindestens eine** Bedingung reicht. "
            "Hier müssen **beide** Bedingungen stimmen — das ist `AND`."
        )

    if uses_or(sol) and uses_and(user) and not uses_or(user):
        return (
            "Du hast `AND` verwendet. `AND` verlangt, dass **beide** Bedingungen wahr sind. "
            "Hier reicht **mindestens eine** — das ist `OR`."
        )

    return None


def friendly_sql_error(err: str, sql: str, sandbox: str = "wmx") -> str:
    low = (err or "").lower()
    structural = diagnose_structure(sql, sql)
    if has_clause(sql, "SELECT") and not has_clause(sql, "FROM"):
        return diagnose_structure(sql, "SELECT 1 FROM orders")
    if has_empty_select_list(sql):
        return (
            "Die SELECT-Liste ist noch leer. Nach `SELECT` kommt, **was** du sehen möchtest "
            "(`*` oder Spaltennamen), danach `FROM`."
        )
    if uses_equals_null(sql):
        return (
            "NULL ist kein normaler Wert. `= NULL` ist deshalb immer unbekannt. "
            "Schreibe `IS NULL` oder `IS NOT NULL`."
        )
    if "syntax error at end of input" in low:
        return (
            "Die Abfrage ist unvollständig. Prüfe, ob `SELECT`, `FROM` und eventuelle "
            "Anführungszeichen oder Klammern geschlossen sind."
        )
    if "syntax error at or near" in low:
        near = re.search(r'syntax error at or near "([^"]+)"', err or "", re.I)
        token = near.group(1) if near else ""
        hint = f" Postgres stolpert bei `{token}`." if token else ""
        if token.lower() in {"orders", "clients", "stock"} and not has_clause(sql, "FROM"):
            return diagnose_structure(sql, "SELECT * FROM orders")
        return "Die Abfrage hat einen Syntaxfehler." + hint + " Lies die Query wie eine Frage: Was? Woher? Welche?"
    if "does not exist" in low and "column" in low:
        extra = (
            " Zwischen zwei Spalten gehört ein Komma (`order_number, task_status`)."
            if sandbox != "learn"
            else ""
        )
        return (
            "Eine Spalte in deiner Abfrage gibt es in dieser Tabelle nicht. "
            "Schau in der Tabelle nach den genauen Namen — Groß/Kleinschreibung und Tippfehler zählen."
            + extra
        )
    if "does not exist" in low:
        if sandbox == "learn":
            return (
                "Diese Tabelle gibt es im Übungsbereich nicht. "
                "Im Anfänger-Pfad heißen die Tabellen `orders`, `clients` und `stock`."
            )
        return (
            "Tabellen immer voll qualifiziert: instance_1.flowapp_demo_<name>. "
            "Im Schema den deutschen Namen suchen und die Tabelle anklicken."
        )
    if "statement timeout" in low or "canceling statement" in low:
        return "Die Abfrage lief zu lange und wurde abgebrochen. Prüfe JOINs ohne `ON`-Bedingung."
    if "permission denied" in low:
        return "Im Übungsbereich darfst du Daten nur lesen (`SELECT`). Änderungen an Tabellen sind gesperrt."
    if structural and "syntax" in low:
        return structural
    return err or "Die Abfrage konnte nicht ausgeführt werden."
