"""Beginner SQL academy: interactive steps, not documentation pages."""

CLIENT_NAMES = {10: "Helio", 20: "Alpin", 30: "Nordkai"}


def O(oid, number, client_id, status, quantity, created):
    return {
        "id": oid,
        "order_number": number,
        "client_id": client_id,
        "client": CLIENT_NAMES.get(client_id),
        "status": status,
        "quantity": quantity,
        "created_at": created,
    }


ORDERS = [
    O(1, 4711, 10, "offen", 12, "2026-09-08"),
    O(2, 4712, 20, "fertig", 4, "2026-09-07"),
    O(3, 4713, 10, "offen", 25, "2026-09-09"),
    O(4, 4714, 20, "offen", 8, "2026-09-06"),
    O(5, 4715, 10, "fertig", 30, "2026-09-05"),
    O(6, 4716, 30, "offen", 15, "2026-09-10"),
    O(7, 4717, 20, "storniert", 2, "2026-09-04"),
    O(8, 4718, 10, "offen", 50, "2026-09-10"),
    O(9, 4719, 10, "offen", 18, "2026-09-11"),
    O(10, 4720, 20, "fertig", 22, "2026-09-03"),
    O(11, 4721, 30, "fertig", 9, "2026-09-02"),
    O(12, 4722, 30, "offen", 6, "2026-09-12"),
    O(13, 4723, 10, "storniert", 11, "2026-09-01"),
    O(14, 4724, 20, "offen", 40, "2026-09-13"),
    O(15, 4725, 30, "offen", 3, "2026-09-08"),
    O(16, 4726, 10, "fertig", 7, "2026-09-14"),
    O(17, 4727, 20, "offen", 16, "2026-09-15"),
    O(18, 4728, 30, "storniert", 5, "2026-09-06"),
    O(19, 4729, 10, "offen", 100, "2026-09-16"),
    O(20, 4730, None, "offen", 14, "2026-09-09"),
    O(21, 4731, 20, "offen", None, "2026-09-11"),
    O(22, 4732, 10, "fertig", None, "2026-09-07"),
    O(23, 4733, 30, "offen", 1, "2026-09-17"),
    O(24, 4734, 10, "offen", 13, "2026-09-18"),
]

STOCK = [
    {"id": 1, "item": "Palette A", "quantity": 40, "weight": 120},
    {"id": 2, "item": "Palette B", "quantity": 8, "weight": 80},
    {"id": 3, "item": "Karton C", "quantity": 15, "weight": 25},
    {"id": 4, "item": "Palette D", "quantity": 3, "weight": 100},
    {"id": 5, "item": "Karton E", "quantity": None, "weight": 40},
    {"id": 6, "item": "Folie F", "quantity": 12, "weight": None},
    {"id": 7, "item": "Palette G", "quantity": 0, "weight": 50},
]

CLIENTS = [
    {"id": 10, "name": "Helio", "country": "AT"},
    {"id": 20, "name": "Alpin", "country": "DE"},
    {"id": 30, "name": "Nordkai", "country": "CH"},
    {"id": 40, "name": "Westfeld", "country": "DE"},
]

CONCEPTS = [
    {"id": "TABLE", "label": "Tabellen"},
    {"id": "SELECT", "label": "SELECT"},
    {"id": "FROM", "label": "FROM"},
    {"id": "WHERE", "label": "WHERE"},
    {"id": "COMPARE", "label": "Vergleiche"},
    {"id": "AND", "label": "AND / OR"},
    {"id": "ORDER BY", "label": "ORDER BY"},
    {"id": "LIMIT", "label": "LIMIT"},
    {"id": "NULL", "label": "NULL"},
    {"id": "GROUP BY", "label": "GROUP BY"},
    {"id": "JOIN", "label": "JOIN"},
    {"id": "HAVING", "label": "HAVING"},
    {"id": "CASE", "label": "CASE"},
    {"id": "SUBQUERY", "label": "Unterabfrage"},
    {"id": "DML", "label": "Ändern"},
    {"id": "TX", "label": "Transaktionen"},
]

PATH_IDS = [
    "ch0",
    "ch1",
    "ch2",
    "ch3",
    "ch4",
    "ch5",
    "ch6",
    "ch7",
    "ch-alias",
    "ch8",
    "ch-agg",
    "ch-having",
    "ch-keys",
    "ch9",
    "ch10",
    "ch-items",
    "ch-case",
    "challenge-1",
    "challenge-2",
    "ch-subq",
    "challenge-4",
    "ch-dml",
    "ch-tx",
    "ch-pg",
    "challenge-3",
]


def table(name, label, rows, columns=None):
    columns = columns or list(rows[0].keys())
    return {
        "name": name,
        "label": label,
        "columns": columns,
        "rows": [{k: r[k] for k in columns} for r in rows],
    }


def orders_table(*columns):
    cols = list(columns) if columns else ["id", "order_number", "client", "status"]
    return table("orders", "Aufträge", ORDERS, cols)


def stock_table(*columns):
    cols = list(columns) if columns else ["id", "item", "quantity", "weight"]
    return table("stock", "Bestand", STOCK, cols)


def clients_table(*columns):
    cols = list(columns) if columns else ["id", "name", "country"]
    return table("clients", "Kunden", CLIENTS, cols)


def ids(*preds, rows=None):
    rows = rows or ORDERS
    return [r["id"] for r in rows if all(p(r) for p in preds)]


def Q(q, options, correct, explain):
    return {"q": q, "options": options, "correct": correct, "explain": explain}


N_ORDERS = len(ORDERS)
OFFEN = ids(lambda r: r["status"] == "offen")
FERTIG = ids(lambda r: r["status"] == "fertig")
HELIO_OFFEN = ids(lambda r: r["client"] == "Helio" and r["status"] == "offen")
QTY_GT_10 = ids(lambda r: r["quantity"] is not None and r["quantity"] > 10)
NOT_FERTIG = ids(lambda r: r["status"] != "fertig")
QTY_BETWEEN = ids(lambda r: r["quantity"] is not None and 10 <= r["quantity"] <= 20)
QTY_NULL = ids(lambda r: r["quantity"] is None)
HAS_CLIENT = ids(lambda r: r["client_id"] is not None)
NO_CLIENT = ids(lambda r: r["client_id"] is None)
STOCK_HEAVY = [r["id"] for r in STOCK if r["weight"] is not None and r["weight"] >= 100]
STOCK_PALETTE = [r["id"] for r in STOCK if (r["item"] or "").startswith("Palette")]
STOCK_WEIGHT_NULL = [r["id"] for r in STOCK if r["weight"] is None]


HINT_SELECT = [
    "Zwei Teile: SELECT sagt, was du sehen willst. FROM sagt, aus welcher Tabelle.",
    "Die Auftragstabelle heißt `orders`. Alle Spalten: Stern `*`.",
]
HINT_WHERE = [
    "Du willst nicht alle Zeilen. Dafür filterst du mit WHERE.",
    "Textwerte stehen in einfachen Anführungszeichen: status = 'offen'.",
]


