"""Additional official path chapters: aggregates, line items, CASE, subqueries."""

from lessons.academy_data import (
    ORDERS,
    Q,
    clients_table,
    ids,
    orders_table,
)
from lessons.academy_more import ORDER_ITEMS, ORDERS_WITH_ITEMS, items_table

SUM_OFFEN_IDS = ids(lambda r: r["status"] == "offen" and r["quantity"] is not None)
HAS_ITEMS_IDS = list(ORDERS_WITH_ITEMS)
NO_ITEMS_IDS = [r["id"] for r in ORDERS if r["id"] not in set(ORDERS_WITH_ITEMS)]


def extra_path_lessons():
    return [
        {
            "id": "ch-agg",
            "chapter": 0,
            "title": "Summen und Mittelwerte",
            "minutes": 12,
            "goal": "Du rechnest mit SUM, AVG, MIN und MAX — eine Zahl pro Gruppe, nicht nur zählen.",
            "concepts": ["GROUP BY"],
            "model": ["SELECT", "FROM", "WHERE", "GROUP BY"],
            "steps": [
                {
                    "type": "explain",
                    "title": "Zählen ist nicht rechnen",
                    "text": "`COUNT(*)` zählt Zeilen. `SUM` addiert Werte, `AVG` mittelt, `MIN`/`MAX` holen das Kleinste und Größte.\n\n"
                    "NULL zählt bei SUM und AVG nicht mit — eine leere Menge ist kein 0.",
                    "sql": "SELECT SUM(quantity)\nFROM orders\nWHERE status = 'offen';",
                    "plain": "Wie viel Menge steckt in den offenen Aufträgen zusammen?",
                    "parts": [
                        {"match": "SELECT SUM(quantity)", "token": "SELECT", "question": "Was?", "answer": "Die Summe der Mengen, nicht die Anzahl der Zeilen."},
                        {"match": "FROM orders", "token": "FROM", "question": "Woher?", "answer": "Aufträge."},
                        {"match": "WHERE status = 'offen'", "token": "WHERE", "question": "Welche?", "answer": "Nur offene — leere quantity-Zellen bleiben draußen."},
                    ],
                    "concepts": ["GROUP BY"],
                },
                {
                    "type": "predict",
                    "title": "Welche Mengen gehen in die Summe?",
                    "text": "Markiere die offenen Aufträge, deren `quantity` in `SUM(quantity)` wirklich mitzählt.",
                    "sql": "SELECT * FROM orders WHERE status = 'offen' AND quantity IS NOT NULL;",
                    "table": orders_table("id", "order_number", "status", "quantity"),
                    "expected_ids": SUM_OFFEN_IDS,
                    "id_field": "id",
                    "execute": True,
                    "concepts": ["GROUP BY", "NULL"],
                    "feedback_ok": "Offen und eine Zahl in quantity. 4731 ist offen, aber die Menge fehlt — die Zeile zählt nicht.",
                    "feedback_bad": "Nur offene Zeilen mit einer Zahl in quantity. Fertige Aufträge und leere Mengen bleiben draußen.",
                },
                {
                    "type": "write",
                    "title": "Offene Menge addieren",
                    "prompt": "Wie groß ist die Summe der Mengen aller **offenen** Aufträge? Nur die eine Zahl.",
                    "placeholder": "SELECT …",
                    "solution": "SELECT SUM(quantity) FROM orders WHERE status = 'offen';",
                    "concepts": ["GROUP BY"],
                    "hints": [
                        "Eine Zahl, keine Liste: SUM(quantity).",
                        "Vorher filtern: WHERE status = 'offen'.",
                    ],
                },
                {
                    "type": "apply",
                    "title": "Mittel pro Kunde",
                    "prompt": "Zeig je Kundenname die durchschnittliche Menge. Zeilen ohne Kundenname weglassen.",
                    "placeholder": "SELECT …",
                    "solution": (
                        "SELECT client, AVG(quantity) FROM orders "
                        "WHERE client IS NOT NULL GROUP BY client;"
                    ),
                    "concepts": ["GROUP BY"],
                    "hints": [
                        "Pro Kunde: GROUP BY client, dazu AVG(quantity).",
                        "WHERE client IS NOT NULL, sonst entsteht eine NULL-Gruppe.",
                    ],
                },
            ],
            "quiz": [
                Q("Was macht SUM(quantity), das COUNT(*) nicht macht?", [
                    "Es zählt, wie viele Zeilen offen sind.",
                    "Es addiert die Werte in der Spalte quantity.",
                    "Es sortiert nach Menge.",
                    "Es ersetzt WHERE.",
                ], 1, "COUNT zählt Zeilen. SUM rechnet mit den Zahlen in einer Spalte."),
                Q("Warum fehlt 4731 in SUM(quantity) der offenen Aufträge?", [
                    "Der Auftrag ist fertig.",
                    "quantity ist NULL — NULL geht nicht in die Summe.",
                    "SUM ignoriert immer die letzte Zeile.",
                    "4731 hat keinen Kunden.",
                ], 1, "NULL ist kein 0. Die Zeile bleibt in der Tabelle, die Summe überspringt den leeren Wert."),
                Q("Was liefert AVG(quantity) GROUP BY client?", [
                    "Eine Zahl für die ganze Tabelle.",
                    "Pro Kunde das Mittel seiner Mengen.",
                    "Die größte Menge aller Aufträge.",
                    "Nur Helio.",
                ], 1, "GROUP BY macht eine Ergebniszeile je Kunde. AVG rechnet innerhalb der Gruppe."),
                Q("MIN und MAX brauchen …", [
                    "immer einen JOIN.",
                    "eine Spalte, deren kleinsten oder größten Wert du willst.",
                    "HAVING.",
                    "ORDER BY DESC.",
                ], 1, "MIN(quantity) / MAX(quantity). Mit GROUP BY gilt das pro Gruppe."),
            ],
        },
        {
            "id": "ch-items",
            "chapter": 0,
            "title": "Auftrag und Positionen",
            "minutes": 12,
            "goal": "Du verbindest Aufträge mit ihren Zeilen in order_items — eins-zu-viele, zum Schreiben.",
            "concepts": ["JOIN"],
            "model": ["SELECT", "FROM", "JOIN", "ON", "GROUP BY"],
            "steps": [
                {
                    "type": "look",
                    "title": "Ein Auftrag, mehrere Zeilen",
                    "text": "`orders` ist der Kopf. `order_items` sind die Positionen: welche Palette, wie viele.\n\n"
                    "Ein Auftrag kann mehrere Zeilen haben. Auftrag **4730** hat keine — genau wie er keinen Kunden hat.",
                    "tables": [
                        orders_table("id", "order_number", "status"),
                        items_table("order_id", "sku", "qty"),
                    ],
                    "cta": "Zeilen markieren",
                },
                {
                    "type": "predict",
                    "title": "Welche Aufträge haben Positionen?",
                    "text": "Markiere die Aufträge, die in `order_items` mindestens eine Zeile haben.",
                    "sql": (
                        "SELECT DISTINCT o.* FROM orders o "
                        "JOIN order_items i ON i.order_id = o.id;"
                    ),
                    "table": orders_table("id", "order_number", "status"),
                    "expected_ids": HAS_ITEMS_IDS,
                    "id_field": "id",
                    "execute": True,
                    "concepts": ["JOIN"],
                    "feedback_ok": "INNER JOIN behält nur Aufträge mit mindestens einer Position. 4730 fehlt.",
                    "feedback_bad": "Nur Aufträge, die in order_items vorkommen. 4730 hat keine Position — den nicht markieren.",
                },
                {
                    "type": "write",
                    "title": "Kopf und Zeile zusammen",
                    "prompt": "Zeig Auftragsnummer, Artikel (`sku`) und Menge der Position (`qty`).",
                    "placeholder": "SELECT …",
                    "solution": (
                        "SELECT o.order_number, i.sku, i.qty "
                        "FROM orders o JOIN order_items i ON i.order_id = o.id;"
                    ),
                    "strict_columns": True,
                    "concepts": ["JOIN"],
                    "hints": [
                        "Zwei Tabellen: orders und order_items. Die Naht ist order_id = o.id.",
                        "SELECT o.order_number, i.sku, i.qty.",
                    ],
                },
                {
                    "type": "apply",
                    "title": "Menge je Auftrag",
                    "prompt": "Zeig je Auftragsnummer die Summe der Positionsmengen. Nur Aufträge, die Positionen haben.",
                    "placeholder": "SELECT …",
                    "solution": (
                        "SELECT o.order_number, SUM(i.qty) "
                        "FROM orders o JOIN order_items i ON i.order_id = o.id "
                        "GROUP BY o.order_number;"
                    ),
                    "concepts": ["JOIN", "GROUP BY"],
                    "hints": [
                        "JOIN wie eben, dann GROUP BY die Auftragsnummer und SUM(i.qty).",
                        "INNER JOIN lässt 4730 automatisch weg.",
                    ],
                },
            ],
            "quiz": [
                Q("Warum gibt es order_items extra?", [
                    "Damit SELECT schneller wird.",
                    "Ein Auftrag kann mehrere Artikelzeilen haben — das passt nicht in eine orders-Spalte.",
                    "Postgres erlaubt nur drei Tabellen.",
                    "sku darf nicht in orders stehen.",
                ], 1, "1:n: ein Kopf, viele Positionen. Sonst würdest du den Auftrag verdoppeln."),
                Q("Was passiert mit 4730 beim INNER JOIN auf order_items?", [
                    "Er bleibt mit qty NULL.",
                    "Er fällt raus — keine passende Position.",
                    "Postgres legt eine leere Position an.",
                    "Er erscheint doppelt.",
                ], 1, "INNER JOIN behält nur Paare. Ohne Position kein Paar."),
                Q("Die Naht zwischen orders und order_items ist …", [
                    "o.client_id = i.sku",
                    "i.order_id = o.id",
                    "o.order_number = i.qty",
                    "ON ohne Spalten.",
                ], 1, "Foreign Key: order_items.order_id zeigt auf orders.id."),
                Q("SUM(i.qty) GROUP BY o.order_number liefert …", [
                    "Eine Zahl fürs ganze Lager.",
                    "Pro Auftrag die addierte Positionsmenge.",
                    "Nur Palette A.",
                    "Jede Position einzeln.",
                ], 1, "Eine Ergebniszeile je Auftrag, darin die Summe seiner Zeilen."),
            ],
        },
        {
            "id": "ch-case",
            "chapter": 0,
            "title": "CASE und COALESCE",
            "minutes": 12,
            "goal": "Du formst Werte um: Labels mit CASE, Lücken mit COALESCE — die Zeile bleibt.",
            "concepts": ["SELECT", "NULL"],
            "model": ["SELECT", "FROM", "JOIN", "ON"],
            "steps": [
                {
                    "type": "explain",
                    "title": "Ein Wert, je nach Fall",
                    "text": "`CASE` prüft Bedingungen und setzt einen anderen Text oder eine andere Zahl.\n\n"
                    "Die Zeile bleibt. Nur die angezeigte Spalte ändert sich.",
                    "sql": (
                        "SELECT order_number,\n"
                        "  CASE status\n"
                        "    WHEN 'offen' THEN 'läuft'\n"
                        "    WHEN 'fertig' THEN 'erledigt'\n"
                        "    ELSE 'anders'\n"
                        "  END\n"
                        "FROM orders;"
                    ),
                    "plain": "Status als lesbares Label, ohne Zeilen zu verlieren.",
                    "parts": [
                        {"match": "CASE status", "token": "CASE", "question": "Wonach?", "answer": "Der Wert in status entscheidet den Zweig."},
                        {"match": "WHEN 'offen' THEN 'läuft'", "token": "WHEN", "question": "Zweig?", "answer": "Stimmt der Status, kommt das Label."},
                        {"match": "ELSE 'anders'", "token": "ELSE", "question": "Sonst?", "answer": "storniert und alles Unbekannte landen hier."},
                    ],
                    "concepts": ["SELECT"],
                },
                {
                    "type": "write",
                    "title": "Status übersetzen",
                    "prompt": "Zeig Auftragsnummer und ein Label: offen → läuft, fertig → erledigt, alles andere → anders.",
                    "placeholder": "SELECT …",
                    "solution": (
                        "SELECT order_number, "
                        "CASE status WHEN 'offen' THEN 'läuft' WHEN 'fertig' THEN 'erledigt' ELSE 'anders' END "
                        "FROM orders;"
                    ),
                    "concepts": ["SELECT"],
                    "hints": [
                        "CASE status WHEN … THEN … ELSE … END. Das END gehört dazu.",
                        "Zwei WHEN-Zweige für offen und fertig, ELSE für den Rest.",
                    ],
                },
                {
                    "type": "look",
                    "title": "Leer ist unbequem zu lesen",
                    "text": "Nach LEFT JOIN ist der Name bei Auftrag **4730** leer. "
                    "`COALESCE` nimmt den ersten Wert, der nicht NULL ist — die Zeile bleibt stehen.",
                    "sql": (
                        "SELECT o.order_number, COALESCE(c.name, 'ohne Kunde')\n"
                        "FROM orders o\n"
                        "LEFT JOIN clients c ON c.id = o.client_id;"
                    ),
                    "tables": [orders_table("id", "order_number", "client")],
                    "cta": "Selbst schreiben",
                },
                {
                    "type": "apply",
                    "title": "Lücke füllen, Zeile behalten",
                    "prompt": "Liste alle Auftragsnummern und den Kundennamen. Fehlt der Kunde, steht **ohne Kunde**.",
                    "placeholder": "SELECT …",
                    "solution": (
                        "SELECT o.order_number, COALESCE(c.name, 'ohne Kunde') "
                        "FROM orders o LEFT JOIN clients c ON c.id = o.client_id;"
                    ),
                    "concepts": ["JOIN", "NULL"],
                    "hints": [
                        "LEFT JOIN, Auftrag links — sonst fällt 4730 weg.",
                        "COALESCE(c.name, 'ohne Kunde') ersetzt die leere Namenszelle.",
                    ],
                },
            ],
            "quiz": [
                Q("Was ändert CASE an der Zeile?", [
                    "Es löscht Zeilen, die nicht passen.",
                    "Nichts an der Zugehörigkeit — nur den angezeigten Wert.",
                    "Es ersetzt WHERE.",
                    "Es macht aus NULL automatisch 0.",
                ], 1, "CASE ist SELECT-Logik. Filter bleibt WHERE."),
                Q("Wozu ist ELSE da?", [
                    "ELSE ist Pflicht in Postgres.",
                    "Für jeden Status, den kein WHEN trifft — sonst wird das Ergebnis NULL.",
                    "ELSE filtert storniert weg.",
                    "ELSE sortiert.",
                ], 1, "Ohne ELSE ist der Rest NULL. ELSE 'anders' macht das sichtbar."),
                Q("COALESCE(c.name, 'ohne Kunde') bei 4730 liefert …", [
                    "NULL.",
                    "ohne Kunde.",
                    "Westfeld.",
                    "Einen Fehler.",
                ], 1, "Der erste nicht-NULL-Wert gewinnt. c.name ist leer, also der Text."),
                Q("Warum COALESCE und nicht WHERE name IS NOT NULL?", [
                    "COALESCE ist schneller.",
                    "WHERE würde 4730 werfen. COALESCE behält die Zeile und füllt die Zelle.",
                    "WHERE kennt keinen Namen.",
                    "COALESCE ersetzt JOIN.",
                ], 1, "Filtern und Ersetzen sind verschieden. Hier soll die Lücke lesbar bleiben."),
            ],
        },
        {
            "id": "ch-subq",
            "chapter": 0,
            "title": "Unterabfragen",
            "minutes": 12,
            "goal": "Du stellst eine Frage in der anderen: IN, EXISTS — und findest Lücken ohne zweiten JOIN-Satz.",
            "concepts": ["SELECT", "JOIN"],
            "model": ["SELECT", "FROM", "WHERE"],
            "steps": [
                {
                    "type": "explain",
                    "title": "Eine Liste aus einer zweiten Frage",
                    "text": "`IN (SELECT …)` nimmt Werte, die eine innere Abfrage liefert.\n\n"
                    "Die innere Frage läuft zuerst: welche `order_id` gibt es in `order_items`? "
                    "Die äußere fragt: welche Aufträge gehören dazu?",
                    "sql": (
                        "SELECT order_number, status\n"
                        "FROM orders\n"
                        "WHERE id IN (SELECT order_id FROM order_items);"
                    ),
                    "plain": "Aufträge, die mindestens eine Position haben.",
                    "parts": [
                        {"match": "WHERE id IN", "token": "IN", "question": "Welche id?", "answer": "Nur Werte, die die Klammer zurückgibt."},
                        {"match": "SELECT order_id FROM order_items", "token": "SELECT", "question": "Innere Frage?", "answer": "Alle Auftrags-ids, die in den Positionen vorkommen."},
                    ],
                    "concepts": ["SELECT"],
                },
                {
                    "type": "predict",
                    "title": "Wer hat keine Position?",
                    "text": "Markiere die Aufträge, die **nicht** in `order_items` vorkommen.",
                    "sql": "SELECT * FROM orders WHERE id NOT IN (SELECT order_id FROM order_items);",
                    "table": orders_table("id", "order_number", "status"),
                    "expected_ids": NO_ITEMS_IDS,
                    "id_field": "id",
                    "execute": True,
                    "concepts": ["SELECT"],
                    "feedback_ok": "Nur 4730 — der Auftrag ohne Positionen.",
                    "feedback_bad": "NOT IN: die Aufträge, deren id in order_items fehlt. Das ist 4730.",
                },
                {
                    "type": "write",
                    "title": "Mit Position, per IN",
                    "prompt": "Zeig Auftragsnummer und Status aller Aufträge, die mindestens eine Position haben. Mit IN, nicht mit JOIN.",
                    "placeholder": "SELECT …",
                    "solution": (
                        "SELECT order_number, status FROM orders "
                        "WHERE id IN (SELECT order_id FROM order_items);"
                    ),
                    "strict_columns": True,
                    "concepts": ["SELECT"],
                    "hints": [
                        "Äußere Tabelle orders. Innere Frage liefert order_id aus order_items.",
                        "WHERE id IN (SELECT order_id FROM order_items).",
                    ],
                },
                {
                    "type": "apply",
                    "title": "Kunde ohne Auftrag",
                    "prompt": "Welche Kunden haben noch keinen Auftrag? Nur der Name. Mit NOT EXISTS.",
                    "placeholder": "SELECT …",
                    "solution": (
                        "SELECT name FROM clients c "
                        "WHERE NOT EXISTS ("
                        "SELECT 1 FROM orders o WHERE o.client_id = c.id"
                        ");"
                    ),
                    "strict_columns": True,
                    "concepts": ["SELECT", "JOIN"],
                    "hints": [
                        "EXISTS prüft: gibt es mindestens eine passende Zeile? NOT dreht das um.",
                        "Innere Frage: orders mit o.client_id = c.id. Westfeld ist der Treffer.",
                    ],
                },
            ],
            "quiz": [
                Q("Was liefert die innere Abfrage bei IN (SELECT order_id FROM order_items)?", [
                    "Ganze Auftragszeilen.",
                    "Eine Liste von order_id-Werten.",
                    "Nur 4730.",
                    "Einen JOIN.",
                ], 1, "IN erwartet Werte. Die innere SELECT-Liste ist eine Spalte."),
                Q("IN und INNER JOIN auf dieselben ids …", [
                    "sind immer verschieden.",
                    "können dieselbe Menge Aufträge liefern — JOIN kann extra Spalten aus der zweiten Tabelle zeigen.",
                    "verbieten GROUP BY.",
                    "brauchen immer HAVING.",
                ], 1, "Für „wer hat Positionen?“ reicht IN. Für sku + qty brauchst du den JOIN."),
                Q("Warum NOT EXISTS statt NOT IN, wenn NULL im Spiel sein kann?", [
                    "EXISTS ist kürzer.",
                    "NOT IN wird knifflig, sobald die innere Liste NULL enthält. EXISTS prüft nur: gibt es eine Zeile?",
                    "NOT IN ist in Postgres verboten.",
                    "EXISTS sortiert automatisch.",
                ], 1, "Westfeld: keine orders-Zeile mit seiner id. NOT EXISTS ist dafür der klare Satz."),
                Q("Was ist Westfeld in dieser Lektion?", [
                    "Ein Auftrag ohne Position.",
                    "Ein Kunde ohne Auftrag — die innere Frage findet keine Zeile.",
                    "Ein Status.",
                    "Ein JOIN-Typ.",
                ], 1, "Dieselbe Lücke wie beim Anti-Join, nur als Unterabfrage."),
            ],
        },
        {
            "id": "challenge-4",
            "chapter": 0,
            "title": "Challenge: SKUs in offenen Aufträgen",
            "minutes": 10,
            "goal": "Du verbindest Positionen mit Aufträgen, filterst, summierst und sortierst — ohne Syntax-Liste.",
            "concepts": ["JOIN", "GROUP BY", "WHERE"],
            "challenge": True,
            "model": ["SELECT", "FROM", "JOIN", "ON", "WHERE", "GROUP BY", "ORDER BY"],
            "steps": [
                {
                    "type": "look",
                    "title": "Die Frage steht, nicht das SQL",
                    "text": "Artikel stecken in `order_items`. Offen oder fertig steht in `orders`.\n\n"
                    "Du entscheidest Naht, Filter und ob du auflistest oder addierst.",
                    "tables": [
                        orders_table("id", "order_number", "status"),
                        items_table("order_id", "sku", "qty"),
                    ],
                    "cta": "Aufgabe öffnen",
                },
                {
                    "type": "challenge",
                    "title": "Lagerfrage",
                    "prompt": "Welche Artikel (`sku`) stecken in **offenen** Aufträgen — und wie viel Menge insgesamt? "
                    "Die größte Menge zuerst.",
                    "placeholder": "Übersetze die Frage in SQL…",
                    "solution": (
                        "SELECT i.sku, SUM(i.qty) FROM order_items i "
                        "JOIN orders o ON o.id = i.order_id "
                        "WHERE o.status = 'offen' "
                        "GROUP BY i.sku ORDER BY SUM(i.qty) DESC;"
                    ),
                    "strict_columns": True,
                    "ordered": True,
                    "concepts": ["JOIN", "GROUP BY", "WHERE"],
                    "hints": [
                        "sku und qty: order_items. Status: orders. Welche Naht, welcher Filter?",
                        "GROUP BY sku, SUM(qty), offene Aufträge in WHERE, größte Summe zuerst.",
                    ],
                },
            ],
            "quiz": [
                Q("Warum brauchst du orders, obwohl sku in order_items steht?", [
                    "orders hat die schöneren Namen.",
                    "Ob der Auftrag offen ist, steht nur im Kopf — nicht in der Position.",
                    "JOIN ist immer Pflicht.",
                    "sku gibt es in orders auch.",
                ], 1, "Position kennt den Artikel. Der Kopf kennt den Status."),
                Q("Wohin gehört status = 'offen'?", [
                    "Nach HAVING, weil du SUM benutzt.",
                    "Nach WHERE — Eigenschaft der Auftragszeile, bevor die Gruppen feststehen.",
                    "Nur in SELECT.",
                    "In ON statt in WHERE.",
                ], 1, "Status ist keine Gruppenbedingung."),
                Q("Warum GROUP BY sku?", [
                    "Sonst kennt SQL den Artikelnamen nicht.",
                    "Du willst eine Zeile pro Artikel, darin die addierte Menge.",
                    "GROUP BY sortiert.",
                    "Ohne GROUP BY geht JOIN nicht.",
                ], 1, "SUM ohne Gruppe wäre eine Zahl für alles."),
                Q("Was wäre INNER vs LEFT JOIN hier?", [
                    "LEFT JOIN von items → orders würde Positionen ohne Auftrag behalten — die Aufgabe will offene Aufträge.",
                    "LEFT JOIN ist verboten.",
                    "INNER JOIN verliert immer sku.",
                    "Es gibt keinen Unterschied.",
                ], 0, "Positionen gehören zu Aufträgen. INNER JOIN auf den Kopf, dann Status filtern, reicht."),
            ],
        },
    ]