ACADEMY = {
    "id": "sql",
    "label": "PostgreSQL Grundlagen",
    "blurb": "Vom ersten Blick in eine Tabelle bis zu JOIN, Gruppen, Änderungen und dem Postgres-Modell.",
    "concepts": CONCEPTS,
    "lessons": [
        {
            "id": "ch0",
            "chapter": 0,
            "title": "Daten verstehen",
            "minutes": 8,
            "goal": "Du erkennst Zeilen, Spalten, Werte und IDs — noch ohne SQL zu schreiben.",
            "concepts": ["TABLE"],
            "model": ["TABLE"],
            "steps": [
                {
                    "type": "look",
                    "title": "Eine Tabelle voller Aufträge",
                    "text": "Das hier ist eine **Tabelle**. Stell sie dir wie eine Excel-Liste vor: oben die Überschriften, darunter die Einträge.",
                    "table": orders_table(),
                    "note": "Jede Zeile ist ein Auftrag. Jede Spalte ist eine Art von Information. Leere Zellen heißen später NULL — erstmal die vollen ansehen.",
                    "cta": "Ich habe die Tabelle angesehen",
                },
                {
                    "type": "inspect",
                    "title": "Welche Spalte enthält den Kunden?",
                    "text": "Tippe auf die **Spaltenüberschrift**, in der der Kundenname steht.",
                    "table": orders_table(),
                    "interaction": "click_column",
                    "answer": "client",
                    "concepts": ["TABLE"],
                    "feedback_ok": "Genau. Die Spalte `client` speichert, zu wem der Auftrag gehört.",
                    "feedback_bad": "In der Spalte `client` stehen Namen wie Helio und Alpin. Tippe auf diese Überschrift.",
                },
                {
                    "type": "inspect",
                    "title": "Wie viele Datensätze sind das?",
                    "text": "Ein Datensatz ist eine **Zeile**. Wie viele Aufträge liegen in der Tabelle?",
                    "table": orders_table(),
                    "interaction": "number",
                    "answer": N_ORDERS,
                    "concepts": ["TABLE"],
                    "feedback_ok": f"Richtig — {N_ORDERS} Zeilen, also {N_ORDERS} Aufträge.",
                    "feedback_bad": "Zähle die Zeilen unter der Überschrift — jede Zeile ist ein Auftrag, die Überschrift nicht.",
                },
                {
                    "type": "inspect",
                    "title": "Welchen Status hat Auftrag 4712?",
                    "text": "Finde die Zeile mit Auftragsnummer **4712** und tippe auf den Status-Wert.",
                    "table": orders_table(),
                    "interaction": "click_cell",
                    "answer": {"column": "status", "value": "fertig"},
                    "concepts": ["TABLE"],
                    "feedback_ok": "Auftrag 4712 ist `fertig` — abgeschlossen.",
                    "feedback_bad": "Finde in `order_number` die 4712. In derselben Zeile steht rechts der Status — den Wert antippen.",
                },
                {
                    "type": "inspect",
                    "title": "Markiere den kompletten Auftrag 4713",
                    "text": "Eine **Zeile** gehört immer zusammen. Tippe irgendwo in die Zeile von Auftrag **4713**.",
                    "table": orders_table(),
                    "interaction": "click_row",
                    "id_field": "order_number",
                    "answer": 4713,
                    "concepts": ["TABLE"],
                    "feedback_ok": "Das ist ein Datensatz: id 3, Nummer 4713, Kunde Helio, Status offen.",
                    "feedback_bad": "Eine ganze Zeile markieren: irgendwo in die Zeile mit `order_number` 4713 klicken.",
                },
                {
                    "type": "look",
                    "title": "Genau solche Fragen stellen wir gleich SQL",
                    "text": "Du hast gerade von Hand gesucht: Welche Spalte? Welche Zeile? Welcher Wert?\n\nEine Datenbank kann dieselben Fragen beantworten — mit einer kurzen Anweisung namens **SQL**.\n\nAls Nächstes siehst du die erste Abfrage. Du musst sie noch nicht schreiben.",
                    "table": orders_table(),
                    "cta": "Weiter zur ersten Abfrage",
                },
            ],
            "quiz": [
                Q("Wozu ist die Spalte id da?", [
                    "Eine eindeutige Nummer für genau diesen Datensatz.",
                    "Die Anzahl der Aufträge in der Tabelle.",
                    "Der Name des Kunden.",
                    "Der Status des Auftrags.",
                ], 0, "Die id identifiziert eine Zeile. Zwei Aufträge können denselben Kunden haben — aber nie dieselbe id."),
                Q("Was ist eine Zeile in der Tabelle orders?", [
                    "Eine Spaltenüberschrift.",
                    "Ein Auftrag (ein Datensatz).",
                    "Die ganze Datenbank.",
                    "Nur der Kundenname.",
                ], 1, "Eine Zeile = ein Datensatz. Hier: ein Auftrag mit Nummer, Kunde, Status."),
                Q("Was ist eine Spalte?", [
                    "Ein einzelner Auftrag.",
                    "Eine Art von Information, die in jeder Zeile vorkommt (z. B. status).",
                    "Immer genau acht Werte.",
                    "Dasselbe wie eine Tabelle.",
                ], 1, "Spalten sind die Überschriften: dieselbe Frage an jede Zeile."),
                Q("Warum reicht der Kundenname allein nicht als Schlüssel?", [
                    "Namen darf man in SQL nicht speichern.",
                    "Mehrere Aufträge können denselben Kunden haben.",
                    "Kunden stehen nie in Tabellen.",
                    "SQL kennt keine Textwerte.",
                ], 1, "Helio hat viele Aufträge. Eindeutig ist die id, nicht der Name."),
            ],
        },
        {
            "id": "ch1",
            "chapter": 1,
            "title": "Die erste SQL-Abfrage",
            "minutes": 10,
            "goal": "Du verstehst SELECT * FROM orders und führst deine erste Abfrage aus.",
            "concepts": ["SELECT", "FROM"],
            "model": ["SELECT", "FROM"],
            "steps": [
                {
                    "type": "explain",
                    "title": "SQL ist eine Frage an die Tabelle",
                    "text": "Klicke die beiden Teile an. Jeder Teil beantwortet eine Frage.",
                    "sql": "SELECT *\nFROM orders;",
                    "plain": "Zeige mir alle Informationen aus den Aufträgen.",
                    "parts": [
                        {
                            "match": "SELECT *",
                            "token": "SELECT",
                            "question": "Was möchte ich sehen?",
                            "answer": "Alle Spalten. Der Stern `*` bedeutet „alles“.",
                        },
                        {
                            "match": "FROM orders",
                            "token": "FROM",
                            "question": "Woher kommen die Daten?",
                            "answer": "Aus der Tabelle `orders` — unseren Aufträgen.",
                        },
                    ],
                    "concepts": ["SELECT", "FROM"],
                },
                {
                    "type": "demo",
                    "title": "Ausführen und vergleichen",
                    "text": "Links die Tabelle **vorher**. Führe die Query aus — rechts siehst du, was SQL zurückgibt. Bei `SELECT *` sind das dieselben Zeilen.",
                    "sql": "SELECT * FROM orders;",
                    "table": orders_table("id", "order_number", "client", "status"),
                    "visualize": "all",
                    "concepts": ["SELECT", "FROM"],
                },
                {
                    "type": "predict",
                    "title": "Welche Zeilen kommen zurück?",
                    "text": "Diese Query holt alle Spalten, ohne zu filtern. Markiere die Zeilen, die im Ergebnis erscheinen.",
                    "sql": "SELECT * FROM orders;",
                    "table": orders_table(),
                    "expected_ids": ids(lambda r: True),
                    "id_field": "id",
                    "execute": True,
                    "concepts": ["SELECT", "FROM"],
                    "feedback_ok": f"Richtig: ohne WHERE kommen alle {N_ORDERS} Aufträge zurück.",
                    "feedback_bad": "Ohne `WHERE` filtert die Query nicht. Markiere deshalb jeden Auftrag.",
                },
                {
                    "type": "build",
                    "title": "Baue die erste Query",
                    "prompt": "Zeige alle Spalten aller Aufträge.",
                    "pieces": ["SELECT", "*", "FROM", "orders"],
                    "distractors": ["WHERE", "clients"],
                    "solution": "SELECT * FROM orders;",
                    "concepts": ["SELECT", "FROM"],
                    "hints": HINT_SELECT,
                },
                {
                    "type": "write",
                    "title": "Jetzt selbst schreiben",
                    "prompt": "Zeige alle Informationen aus der Tabelle orders.",
                    "starter": "",
                    "placeholder": "SELECT …",
                    "solution": "SELECT * FROM orders;",
                    "concepts": ["SELECT", "FROM"],
                    "hints": HINT_SELECT,
                },
            ],
            "quiz": [
                Q("Was bedeutet der Stern * nach SELECT?", [
                    "Nur die erste Spalte.",
                    "Alle Spalten der Tabelle.",
                    "Nur Zeilen mit Status offen.",
                    "Die Tabelle clients.",
                ], 1, "`*` heißt: jede Spalte. Später nennst du Spalten namentlich, wenn du nicht alles brauchst."),
                Q("Wofür ist FROM da?", [
                    "Zum Sortieren.",
                    "Zum Filtern von Zeilen.",
                    "Es sagt, aus welcher Tabelle die Daten kommen.",
                    "Es löscht die Tabelle.",
                ], 2, "FROM = woher. SELECT = was. WHERE (kommt später) = welche Zeilen."),
                Q("Was passiert ohne WHERE?", [
                    "SQL liefert keine Zeilen.",
                    "SQL liefert alle Zeilen der Tabelle.",
                    "SQL nimmt nur die erste Zeile.",
                    "Die Abfrage ist ungültig.",
                ], 1, "Ohne Filter kommen alle Datensätze."),
                Q("Welche Reihenfolge der Satzteile ist üblich?", [
                    "FROM, dann SELECT",
                    "SELECT, dann FROM",
                    "Nur SELECT reicht immer",
                    "WHERE muss vor SELECT stehen",
                ], 1, "Wir schreiben SELECT … FROM … — auch wenn die Datenbank intern zuerst FROM liest."),
            ],
        },
        {
            "id": "ch2",
            "chapter": 2,
            "title": "SELECT verstehen",
            "minutes": 10,
            "goal": "SELECT bestimmt, welche Informationen im Ergebnis erscheinen — nicht, welche Zeilen.",
            "concepts": ["SELECT"],
            "model": ["SELECT", "FROM"],
            "steps": [
                {
                    "type": "look",
                    "title": "SELECT wählt Spalten",
                    "text": "`WHERE` (kommt gleich) filtert **Zeilen**. `SELECT` wählt **Spalten**.\n\nStell dir vor, du blendest in Excel Spalten aus — die Zeilen bleiben.",
                    "table": orders_table("order_number", "status"),
                    "note": f"Nur Nummer und Status — id und Kunde sind weg, aber alle {N_ORDERS} Aufträge sind noch da.",
                    "cta": "Weiter",
                },
                {
                    "type": "predict-cols",
                    "title": "Welche Spalten erscheinen?",
                    "text": "Markiere die Spalten, die diese Query im Ergebnis hat.",
                    "sql": "SELECT order_number, status\nFROM orders;",
                    "table": orders_table(),
                    "expected_columns": ["order_number", "status"],
                    "concepts": ["SELECT"],
                    "feedback_ok": "Ja: nur `order_number` und `status`. Die Zeilen bleiben alle.",
                    "feedback_bad": "Nach `SELECT` stehen nur `order_number` und `status`. Genau diese beiden Überschriften markieren.",
                },
                {
                    "type": "demo",
                    "title": "Query ausführen",
                    "text": "Sieh zu, wie aus vier Spalten zwei werden.",
                    "sql": "SELECT order_number, status FROM orders;",
                    "table": orders_table(),
                    "visualize": "columns",
                    "keep_columns": ["order_number", "status"],
                    "concepts": ["SELECT"],
                },
                {
                    "type": "write",
                    "title": "Selbst wählen",
                    "prompt": "Zeige zu jedem Auftrag den Kunden und den Status.",
                    "placeholder": "SELECT …",
                    "solution": "SELECT client, status FROM orders;",
                    "strict_columns": True,
                    "concepts": ["SELECT"],
                    "hints": [
                        "Zwei Spalten, getrennt durch Komma. Kein WHERE nötig.",
                        "Die Kundenspalte heißt `client`, der Status `status`.",
                    ],
                },
                {
                    "type": "apply",
                    "title": "Nur die Nummern",
                    "prompt": "Die Halle will eine schlanke Liste: nur die Auftragsnummern.",
                    "placeholder": "SELECT …",
                    "solution": "SELECT order_number FROM orders;",
                    "strict_columns": True,
                    "concepts": ["SELECT"],
                    "hints": [
                        "Eine Spalte reicht. Der Stern `*` wäre zu viel.",
                        "Die Spalte heißt `order_number`.",
                    ],
                },
            ],
            "quiz": [
                Q("Was bestimmt SELECT?", [
                    "Welche Informationen (Spalten) im Ergebnis erscheinen.",
                    "Welche Zeilen gelöscht werden.",
                    "Wie die Tabelle heißt.",
                    "Die Sortierung.",
                ], 0, "FROM sagt woher, SELECT sagt was. Zeilen filtert später WHERE."),
                Q("Was passiert mit den Zeilen, wenn du nur zwei Spalten auswählst?", [
                    "Es bleibt nur noch eine Zeile.",
                    "Die Zeilen bleiben; ausgeblendet werden Spalten.",
                    "SQL sortiert automatisch.",
                    "Leere Zeilen verschwinden.",
                ], 1, "SELECT blendet Spalten aus, löscht aber keine Datensätze."),
                Q("Wie trennst du zwei Spalten in der SELECT-Liste?", [
                    "Mit einem Punkt.",
                    "Mit einem Komma.",
                    "Mit AND.",
                    "Mit FROM.",
                ], 1, "`SELECT client, status` — Komma zwischen den Namen."),
                Q("Wann ist SELECT * unpraktisch?", [
                    "Immer — Stern ist verboten.",
                    "Wenn du nur wenige Spalten brauchst oder die Tabelle sehr breit ist.",
                    "Nur bei leeren Tabellen.",
                    "Nur zusammen mit WHERE.",
                ], 1, "Zum Entdecken ist `*` gut. Für Reports nennst du die Spalten."),
            ],
        },
        {
            "id": "ch3",
            "chapter": 3,
            "title": "WHERE",
            "minutes": 12,
            "goal": "WHERE entscheidet, welche Zeilen berücksichtigt werden.",
            "concepts": ["WHERE"],
            "model": ["SELECT", "FROM", "WHERE"],
            "steps": [
                {
                    "type": "explain",
                    "title": "Nicht alle Zeilen sind interessant",
                    "text": "Im Lager willst du oft nur die **offenen** Aufträge. Dafür kommt ein dritter Satzteil dazu.",
                    "sql": "SELECT *\nFROM orders\nWHERE status = 'offen';",
                    "plain": "Zeige alle Spalten der Aufträge, aber nur die mit Status offen.",
                    "parts": [
                        {"match": "SELECT *", "token": "SELECT", "question": "Was?", "answer": "Alle Spalten."},
                        {"match": "FROM orders", "token": "FROM", "question": "Woher?", "answer": "Aus den Aufträgen."},
                        {
                            "match": "WHERE status = 'offen'",
                            "token": "WHERE",
                            "question": "Welche?",
                            "answer": "Nur Zeilen, bei denen status genau `offen` ist. Textwerte stehen in einfachen Anführungszeichen.",
                        },
                    ],
                    "concepts": ["WHERE"],
                },
                {
                    "type": "demo",
                    "title": "Die anderen Zeilen fallen weg",
                    "text": "Führe aus. Nicht passende Zeilen werden ausgegraut — SQL liefert sie nicht mit.",
                    "sql": "SELECT * FROM orders WHERE status = 'offen';",
                    "table": orders_table(),
                    "visualize": "where",
                    "match_column": "status",
                    "match_value": "offen",
                    "concepts": ["WHERE"],
                },
                {
                    "type": "predict",
                    "title": "Welche Datensätze kommen zurück?",
                    "text": "Markiere die Zeilen, die diese Abfrage liefert.",
                    "sql": "SELECT * FROM orders WHERE status = 'offen';",
                    "table": orders_table(),
                    "expected_ids": OFFEN,
                    "id_field": "id",
                    "execute": True,
                    "visualize": "where",
                    "concepts": ["WHERE"],
                    "feedback_ok": "Nur Zeilen mit status = offen. fertig und storniert bleiben draußen.",
                    "feedback_bad": "Nur Zeilen mit `status` = `offen`. `fertig` und `storniert` nicht markieren.",
                },
                {
                    "type": "build",
                    "title": "Filter bauen",
                    "prompt": "Zeige alle offenen Aufträge.",
                    "pieces": ["SELECT", "*", "FROM", "orders", "WHERE", "status", "=", "'offen'"],
                    "distractors": ["'fertig'", "ORDER", "BY"],
                    "solution": "SELECT * FROM orders WHERE status = 'offen';",
                    "concepts": ["WHERE"],
                    "hints": HINT_WHERE,
                },
                {
                    "type": "write",
                    "title": "Selbst filtern",
                    "prompt": "Zeige alle abgeschlossenen Aufträge (Status fertig).",
                    "placeholder": "SELECT …",
                    "solution": "SELECT * FROM orders WHERE status = 'fertig';",
                    "concepts": ["WHERE"],
                    "hints": [
                        "Dieselbe Struktur wie eben, nur ein anderer Status-Wert.",
                        "Der Wert heißt `fertig`, in Anführungszeichen.",
                    ],
                },
                {
                    "type": "apply",
                    "title": "Ohne den Befehl zu verraten",
                    "prompt": "Im Lager liegen viele Aufträge. Finde alle Aufträge von Alpin.",
                    "placeholder": "SELECT …",
                    "solution": "SELECT * FROM orders WHERE client = 'Alpin';",
                    "concepts": ["WHERE"],
                    "hints": [
                        "Du suchst nicht alle Zeilen — nur die eines Kunden.",
                        "Die Kundenspalte heißt `client`.",
                    ],
                },
            ],
            "quiz": [
                Q("Wofür ist WHERE da?", [
                    "Spalten auswählen.",
                    "Zeilen filtern.",
                    "Tabellen umbenennen.",
                    "Ergebnisse sortieren.",
                ], 1, "WHERE entscheidet, welche Datensätze übrig bleiben."),
                Q("Warum stehen Textwerte in einfachen Anführungszeichen?", [
                    "SQL verlangt immer Anführungszeichen, auch bei Zahlen.",
                    "Sonst hält SQL den Text für einen Spaltennamen.",
                    "Doppelte Anführungszeichen sind verboten.",
                    "Nur bei Kunden, nicht bei Status.",
                ], 1, "`status = offen` ohne Quotes sucht eine Spalte namens offen. Richtig: `'offen'`."),
                Q("Was liefert WHERE status = 'offen'?", [
                    "Alle Aufträge.",
                    "Nur Aufträge mit genau diesem Status.",
                    "Nur die erste offene Zeile.",
                    "Nur Helio-Aufträge.",
                ], 1, "Gleichheit ist exakt. `fertig` und `storniert` fallen weg."),
                Q("Filtert WHERE Spalten oder Zeilen?", [
                    "Spalten — wie SELECT.",
                    "Zeilen — Datensätze.",
                    "Beides immer gleichzeitig.",
                    "Weder noch, es sortiert nur.",
                ], 1, "SELECT = Spalten, WHERE = Zeilen."),
            ],
        },
        {
            "id": "ch4",
            "chapter": 4,
            "title": "Vergleiche",
            "minutes": 12,
            "goal": "Du nutzt =, !=, >, LIKE, IN und BETWEEN bewusst pro Zeile.",
            "concepts": ["COMPARE", "WHERE"],
            "model": ["SELECT", "FROM", "WHERE"],
            "steps": [
                {
                    "type": "look",
                    "title": "Vergleich ist eine Ja/Nein-Frage pro Zeile",
                    "text": "SQL prüft jede Zeile: Ist die Bedingung wahr?\n\n`=` gleich · `!=` ungleich · `>` größer · `<` kleiner · `>=` mindestens · `<=` höchstens\n\nDazu später: `LIKE` (Muster), `IN` (Liste), `BETWEEN` (Bereich).",
                    "table": orders_table("order_number", "client", "quantity"),
                    "note": "quantity ist die bestellte Menge. Leere Mengen (NULL) sind bei Zahlenvergleichen nicht wahr — die kommen in Kapitel 7.",
                    "cta": "Zeilen markieren",
                },
                {
                    "type": "predict",
                    "title": "quantity > 10",
                    "text": "Markiere jede Zeile, für die `quantity > 10` wahr ist.",
                    "sql": "SELECT * FROM orders WHERE quantity > 10;",
                    "table": orders_table("id", "order_number", "client", "quantity"),
                    "expected_ids": QTY_GT_10,
                    "id_field": "id",
                    "execute": True,
                    "concepts": ["COMPARE"],
                    "feedback_ok": "`>` bedeutet echt größer als 10. NULL-Mengen zählen nicht — unbekannt ist nicht wahr.",
                    "feedback_bad": "`>` heißt echt größer als 10. Die 10 selbst und leere `quantity`-Zellen zählen nicht.",
                },
                {
                    "type": "predict",
                    "title": "Nicht abgeschlossen",
                    "text": "Markiere die Zeilen für `status != 'fertig'`.",
                    "sql": "SELECT * FROM orders WHERE status != 'fertig';",
                    "table": orders_table(),
                    "expected_ids": NOT_FERTIG,
                    "id_field": "id",
                    "execute": True,
                    "concepts": ["COMPARE"],
                    "feedback_ok": "`!=` schließt nur `fertig` aus. Offen und storniert bleiben.",
                    "feedback_bad": "`!= 'fertig'` lässt `offen` und `storniert` drin. Beide markieren.",
                },
                {
                    "type": "predict",
                    "title": "Schwere Paletten",
                    "text": "Im Bestand: welche Zeilen erfüllen `weight >= 100`?",
                    "sql": "SELECT * FROM stock WHERE weight >= 100;",
                    "table": stock_table(),
                    "expected_ids": STOCK_HEAVY,
                    "id_field": "id",
                    "execute": True,
                    "concepts": ["COMPARE"],
                    "feedback_ok": "`>=` nimmt 100 mit. Palette A (120) und Palette D (100).",
                    "feedback_bad": "`>= 100` nimmt 100 mit. Palette A (120) und Palette D (100).",
                },
                {
                    "type": "write",
                    "title": "LIKE: Namen mit Muster",
                    "prompt": "Zeige alle Bestandszeilen, deren Bezeichnung mit Palette beginnt.",
                    "placeholder": "SELECT …",
                    "solution": "SELECT * FROM stock WHERE item LIKE 'Palette%';",
                    "require": ["LIKE"],
                    "concepts": ["COMPARE"],
                    "hints": [
                        "`LIKE` vergleicht mit einem Muster. `%` steht für beliebigen Rest.",
                        "Die Spalte heißt `item`, die Tabelle `stock`.",
                    ],
                },
                {
                    "type": "write",
                    "title": "IN und BETWEEN",
                    "prompt": "Zeige Aufträge, deren Menge zwischen 10 und 20 liegt (beide Grenzen inklusive).",
                    "placeholder": "SELECT …",
                    "solution": "SELECT * FROM orders WHERE quantity BETWEEN 10 AND 20;",
                    "require": ["BETWEEN"],
                    "concepts": ["COMPARE"],
                    "hints": [
                        "`BETWEEN a AND b` nimmt a und b mit. NULL-Mengen liegen in keinem Bereich.",
                        "Die Spalte heißt `quantity`.",
                    ],
                },
                {
                    "type": "apply",
                    "title": "Eine Liste von Statuswerten",
                    "prompt": "Zeige Aufträge, die offen oder storniert sind — mit IN, nicht mit OR.",
                    "placeholder": "SELECT …",
                    "solution": "SELECT * FROM orders WHERE status IN ('offen', 'storniert');",
                    "require": ["IN"],
                    "concepts": ["COMPARE"],
                    "hints": [
                        "`IN ('wert1', 'wert2')` ist eine Liste. Komma zwischen den Werten.",
                        "Die Spalte heißt `status`.",
                    ],
                },
            ],
            "quiz": [
                Q("Was bedeutet >= 100?", [
                    "Nur Werte über 100, 100 selbst nicht.",
                    "Mindestens 100, die 100 zählt mit.",
                    "Genau 100.",
                    "Alle Werte unter 100.",
                ], 1, "`>=` ist „größer oder gleich“."),
                Q("Wofür steht % in LIKE 'Palette%'?", [
                    "Prozentrechnung.",
                    "Beliebiger Text danach, auch leer.",
                    "Genau ein Zeichen.",
                    "Nur Zahlen.",
                ], 1, "`Palette%` trifft Palette A, Palette G, …"),
                Q("Was macht IN ('offen', 'storniert')?", [
                    "Beide Werte müssen in derselben Zelle stehen.",
                    "Der Status ist einer der genannten Werte.",
                    "SQL sortiert nach diesen Werten.",
                    "Es ist dasselbe wie BETWEEN.",
                ], 1, "`IN` ist eine Liste erlaubter Werte. Entspricht OR, liest sich kürzer."),
                Q("Liegt eine leere Menge (NULL) in BETWEEN 10 AND 20?", [
                    "Ja, NULL zählt als 0.",
                    "Nein. NULL ist unbekannt und fällt bei solchen Vergleichen weg.",
                    "Nur am Montag.",
                    "Ja, NULL liegt in jedem Bereich.",
                ], 1, "Vergleiche mit NULL sind nicht wahr. Dafür gibt es später `IS NULL`."),
            ],
        },
        {
            "id": "ch5",
            "chapter": 5,
            "title": "AND / OR / NOT",
            "minutes": 12,
            "goal": "Du trennst bewusst: beide Bedingungen (AND) oder mindestens eine (OR).",
            "concepts": ["AND"],
            "model": ["SELECT", "FROM", "WHERE"],
            "steps": [
                {
                    "type": "look",
                    "title": "Zwei Bedingungen, ein Unterschied",
                    "text": "**AND** — beide Bedingungen müssen stimmen.\n\n**OR** — mindestens eine muss stimmen.\n\n**NOT** — die Bedingung soll gerade nicht stimmen.",
                    "table": orders_table("order_number", "client", "status"),
                    "note": "Helio hat offene und abgeschlossene Aufträge. Alpin ebenfalls.",
                    "cta": "AND ausprobieren",
                },
                {
                    "type": "predict",
                    "title": "AND: beide müssen stimmen",
                    "text": "Markiere Zeilen, die **Helio und offen** sind.",
                    "sql": "SELECT * FROM orders WHERE client = 'Helio' AND status = 'offen';",
                    "table": orders_table(),
                    "expected_ids": HELIO_OFFEN,
                    "id_field": "id",
                    "execute": True,
                    "concepts": ["AND"],
                    "feedback_ok": "Helio allein reicht nicht. Status muss zusätzlich offen sein — fertige Helio-Aufträge fallen weg.",
                    "feedback_bad": "`AND` braucht beides: Kunde Helio **und** Status offen. Helio + fertig fällt raus.",
                },
                {
                    "type": "predict",
                    "title": "OR: eine reicht",
                    "text": "Markiere Zeilen, die **Helio oder offen** sind (mindestens eins von beiden).",
                    "sql": "SELECT * FROM orders WHERE client = 'Helio' OR status = 'offen';",
                    "table": orders_table(),
                    "expected_ids": ids(lambda r: r["client"] == "Helio" or r["status"] == "offen"),
                    "id_field": "id",
                    "execute": True,
                    "concepts": ["AND"],
                    "feedback_ok": "OR ist größer als AND: jeder Helio-Auftrag **und** jeder offene Auftrag.",
                    "feedback_bad": "`OR` reicht eine Seite: jeder Helio-Auftrag oder jeder offene Auftrag — beides markieren.",
                },
                {
                    "type": "write",
                    "title": "Beide Bedingungen",
                    "prompt": "Zeige alle offenen Helio-Aufträge.",
                    "placeholder": "SELECT …",
                    "solution": "SELECT * FROM orders WHERE client = 'Helio' AND status = 'offen';",
                    "concepts": ["AND", "WHERE"],
                    "hints": [
                        "Kunde und Status müssen gleichzeitig passen. AND oder OR?",
                        "Die Kundenspalte heißt `client`, der Status `offen`.",
                    ],
                },
                {
                    "type": "write",
                    "title": "Mindestens eine",
                    "prompt": "Zeige Aufträge, die storniert **oder** abgeschlossen sind.",
                    "placeholder": "SELECT …",
                    "solution": "SELECT * FROM orders WHERE status = 'storniert' OR status = 'fertig';",
                    "concepts": ["AND"],
                    "hints": [
                        "Zwei Status-Werte, es reicht wenn einer stimmt.",
                        "Dieselbe Spalte zweimal vergleichen, verbunden mit OR.",
                    ],
                },
                {
                    "type": "apply",
                    "title": "AND und OR nicht verwechseln",
                    "prompt": "Finde offene Aufträge von Alpin. Nur die, die wirklich beides erfüllen.",
                    "placeholder": "SELECT …",
                    "solution": "SELECT * FROM orders WHERE client = 'Alpin' AND status = 'offen';",
                    "concepts": ["AND"],
                    "hints": [
                        "Wenn du OR nimmst, kommen auch Alpin-Aufträge mit anderem Status.",
                        "Beide Bedingungen: Kunde Alpin **und** Status offen.",
                    ],
                },
            ],
            "quiz": [
                Q("Was liefert WHERE NOT status = 'offen'?", [
                    "Alle Zeilen, deren Status nicht offen ist.",
                    "Nur die offenen Zeilen.",
                    "Gar keine Zeilen.",
                    "Nur Helio.",
                ], 0, "`NOT` dreht die Bedingung um. Oft schreibst du dasselbe als `status != 'offen'`."),
                Q("Wann nimmst du AND?", [
                    "Wenn mindestens eine Bedingung reichen soll.",
                    "Wenn **beide** Bedingungen wahr sein müssen.",
                    "Statt FROM.",
                    "Nur bei Zahlen.",
                ], 1, "AND = Schnittmenge. OR = Vereinigung."),
                Q("Warum ist OR „größer“ als AND?", [
                    "OR ist ein Fehler.",
                    "OR lässt Zeilen durch, die nur eine der Bedingungen erfüllen.",
                    "AND liefert immer mehr Zeilen.",
                    "OR ignoriert WHERE.",
                ], 1, "Offen **oder** Helio umfasst mehr als offen **und** Helio."),
                Q("Was ist der typische Anfängerfehler bei zwei Filtern?", [
                    "SELECT zu vergessen.",
                    "OR zu schreiben, obwohl beide Bedingungen nötig sind (oder umgekehrt).",
                    "Anführungszeichen bei Zahlen.",
                    "LIMIT 1 ist Pflicht.",
                ], 1, "Erst auf Deutsch sagen: müssen **beide** stimmen oder reicht **eine**?"),
            ],
        },
        {
            "id": "ch6",
            "chapter": 6,
            "title": "ORDER BY und LIMIT",
            "minutes": 10,
            "goal": "Du sortierst Ergebnisse und begrenzst, wie viele Zeilen du siehst.",
            "concepts": ["ORDER BY", "LIMIT"],
            "model": ["SELECT", "FROM", "WHERE", "ORDER BY", "LIMIT"],
            "steps": [
                {
                    "type": "explain",
                    "title": "Reihenfolge ist eine eigene Frage",
                    "text": "Ohne `ORDER BY` ist die Reihenfolge egal. Mit `ORDER BY` sagst du, wie sortiert wird.",
                    "sql": "SELECT order_number, client\nFROM orders\nORDER BY order_number DESC;",
                    "plain": "Zeige Auftragsnummer und Kunde, höchste Nummer zuerst.",
                    "parts": [
                        {"match": "SELECT order_number, client", "token": "SELECT", "question": "Was?", "answer": "Nummer und Kunde."},
                        {"match": "FROM orders", "token": "FROM", "question": "Woher?", "answer": "Aufträge."},
                        {
                            "match": "ORDER BY order_number DESC",
                            "token": "ORDER BY",
                            "question": "Sortierung?",
                            "answer": "`DESC` = absteigend (groß nach klein). `ASC` = aufsteigend (klein nach groß), das ist die Voreinstellung.",
                        },
                    ],
                    "concepts": ["ORDER BY"],
                },
                {
                    "type": "predict",
                    "title": "Wer liegt vorne?",
                    "text": "Bei `ORDER BY order_number DESC` — markiere **nur die erste Ergebniszeile** (höchste Nummer).",
                    "sql": "SELECT * FROM orders ORDER BY order_number DESC;",
                    "table": orders_table("id", "order_number", "client", "status"),
                    "expected_ids": [24],
                    "id_field": "id",
                    "single": True,
                    "execute": True,
                    "concepts": ["ORDER BY"],
                    "feedback_ok": "4734 ist die höchste Nummer — die kommt bei DESC zuerst.",
                    "feedback_bad": "`DESC` stellt die größte Nummer nach oben. Das ist Auftrag 4734 — weiter unten in der Liste.",
                },
                {
                    "type": "explain",
                    "title": "LIMIT schneidet ab",
                    "text": "`LIMIT 5` heißt: höchstens fünf Zeilen. Zusammen mit ORDER BY bekommst du „die fünf …sten“.",
                    "sql": "SELECT *\nFROM orders\nORDER BY created_at DESC\nLIMIT 5;",
                    "plain": "Die fünf neuesten Aufträge.",
                    "parts": [
                        {
                            "match": "ORDER BY created_at DESC",
                            "token": "ORDER BY",
                            "question": "Sortierung?",
                            "answer": "Neues Datum zuerst.",
                        },
                        {
                            "match": "LIMIT 5",
                            "token": "LIMIT",
                            "question": "Wie viele?",
                            "answer": "Nur fünf Zeilen — nach dem Sortieren.",
                        },
                    ],
                    "concepts": ["LIMIT", "ORDER BY"],
                },
                {
                    "type": "write",
                    "title": "Fünf neueste",
                    "prompt": "Zeige die fünf neuesten Aufträge.",
                    "placeholder": "SELECT …",
                    "solution": "SELECT * FROM orders ORDER BY created_at DESC LIMIT 5;",
                    "ordered": True,
                    "expect_limit": True,
                    "concepts": ["ORDER BY", "LIMIT"],
                    "hints": [
                        "Neueste zuerst sortieren, dann auf 5 begrenzen.",
                        "Sortierspalte ist `created_at`. DESC = neu zuerst.",
                    ],
                },
                {
                    "type": "apply",
                    "title": "Die Praxisfrage",
                    "prompt": "Zeige nur Auftragsnummer und Status der fünf neuesten Aufträge.",
                    "placeholder": "SELECT …",
                    "solution": "SELECT order_number, status FROM orders ORDER BY created_at DESC LIMIT 5;",
                    "strict_columns": True,
                    "ordered": True,
                    "expect_limit": True,
                    "concepts": ["SELECT", "ORDER BY", "LIMIT"],
                    "hints": [
                        "SELECT wählt die Spalten, ORDER BY die Reihenfolge, LIMIT die Anzahl.",
                        "Zwei Spalten: `order_number` und `status`.",
                    ],
                },
            ],
            "quiz": [
                Q("Was bedeutet ORDER BY created_at DESC?", [
                    "Älteste zuerst.",
                    "Neueste / größte Datumswerte zuerst.",
                    "Zufällige Reihenfolge.",
                    "Nur fünf Zeilen.",
                ], 1, "`DESC` = absteigend. Beim Datum: das jüngste zuerst."),
                Q("Was macht LIMIT 5?", [
                    "Filtert auf Status 5.",
                    "Liefert höchstens fünf Zeilen — nach dem Sortieren, wenn ORDER BY da ist.",
                    "Wählt fünf Spalten.",
                    "Löscht fünf Zeilen.",
                ], 1, "LIMIT schneidet das Ergebnis ab. Ohne ORDER BY sind „die fünf“ beliebig."),
                Q("Warum ORDER BY vor LIMIT schreiben (in der Query)?", [
                    "SQL verbietet die andere Reihenfolge.",
                    "Du willst erst sortieren und dann die obersten N nehmen.",
                    "LIMIT sortiert selbst.",
                    "FROM muss danach stehen.",
                ], 1, "Die fünf neuesten: erst Datum absteigend, dann LIMIT 5."),
                Q("Was ist ASC?", [
                    "Absteigend.",
                    "Aufsteigend (klein nach groß) — die Voreinstellung.",
                    "Ein Tabellenname.",
                    "Ein Filter.",
                ], 1, "Ohne Zusatz sortiert ORDER BY aufsteigend (ASC)."),
            ],
        },
        {
            "id": "ch7",
            "chapter": 7,
            "title": "NULL — fehlende Werte",
            "minutes": 10,
            "goal": "Du behandelst leere Zellen mit IS NULL / IS NOT NULL, nie mit = NULL.",
            "concepts": ["NULL", "WHERE"],
            "model": ["SELECT", "FROM", "WHERE"],
            "steps": [
                {
                    "type": "look",
                    "title": "Leer ist nicht 0",
                    "text": "**NULL** heißt: für dieses Feld gibt es keinen Wert. Nicht die Zahl 0, nicht der Text `offen`.\n\nVergleiche wie `= NULL` sind nie wahr. Stattdessen: `IS NULL` / `IS NOT NULL`.",
                    "table": orders_table("order_number", "client", "quantity"),
                    "note": "Manche Mengen und ein Kunde fehlen. In der Tabelle siehst du leere Zellen.",
                    "cta": "Weiter",
                },
                {
                    "type": "predict",
                    "title": "Welche Mengen fehlen?",
                    "text": "Markiere die Zeilen, für die `quantity IS NULL` wahr ist.",
                    "sql": "SELECT * FROM orders WHERE quantity IS NULL;",
                    "table": orders_table("id", "order_number", "client", "quantity"),
                    "expected_ids": QTY_NULL,
                    "id_field": "id",
                    "execute": True,
                    "concepts": ["NULL"],
                    "feedback_ok": "Nur die Zeilen ohne Menge. 0 wäre ein Wert — NULL ist keiner.",
                    "feedback_bad": "Leere `quantity`-Zellen markieren. Die Zahl 0 ist ein Wert, kein fehlender.",
                },
                {
                    "type": "write",
                    "title": "Gewicht unbekannt",
                    "prompt": "Zeige Bestandszeilen, bei denen das Gewicht fehlt.",
                    "placeholder": "SELECT …",
                    "solution": "SELECT * FROM stock WHERE weight IS NULL;",
                    "concepts": ["NULL"],
                    "hints": [
                        "Fehlend prüfst du mit IS NULL, nicht mit = NULL.",
                        "Tabelle `stock`, Spalte `weight`.",
                    ],
                },
                {
                    "type": "apply",
                    "title": "Auftrag ohne Kunde",
                    "prompt": "Finde Aufträge, denen kein Kunde zugeordnet ist.",
                    "placeholder": "SELECT …",
                    "solution": "SELECT * FROM orders WHERE client IS NULL;",
                    "concepts": ["NULL"],
                    "hints": [
                        "Kein Kunde = die Spalte `client` ist leer.",
                        "`IS NULL` auf `client` (oder `client_id`).",
                    ],
                },
            ],
            "quiz": [
                Q("Was bedeutet NULL?", [
                    "Die Zahl 0.",
                    "Kein Wert vorhanden.",
                    "Der Text 'null'.",
                    "Die Zeile ist gelöscht.",
                ], 1, "NULL = unbekannt / nicht gesetzt. 0 ist ein echter Wert."),
                Q("Wie findest du Zeilen ohne Menge?", [
                    "WHERE quantity = NULL",
                    "WHERE quantity IS NULL",
                    "WHERE quantity = 0",
                    "WHERE quantity = ''",
                ], 1, "`= NULL` findet nichts. Immer `IS NULL`."),
                Q("Warum ist quantity = NULL falsch?", [
                    "Postgres kennt kein NULL.",
                    "Der Vergleich mit NULL ist unbekannt, also nicht wahr.",
                    "Man darf quantity nicht filtern.",
                    "NULL geht nur in SELECT.",
                ], 1, "SQL: alles, was NULL berührt, wird unbekannt. Filter brauchen IS NULL."),
                Q("Was liefert quantity IS NOT NULL?", [
                    "Nur die Zahl 0.",
                    "Alle Zeilen, in denen eine Menge steht (inkl. 0).",
                    "Gar keine Zeilen.",
                    "Nur Helio.",
                ], 1, "`IS NOT NULL` = Wert vorhanden. 0 bleibt, leere Zellen nicht."),
            ],
        },
        {
            "id": "ch8",
            "chapter": 8,
            "title": "Zählen und gruppieren",
            "minutes": 12,
            "goal": "Du zählst Zeilen mit COUNT und fasst mit GROUP BY nach Kunde oder Status zusammen.",
            "concepts": ["GROUP BY"],
            "model": ["SELECT", "FROM", "WHERE", "GROUP BY"],
            "steps": [
                {
                    "type": "explain",
                    "title": "Eine Zahl statt einer Liste",
                    "text": "`COUNT(*)` zählt Zeilen. Ohne GROUP BY kommt **eine** Zahl für die ganze (gefilterte) Tabelle.",
                    "sql": "SELECT COUNT(*)\nFROM orders\nWHERE status = 'offen';",
                    "plain": "Wie viele offene Aufträge gibt es?",
                    "parts": [
                        {"match": "SELECT COUNT(*)", "token": "SELECT", "question": "Was?", "answer": "Nicht die Zeilen selbst, sondern ihre Anzahl."},
                        {"match": "FROM orders", "token": "FROM", "question": "Woher?", "answer": "Aufträge."},
                        {"match": "WHERE status = 'offen'", "token": "WHERE", "question": "Welche?", "answer": "Nur offene — dann zählen."},
                    ],
                    "concepts": ["GROUP BY"],
                },
                {
                    "type": "demo",
                    "title": "Zählen ausführen",
                    "text": "Du bekommst eine Zelle mit der Anzahl, keine Auftragsliste.",
                    "sql": "SELECT COUNT(*) FROM orders WHERE status = 'offen';",
                    "table": orders_table(),
                    "concepts": ["GROUP BY"],
                },
                {
                    "type": "explain",
                    "title": "Pro Gruppe eine Zahl",
                    "text": "`GROUP BY client` macht **eine Ergebniszeile je Kunde**. `COUNT(*)` zählt dann innerhalb der Gruppe.\n\nWas in SELECT steht, muss aggregiert sein (`COUNT`, `SUM`, …) oder in GROUP BY vorkommen.",
                    "sql": "SELECT client, COUNT(*)\nFROM orders\nWHERE client IS NOT NULL\nGROUP BY client;",
                    "plain": "Wie viele Aufträge hat jeder Kunde?",
                    "parts": [
                        {"match": "SELECT client, COUNT(*)", "token": "SELECT", "question": "Was?", "answer": "Kundenname und die Anzahl seiner Aufträge."},
                        {"match": "WHERE client IS NOT NULL", "token": "WHERE", "question": "Welche?", "answer": "Aufträge ohne Kunde lassen wir weg — sonst gäbe es eine NULL-Gruppe."},
                        {"match": "GROUP BY client", "token": "GROUP BY", "question": "Nach was?", "answer": "Eine Gruppe je Kundenname."},
                    ],
                    "concepts": ["GROUP BY"],
                },
                {
                    "type": "write",
                    "title": "Offene zählen",
                    "prompt": "Wie viele offene Aufträge gibt es? Nur die Anzahl.",
                    "placeholder": "SELECT …",
                    "solution": "SELECT COUNT(*) FROM orders WHERE status = 'offen';",
                    "concepts": ["GROUP BY"],
                    "hints": [
                        "Du willst keine Liste, sondern eine Zahl: COUNT(*).",
                        "Filter vorher mit WHERE auf status = 'offen'.",
                    ],
                },
                {
                    "type": "apply",
                    "title": "Pro Status zählen",
                    "prompt": "Zeig je Status, wie viele Aufträge es gibt.",
                    "placeholder": "SELECT …",
                    "solution": "SELECT status, COUNT(*) FROM orders GROUP BY status;",
                    "concepts": ["GROUP BY"],
                    "hints": [
                        "Eine Zeile pro Status: GROUP BY status, dazu COUNT(*).",
                        "SELECT status und die Anzahl.",
                    ],
                },
            ],
            "quiz": [
                Q("Was liefert COUNT(*) ohne GROUP BY?", [
                    "Alle Zeilen der Tabelle.",
                    "Eine Zahl: wie viele Zeilen (nach WHERE) übrig sind.",
                    "Nur die erste Zeile.",
                    "Die Summe der Mengen.",
                ], 1, "`COUNT(*)` aggregiert. Ohne GROUP BY eine einzige Ergebniszeile."),
                Q("Wozu ist GROUP BY da?", [
                    "Zum Sortieren.",
                    "Gleichartige Zeilen zu Gruppen zusammenfassen, dann zählen/summieren.",
                    "Zum Joinen.",
                    "Es ersetzt WHERE.",
                ], 1, "„Pro Kunde“, „pro Status“ = GROUP BY."),
                Q("Warum steht client sowohl in SELECT als auch in GROUP BY?", [
                    "Zufall.",
                    "Was du nicht aggregierst, musst du gruppieren — sonst mischt SQL die Gruppen.",
                    "GROUP BY braucht immer id.",
                    "SELECT darf dann kein COUNT enthalten.",
                ], 1, "Faustregel: SELECT-Spalten ohne COUNT/SUM gehören in GROUP BY."),
                Q("Was ist SUM(quantity)?", [
                    "Die Anzahl der Zeilen.",
                    "Die Summe der Mengen — NULL-Mengen zählen nicht mit.",
                    "Der Durchschnitt.",
                    "Die größte Menge.",
                ], 1, "`SUM` addiert Zahlen. `COUNT` zählt Zeilen. NULL wird bei SUM ignoriert."),
            ],
        },
        {
            "id": "ch9",
            "chapter": 9,
            "title": "INNER JOIN",
            "minutes": 14,
            "goal": "Du verbindest Auftrag und Kunde über client_id und verstehst: ohne Treffer fliegt die Zeile raus.",
            "concepts": ["JOIN"],
            "model": ["SELECT", "FROM", "JOIN", "ON", "WHERE"],
            "steps": [
                {
                    "type": "look",
                    "title": "Zwei Tabellen, eine Frage",
                    "text": "In `orders` steht der Kundenname zur Übung noch einmal. Die Stammdaten liegen in `clients` (Name, Land).\n\nZusammengehören tun sie über **`orders.client_id = clients.id`**.",
                    "tables": [
                        clients_table(),
                        orders_table("id", "order_number", "client_id", "client"),
                    ],
                    "note": "Westfeld hat in clients eine Zeile — aber keinen Auftrag. Beim INNER JOIN siehst du Westfeld deshalb nicht.",
                    "cta": "JOIN ansehen",
                },
                {
                    "type": "explain",
                    "title": "INNER JOIN behält nur Paare",
                    "text": "Ein **INNER JOIN** (kurz auch `JOIN`) behält Zeilen nur, wenn **beide** Tabellen zusammenpassen.",
                    "sql": "SELECT o.order_number, c.name, c.country\nFROM orders o\nJOIN clients c\n  ON c.id = o.client_id;",
                    "plain": "Auftragsnummer plus Kundenname und Land — aber nur wenn ein Kunde hängt.",
                    "parts": [
                        {"match": "FROM orders o", "token": "FROM", "question": "Woher zuerst?", "answer": "Aufträge. `o` ist ein Kurzname (Alias), damit wir o.order_number schreiben können."},
                        {"match": "JOIN clients c", "token": "JOIN", "question": "Welche Infos extra?", "answer": "Die Kundentabelle. JOIN ohne Wort davor ist INNER JOIN."},
                        {"match": "ON c.id = o.client_id", "token": "ON", "question": "Wie gehören sie zusammen?", "answer": "Die id des Kunden ist derselbe Wert wie client_id am Auftrag."},
                    ],
                    "concepts": ["JOIN"],
                },
                {
                    "type": "predict",
                    "title": "Welche Aufträge überleben den INNER JOIN?",
                    "text": "Markiere die Aufträge, die nach `JOIN clients ON clients.id = orders.client_id` noch da sind.\n\nAuftrag **4730** hat eine leere Kundenspalte — weiter unten in der Tabelle.",
                    "sql": "SELECT * FROM orders JOIN clients ON clients.id = orders.client_id;",
                    "table": orders_table("id", "order_number", "client", "status"),
                    "expected_ids": HAS_CLIENT,
                    "id_field": "id",
                    "execute": True,
                    "visualize": "inner",
                    "concepts": ["JOIN"],
                    "feedback_ok": "Auftrag 4730 hat keine client_id — INNER JOIN lässt ihn weg. Westfeld erscheint hier sowieso nicht, der steht nur in clients.",
                    "feedback_bad": "INNER JOIN behält nur Aufträge mit Kunden. 4730 hat eine leere Kundenspalte (weiter unten) — den nicht markieren.",
                },
                {
                    "type": "build",
                    "title": "Ersten JOIN bauen",
                    "prompt": "Verbinde Aufträge und Kunden. Gib Auftragsnummer und Kundenname aus.",
                    "pieces": ["SELECT", "o.order_number", ",", "c.name", "FROM", "orders", "o", "JOIN", "clients", "c", "ON", "c.id", "=", "o.client_id"],
                    "distractors": ["WHERE", "LEFT"],
                    "solution": "SELECT o.order_number, c.name FROM orders o JOIN clients c ON c.id = o.client_id;",
                    "strict_columns": True,
                    "concepts": ["JOIN"],
                    "hints": [
                        "FROM die erste Tabelle, JOIN die zweite, ON die Schlüssel.",
                        "Auftrag `client_id` zeigt auf Kunde `id`.",
                    ],
                },
                {
                    "type": "write",
                    "title": "Nummer und Land",
                    "prompt": "Zeig zu jedem Auftrag mit Kunde die Auftragsnummer und das Land des Kunden.",
                    "placeholder": "SELECT …",
                    "solution": "SELECT o.order_number, c.country FROM orders o JOIN clients c ON c.id = o.client_id;",
                    "strict_columns": True,
                    "concepts": ["JOIN"],
                    "hints": [
                        "Land steht in clients, nicht in orders.",
                        "ON c.id = o.client_id.",
                    ],
                },
                {
                    "type": "apply",
                    "title": "Nur österreichische Kunden",
                    "prompt": "Zeig Auftragsnummer und Kundenname aller Aufträge, deren Kunde in AT sitzt.",
                    "placeholder": "SELECT …",
                    "solution": "SELECT o.order_number, c.name FROM orders o JOIN clients c ON c.id = o.client_id WHERE c.country = 'AT';",
                    "strict_columns": True,
                    "concepts": ["JOIN", "WHERE"],
                    "hints": [
                        "Erst joinen, dann filtern: WHERE auf c.country.",
                        "AT steht in der Kundentabelle.",
                    ],
                },
            ],
            "quiz": [
                Q("Was bleibt bei einem INNER JOIN Auftrag → Kunde übrig?", [
                    "Alle Aufträge, fehlender Kunde als NULL.",
                    "Nur Aufträge, die einen passenden Kunden haben.",
                    "Alle Kunden, auch ohne Auftrag.",
                    "Immer genau eine Zeile.",
                ], 1, "INNER JOIN = nur Paare. Auftrag ohne client_id fliegt raus."),
                Q("Wofür ist ON da?", [
                    "Zum Sortieren.",
                    "Es sagt, über welche Spalten die Tabellen zusammengehören.",
                    "Es filtert wie WHERE auf den Status.",
                    "Es wählt Spalten.",
                ], 1, "`ON c.id = o.client_id` ist die Naht. WHERE filtert danach fachlich."),
                Q("Was ist ein Tabellen-Alias wie o oder c?", [
                    "Ein zweiter Datenbankname.",
                    "Ein Kurzname in dieser Query, damit Spalten eindeutig sind.",
                    "Ein Statuscode.",
                    "Pflicht in Postgres, sonst läuft nichts.",
                ], 1, "`FROM orders o` — danach `o.order_number`. Pflicht wird es, sobald zwei Tabellen dieselbe Spalte `id` haben."),
                Q("JOIN ohne Zusatzwort ist …", [
                    "LEFT JOIN",
                    "INNER JOIN",
                    "FULL JOIN",
                    "kein JOIN",
                ], 1, "`JOIN` allein = INNER JOIN."),
            ],
        },
        {
            "id": "ch10",
            "chapter": 10,
            "title": "LEFT JOIN und Lücken",
            "minutes": 12,
            "goal": "Du behältst alle Zeilen links und liest NULL rechts als „kein Treffer“.",
            "concepts": ["JOIN", "NULL"],
            "model": ["SELECT", "FROM", "JOIN", "ON", "WHERE"],
            "steps": [
                {
                    "type": "explain",
                    "title": "Links darf niemand verloren gehen",
                    "text": "**LEFT JOIN** behält **alle Zeilen der linken Tabelle**. Fehlt rechts ein Treffer, stehen dort **NULL**.\n\nFaustregel: Was nicht verschwinden darf, gehört nach links.",
                    "sql": "SELECT o.order_number, c.name\nFROM orders o\nLEFT JOIN clients c\n  ON c.id = o.client_id;",
                    "plain": "Alle Aufträge. Wo kein Kunde hängt, ist der Name leer.",
                    "parts": [
                        {"match": "FROM orders o", "token": "FROM", "question": "Was bleibt?", "answer": "Alle Aufträge — die stehen links."},
                        {"match": "LEFT JOIN clients c", "token": "LEFT JOIN", "question": "Extra?", "answer": "Kundeninfos dazu, ohne Aufträge zu verlieren."},
                        {"match": "ON c.id = o.client_id", "token": "ON", "question": "Naht?", "answer": "Wie beim INNER JOIN. Der Unterschied ist nur INNER vs LEFT."},
                    ],
                    "concepts": ["JOIN"],
                },
                {
                    "type": "predict",
                    "title": "Welche Aufträge bleiben beim LEFT JOIN?",
                    "text": "Markiere die Aufträge, die `FROM orders LEFT JOIN clients` noch enthält.\n\nAuftrag **4730** hat eine leere Kundenspalte — weiter unten in der Tabelle.",
                    "sql": "SELECT * FROM orders o LEFT JOIN clients c ON c.id = o.client_id;",
                    "table": orders_table("id", "order_number", "client", "status"),
                    "expected_ids": ids(lambda r: True),
                    "id_field": "id",
                    "execute": True,
                    "concepts": ["JOIN"],
                    "feedback_ok": "Alle Aufträge — inklusive 4730 ohne Kunde. Genau das ist LEFT JOIN.",
                    "feedback_bad": "LEFT JOIN behält jede Zeile der linken Tabelle. Markiere alle Aufträge, auch 4730 mit leerer Kundenspalte (weiter unten).",
                },
                {
                    "type": "write",
                    "title": "Auftragsliste mit möglicher Lücke",
                    "prompt": "Zeig Auftragsnummer und Kundenname aller Aufträge. Aufträge ohne Kunde sollen bleiben.",
                    "placeholder": "SELECT …",
                    "solution": "SELECT o.order_number, c.name FROM orders o LEFT JOIN clients c ON c.id = o.client_id;",
                    "strict_columns": True,
                    "concepts": ["JOIN"],
                    "hints": [
                        "INNER JOIN würde 4730 verlieren. Also LEFT JOIN, Auftrag links.",
                        "ON bleibt c.id = o.client_id.",
                    ],
                },
                {
                    "type": "apply",
                    "title": "Kunde ohne Auftrag",
                    "prompt": "Welche Kunden haben **keinen** Auftrag? Zeige nur den Kundennamen.",
                    "placeholder": "SELECT …",
                    "solution": "SELECT c.name FROM clients c LEFT JOIN orders o ON o.client_id = c.id WHERE o.id IS NULL;",
                    "strict_columns": True,
                    "concepts": ["JOIN", "NULL"],
                    "hints": [
                        "Kunde muss links bleiben: FROM clients LEFT JOIN orders.",
                        "Kein Treffer rechts: `o.id IS NULL`. Westfeld ist genau dieser Fall.",
                    ],
                },
            ],
            "quiz": [
                Q("Was bedeutet NULL in der Kundenspalte nach einem LEFT JOIN Auftrag → Kunde?", [
                    "Die Menge ist 0.",
                    "Links gab es keine passende Zeile rechts — der Auftrag hat keinen Kunden.",
                    "Der JOIN ist fehlgeschlagen und muss wiederholt werden.",
                    "Der Kunde heißt NULL.",
                ], 1, "Die linke Zeile bleibt. Rechts war kein Treffer."),
                Q("Du willst alle Aufträge, auch ohne Kunde. Welcher JOIN?", [
                    "INNER JOIN",
                    "LEFT JOIN, Auftrag links",
                    "Nur WHERE ohne JOIN",
                    "GROUP BY",
                ], 1, "Was nicht verloren gehen darf, gehört nach links."),
                Q("Wie findest du Kunden ohne Auftrag?", [
                    "INNER JOIN und WHERE client = 'Westfeld'",
                    "LEFT JOIN Kunde → Auftrag, dann WHERE die Auftrags-id IS NULL",
                    "DELETE FROM orders",
                    "COUNT(*) ohne GROUP BY",
                ], 1, "Anti-Join: links die Seite, die bleiben soll, rechts IS NULL."),
                Q("Warum schreiben wir selten RIGHT JOIN?", [
                    "Postgres kennt kein RIGHT JOIN.",
                    "RIGHT JOIN liefert immer 0 Zeilen.",
                    "Wir legen die führende Tabelle nach links und schreiben LEFT JOIN.",
                    "RIGHT JOIN ignoriert ON.",
                ], 2, "RIGHT JOIN ist LEFT JOIN mit vertauschten Seiten. Üblich: die wichtige Tabelle links."),
            ],
        },
        {
            "id": "challenge-1",
            "chapter": 11,
            "title": "Challenge: Offene Helio-Aufträge",
            "minutes": 8,
            "goal": "Du übersetzt eine Lagerfrage in SQL — ohne dass die App die Befehle nennt.",
            "concepts": ["SELECT", "WHERE", "AND", "ORDER BY"],
            "challenge": True,
            "model": ["SELECT", "FROM", "WHERE", "ORDER BY"],
            "steps": [
                {
                    "type": "look",
                    "title": "Keine Syntax-Liste",
                    "text": "Das Lager will etwas wissen. Du entscheidest selbst, **welche Spalten**, **welche Zeilen** und **welche Reihenfolge** du brauchst.\n\nDie Tabelle kennst du.",
                    "table": orders_table("order_number", "client", "status", "created_at"),
                    "cta": "Aufgabe öffnen",
                },
                {
                    "type": "challenge",
                    "title": "Lagerfrage",
                    "prompt": "Welche offenen Aufträge gehören aktuell zu Helio? Zeige nur Auftragsnummer und Status, die neuesten zuerst.",
                    "placeholder": "Übersetze die Frage in SQL…",
                    "solution": "SELECT order_number, status FROM orders WHERE client = 'Helio' AND status = 'offen' ORDER BY created_at DESC;",
                    "strict_columns": True,
                    "ordered": True,
                    "concepts": ["SELECT", "WHERE", "AND", "ORDER BY"],
                    "hints": [
                        "Welche Zeilen? (Kunde und Status.) Welche Spalten? Wie sortieren?",
                        "Zwei Bedingungen gehören mit AND zusammen. Sortierung über created_at.",
                    ],
                },
            ],
            "quiz": [
                Q("Welcher Denkschritt war der entscheidende — nicht die genaue Schreibweise?", [
                    "Fachfrage zerlegen: welche Daten, welcher Filter, welche Reihenfolge.",
                    "Die Musterlösung auswendig lernen.",
                    "Möglichst viele Tabellen joinen.",
                    "Immer SELECT * verwenden.",
                ], 0, "SQL-Wörter sind Werkzeug. Zuerst die Frage verstehen: Was? Welche? In welcher Ordnung?"),
                Q("Warum AND und nicht OR bei „Helio und offen“?", [
                    "OR ist in Postgres verboten.",
                    "Beide Bedingungen müssen gleichzeitig stimmen.",
                    "AND sortiert automatisch.",
                    "OR würde weniger Zeilen liefern.",
                ], 1, "OR würde jedes offene **oder** jedes Helio nehmen — zu weit."),
                Q("Warum ORDER BY created_at DESC?", [
                    "Damit nur fünf Zeilen kommen.",
                    "Die neuesten zuerst — „aktuell“ in der Lagerfrage.",
                    "DESC filtert Status.",
                    "Ohne ORDER BY kennt SQL Helio nicht.",
                ], 1, "Aktuell / neueste = absteigendes Datum."),
                Q("Warum nicht SELECT *?", [
                    "Stern ist syntaktisch falsch.",
                    "Die Frage wollte nur Nummer und Status — SELECT wählt die Spalten.",
                    "SELECT * ignoriert WHERE.",
                    "Stern funktioniert nur auf stock.",
                ], 1, "Die Fachfrage nennt die Felder. Nicht alles ausschütten."),
            ],
        },
        {
            "id": "challenge-2",
            "chapter": 12,
            "title": "Challenge: Auftrag plus Land",
            "minutes": 8,
            "goal": "Du verbindest zwei Tabellen für eine echte Lagerfrage und lässt Lücken sichtbar.",
            "concepts": ["JOIN", "SELECT", "WHERE"],
            "challenge": True,
            "model": ["SELECT", "FROM", "JOIN", "ON", "WHERE", "ORDER BY"],
            "steps": [
                {
                    "type": "look",
                    "title": "Stammdaten extra",
                    "text": "Das Land steht nicht in `orders`, sondern in `clients`. Ohne JOIN siehst du es nicht.\n\nEin Auftrag hat keinen Kunden — der soll in der Liste **bleiben**, Land dann leer.",
                    "table": clients_table(),
                    "cta": "Aufgabe öffnen",
                },
                {
                    "type": "challenge",
                    "title": "Lagerfrage",
                    "prompt": "Liste offene Aufträge: Nummer, Kundenname und Land. Aufträge ohne Kunde sollen stehen bleiben. Neueste zuerst.",
                    "placeholder": "Übersetze die Frage in SQL…",
                    "solution": (
                        "SELECT o.order_number, c.name, c.country "
                        "FROM orders o LEFT JOIN clients c ON c.id = o.client_id "
                        "WHERE o.status = 'offen' ORDER BY o.created_at DESC;"
                    ),
                    "strict_columns": True,
                    "ordered": True,
                    "concepts": ["JOIN", "WHERE", "ORDER BY"],
                    "hints": [
                        "Land sitzt in clients. Auftrag darf nicht verschwinden → welche JOIN-Art?",
                        "Filter auf offenen Status **nach** dem Join, Sortierung nach created_at.",
                    ],
                },
            ],
            "quiz": [
                Q("Warum LEFT JOIN und nicht INNER JOIN?", [
                    "INNER JOIN kann kein Land.",
                    "Ein offener Auftrag hat keinen Kunden — INNER JOIN würde ihn verlieren.",
                    "LEFT JOIN ist in Postgres schneller.",
                    "ON funktioniert nur mit LEFT.",
                ], 1, "Die Frage sagt ausdrücklich: ohne Kunde stehen bleiben."),
                Q("Wo filterst du den Status?", [
                    "In ON statt in WHERE.",
                    "In WHERE auf die Auftragstabelle (o.status).",
                    "GROUP BY status.",
                    "Im Kundennamen.",
                ], 1, "ON ist die Naht. Der fachliche Filter bleibt WHERE."),
                Q("Warum c.name und nicht o.client in der Ausgabe?", [
                    "o.client gibt es nicht.",
                    "Die Aufgabe will den Namen aus der Kundentabelle — und NULL, wenn der Join nicht greift.",
                    "c.name ist immer 'Helio'.",
                    "SQL erlaubt o.client nach einem JOIN nicht.",
                ], 1, "Nach LEFT JOIN ist c.name die saubere Stammdaten-Spalte. Fehlt der Kunde, ist sie NULL."),
                Q("Was siehst du für Auftrag 4730?", [
                    "Die Zeile fehlt.",
                    "Nummer, Name und Land NULL.",
                    "Einen Fehler.",
                    "Westfeld als Kunden.",
                ], 1, "LEFT JOIN: Auftrag bleibt, Kundenfelder leer."),
            ],
        },
    ],
}


def lessons():
    return ACADEMY["lessons"]


def lesson_by_id(lesson_id: str):
    for lesson in ACADEMY["lessons"]:
        if lesson["id"] == lesson_id:
            return lesson
    return None


def _finalize_academy():
    from lessons.academy_more import GLOSSARY, extra_lessons, flashcards

    by_id = {lesson["id"]: lesson for lesson in ACADEMY["lessons"]}
    for lesson in extra_lessons():
        by_id[lesson["id"]] = lesson
    missing = [lid for lid in PATH_IDS if lid not in by_id]
    if missing:
        raise RuntimeError("Unbekannte Kapitel in PATH_IDS: " + ", ".join(missing))
    ACADEMY["lessons"] = [by_id[lid] for lid in PATH_IDS]
    for index, lesson in enumerate(ACADEMY["lessons"]):
        lesson["chapter"] = index
    ACADEMY["glossary"] = GLOSSARY
    ACADEMY["concepts"] = CONCEPTS
    ACADEMY["flashcards"] = flashcards()


_finalize_academy()
