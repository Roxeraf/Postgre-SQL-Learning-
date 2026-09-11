"""Additional academy chapters: aliases, keys, HAVING, DML, transactions, Postgres."""

from lessons.academy_data import (
    ORDERS,
    Q,
    clients_table,
    orders_table,
    table,
)

ORDER_ITEMS = [
    {"id": 1, "order_id": 1, "sku": "Palette A", "qty": 2},
    {"id": 2, "order_id": 1, "sku": "Karton C", "qty": 4},
    {"id": 3, "order_id": 2, "sku": "Palette B", "qty": 1},
    {"id": 4, "order_id": 3, "sku": "Palette A", "qty": 5},
    {"id": 5, "order_id": 3, "sku": "Folie F", "qty": 2},
    {"id": 6, "order_id": 4, "sku": "Karton C", "qty": 3},
    {"id": 7, "order_id": 5, "sku": "Palette D", "qty": 1},
    {"id": 8, "order_id": 6, "sku": "Palette A", "qty": 1},
    {"id": 9, "order_id": 6, "sku": "Palette B", "qty": 1},
    {"id": 10, "order_id": 7, "sku": "Karton E", "qty": 2},
    {"id": 11, "order_id": 8, "sku": "Palette A", "qty": 10},
    {"id": 12, "order_id": 9, "sku": "Karton C", "qty": 6},
    {"id": 13, "order_id": 10, "sku": "Palette D", "qty": 2},
    {"id": 14, "order_id": 11, "sku": "Folie F", "qty": 1},
    {"id": 15, "order_id": 12, "sku": "Karton C", "qty": 2},
    {"id": 16, "order_id": 13, "sku": "Palette B", "qty": 1},
    {"id": 17, "order_id": 14, "sku": "Palette A", "qty": 8},
    {"id": 18, "order_id": 14, "sku": "Karton C", "qty": 3},
    {"id": 19, "order_id": 15, "sku": "Folie F", "qty": 4},
    {"id": 20, "order_id": 16, "sku": "Palette G", "qty": 1},
    {"id": 21, "order_id": 17, "sku": "Palette A", "qty": 2},
    {"id": 22, "order_id": 18, "sku": "Karton C", "qty": 1},
    {"id": 23, "order_id": 19, "sku": "Palette A", "qty": 20},
    {"id": 24, "order_id": 21, "sku": "Folie F", "qty": 3},
    {"id": 25, "order_id": 22, "sku": "Palette D", "qty": 1},
    {"id": 26, "order_id": 23, "sku": "Karton C", "qty": 1},
    {"id": 27, "order_id": 24, "sku": "Palette A", "qty": 1},
    {"id": 28, "order_id": 24, "sku": "Folie F", "qty": 2},
]

ORDERS_WITH_ITEMS = sorted({r["order_id"] for r in ORDER_ITEMS})
ORDERS_WITHOUT_ITEMS = [r["id"] for r in ORDERS if r["id"] not in ORDERS_WITH_ITEMS]


def items_table(*columns):
    cols = list(columns) if columns else ["id", "order_id", "sku", "qty"]
    return table("order_items", "Positionen", ORDER_ITEMS, cols)


GLOSSARY = [
    {
        "id": "TABLE",
        "label": "Tabelle",
        "lesson_id": "ch0",
        "sql": "SELECT * FROM orders;",
        "text": "Eine Tabelle ist eine Relation: Zeilen (Datensätze) und Spalten (Attribute). "
        "Jede Zelle hält einen Wert — oder NULL, wenn nichts gesetzt ist.",
    },
    {
        "id": "SELECT",
        "label": "SELECT",
        "lesson_id": "ch2",
        "sql": "SELECT order_number, status FROM orders;",
        "text": "SELECT bestimmt, welche Informationen (Spalten) im Ergebnis erscheinen. "
        "Der Stern * bedeutet alle Spalten. SELECT filtert keine Zeilen.",
    },
    {
        "id": "FROM",
        "label": "FROM",
        "lesson_id": "ch1",
        "sql": "SELECT * FROM orders;",
        "text": "FROM sagt, aus welcher Tabelle die Daten kommen. Ohne FROM weiß SQL nicht, woher.",
    },
    {
        "id": "WHERE",
        "label": "WHERE",
        "lesson_id": "ch3",
        "sql": "SELECT * FROM orders WHERE status = 'offen';",
        "text": "WHERE prüft jede Zeile: Ist die Bedingung wahr? Nur dann bleibt die Zeile. "
        "Textwerte stehen in einfachen Anführungszeichen.",
    },
    {
        "id": "NULL",
        "label": "NULL",
        "lesson_id": "ch7",
        "sql": "SELECT * FROM orders WHERE quantity IS NULL;",
        "text": "NULL heißt: kein Wert. Nicht 0, nicht leerer Text. Vergleiche mit = NULL sind nie wahr. "
        "Suche mit IS NULL / IS NOT NULL.",
    },
    {
        "id": "DISTINCT",
        "label": "DISTINCT",
        "lesson_id": "ch-alias",
        "sql": "SELECT DISTINCT country FROM clients;",
        "text": "DISTINCT entfernt doppelte Ergebniszeilen. Nützlich, wenn du Wertelisten willst, nicht jede Zeile.",
    },
    {
        "id": "AS",
        "label": "Alias (AS)",
        "lesson_id": "ch-alias",
        "sql": "SELECT order_number AS nummer FROM orders;",
        "text": "AS gibt einer Spalte oder Tabelle in dieser Query einen Kurznamen. "
        "Tabellen-Aliase (o, c) machen JOINs lesbar.",
    },
    {
        "id": "PK",
        "label": "Primary Key",
        "lesson_id": "ch-keys",
        "sql": "SELECT id, name FROM clients;",
        "text": "Der Primary Key identifiziert eine Zeile eindeutig — hier meist id. "
        "Zwei Zeilen dürfen denselben Namen haben, nie dieselbe id.",
    },
    {
        "id": "FK",
        "label": "Foreign Key",
        "lesson_id": "ch-keys",
        "sql": "SELECT order_number, client_id FROM orders;",
        "text": "Ein Foreign Key zeigt auf den Primary Key einer anderen Tabelle. "
        "orders.client_id verweist auf clients.id. So gehören Zeilen zusammen, ohne Daten zu kopieren.",
    },
    {
        "id": "JOIN",
        "label": "INNER JOIN",
        "lesson_id": "ch9",
        "sql": "SELECT o.order_number, c.name FROM orders o JOIN clients c ON c.id = o.client_id;",
        "text": "INNER JOIN (kurz JOIN) behält nur Zeilen, die in beiden Tabellen zusammenpassen. "
        "ON sagt, über welche Spalten sie zusammengehören.",
    },
    {
        "id": "LEFT JOIN",
        "label": "LEFT JOIN",
        "lesson_id": "ch10",
        "sql": "SELECT o.order_number, c.name FROM orders o LEFT JOIN clients c ON c.id = o.client_id;",
        "text": "LEFT JOIN behält alle Zeilen der linken Tabelle. Fehlt rechts ein Treffer, stehen dort NULL. "
        "Was nicht verschwinden darf, gehört nach links.",
    },
    {
        "id": "GROUP BY",
        "label": "GROUP BY",
        "lesson_id": "ch8",
        "sql": "SELECT status, COUNT(*) FROM orders GROUP BY status;",
        "text": "GROUP BY fasst gleichartige Zeilen zu Gruppen zusammen. "
        "COUNT/SUM/AVG rechnen dann pro Gruppe. Was in SELECT nicht aggregiert ist, muss gruppiert sein.",
    },
    {
        "id": "HAVING",
        "label": "HAVING",
        "lesson_id": "ch-having",
        "sql": "SELECT client, COUNT(*) FROM orders GROUP BY client HAVING COUNT(*) > 4;",
        "text": "WHERE filtert Zeilen vor dem Gruppieren. HAVING filtert Gruppen danach — "
        "zum Beispiel „nur Kunden mit mehr als vier Aufträgen“.",
    },
    {
        "id": "INSERT",
        "label": "INSERT",
        "lesson_id": "ch-dml",
        "sql": "INSERT INTO stock (id, item, quantity, weight) VALUES (8, 'Karton H', 4, 18);",
        "text": "INSERT fügt neue Zeilen ein. Du nennst Tabelle, Spalten und Werte. "
        "Danach ist die Zeile Teil der Tabelle — bis du sie änderst oder löschst.",
    },
    {
        "id": "UPDATE",
        "label": "UPDATE",
        "lesson_id": "ch-dml",
        "sql": "UPDATE orders SET status = 'fertig' WHERE order_number = 4714;",
        "text": "UPDATE ändert vorhandene Zeilen. SET setzt neue Werte. "
        "Ohne WHERE ändert SQL jede Zeile — deshalb gehört der Filter dazu.",
    },
    {
        "id": "DELETE",
        "label": "DELETE",
        "lesson_id": "ch-dml",
        "sql": "DELETE FROM stock WHERE id = 7;",
        "text": "DELETE entfernt Zeilen. Auch hier: WHERE ist Pflicht, sonst ist die Tabelle leer.",
    },
    {
        "id": "TX",
        "label": "Transaktion",
        "lesson_id": "ch-tx",
        "sql": "BEGIN;\nUPDATE orders SET status = 'fertig' WHERE id = 1;\nROLLBACK;",
        "text": "BEGIN … COMMIT macht mehrere Änderungen zu einer Einheit. "
        "ROLLBACK verwirft alles seit BEGIN. Entweder alles gilt — oder nichts.",
    },
    {
        "id": "SCHEMA",
        "label": "Schema",
        "lesson_id": "ch-pg",
        "sql": "SELECT * FROM orders;",
        "text": "PostgreSQL schichtet: Instanz → Datenbank → Schema → Tabelle. "
        "Diese App arbeitet im Schema learn. Der Suchpfad (search_path) sagt, wo Tabellennamen ohne Schema-Präfix gesucht werden.",
    },
    {
        "id": "INDEX",
        "label": "Index",
        "lesson_id": "ch-pg",
        "sql": "EXPLAIN SELECT * FROM orders WHERE status = 'offen';",
        "text": "Ein Index ist wie ein Stichwortregister: Postgres findet passende Zeilen, ohne die ganze Tabelle zu lesen. "
        "EXPLAIN zeigt den Plan — noch kein Tuning, nur die Idee.",
    },
    {
        "id": "SUM",
        "label": "SUM / AVG",
        "lesson_id": "ch-agg",
        "sql": "SELECT client, SUM(quantity) FROM orders GROUP BY client;",
        "text": "SUM addiert Werte, AVG mittelt, MIN/MAX holen das Kleinste und Größte. "
        "NULL zählt nicht mit. Mit GROUP BY gilt die Rechnung pro Gruppe.",
    },
    {
        "id": "CASE",
        "label": "CASE",
        "lesson_id": "ch-case",
        "sql": "SELECT CASE status WHEN 'offen' THEN 'läuft' ELSE status END FROM orders;",
        "text": "CASE setzt je nach Bedingung einen anderen Wert. Die Zeile bleibt. "
        "Ohne ELSE wird der Rest NULL.",
    },
    {
        "id": "COALESCE",
        "label": "COALESCE",
        "lesson_id": "ch-case",
        "sql": "SELECT COALESCE(c.name, 'ohne Kunde') FROM orders o LEFT JOIN clients c ON c.id = o.client_id;",
        "text": "COALESCE nimmt den ersten Wert, der nicht NULL ist. So bleibt 4730 sichtbar, der Name wird lesbar.",
    },
    {
        "id": "SUBQUERY",
        "label": "Unterabfrage",
        "lesson_id": "ch-subq",
        "sql": "SELECT * FROM orders WHERE id IN (SELECT order_id FROM order_items);",
        "text": "Eine Abfrage in der anderen. IN nimmt eine Werteliste. EXISTS prüft, ob mindestens eine Zeile passt.",
    },
]


def extra_lessons():
    from lessons.path_more import extra_path_lessons

    return extra_path_lessons() + [
        {
            "id": "ch-alias",
            "chapter": 8,
            "title": "DISTINCT und Aliase",
            "minutes": 10,
            "goal": "Du holst eindeutige Werte und gibst Spalten mit AS einen lesbaren Namen.",
            "concepts": ["SELECT"],
            "model": ["SELECT", "FROM"],
            "steps": [
                {
                    "type": "look",
                    "title": "Dieselben Werte, viele Zeilen",
                    "text": "In `orders` kommt **Helio** oft vor — jede Zeile ist ein Auftrag. "
                    "Manchmal willst du keine Auftragsliste, sondern: **welche Kunden kommen vor?**\n\n"
                    "`DISTINCT` entfernt doppelte Ergebniszeilen.",
                    "table": orders_table("order_number", "client", "status"),
                    "note": "Helio, Alpin, Nordkai wiederholen sich. Ein Auftrag ohne Kundenname bleibt eine eigene (leere) Ausprägung.",
                    "cta": "Weiter",
                },
                {
                    "type": "predict",
                    "title": "Welche Kunden kommen in orders vor?",
                    "text": "`SELECT DISTINCT client FROM orders WHERE client IS NOT NULL` — "
                    "markiere die **Kunden**, deren Name in den Aufträgen vorkommt.",
                    "sql": "SELECT DISTINCT client FROM orders WHERE client IS NOT NULL;",
                    "table": clients_table(),
                    "expected_ids": [10, 20, 30],
                    "id_field": "id",
                    "execute": True,
                    "concepts": ["SELECT"],
                    "feedback_ok": "Helio, Alpin, Nordkai. Westfeld hat keinen Auftrag — der Name taucht in orders nicht auf.",
                    "feedback_bad": "Westfeld hat keinen Auftrag. Markiere nur Helio, Alpin und Nordkai.",
                },
                {
                    "type": "explain",
                    "title": "AS gibt der Spalte einen Namen",
                    "text": "Das Ergebnis darf anders heißen als die Tabellenspalte. `AS` ist nur ein Etikett in **dieser** Query.",
                    "sql": "SELECT order_number AS nummer, status\nFROM orders;",
                    "plain": "Dieselbe Spalte, im Ergebnis heißt sie nummer.",
                    "parts": [
                        {
                            "match": "SELECT order_number AS nummer",
                            "token": "SELECT",
                            "question": "Was?",
                            "answer": "Die Auftragsnummer, aber die Ergebnis-Spalte heißt `nummer`.",
                        },
                        {
                            "match": "FROM orders",
                            "token": "FROM",
                            "question": "Woher?",
                            "answer": "Unverändert aus `orders`. AS ändert keine Daten, nur den Namen.",
                        },
                    ],
                    "concepts": ["SELECT"],
                },
                {
                    "type": "write",
                    "title": "Länder ohne Doppelte",
                    "prompt": "Welche Länder kommen in der Kundentabelle vor? Jedes Land nur einmal.",
                    "placeholder": "SELECT …",
                    "solution": "SELECT DISTINCT country FROM clients;",
                    "strict_columns": True,
                    "concepts": ["SELECT"],
                    "hints": [
                        "Du willst Werte, nicht jede Kundenzeile. Das Wort dafür ist DISTINCT.",
                        "Die Spalte heißt `country` in `clients`. DE kommt zweimal vor — DISTINCT macht einmal draus.",
                    ],
                },
                {
                    "type": "apply",
                    "title": "Lesbarer Spaltenname",
                    "prompt": "Zeig alle Kundennamen. Die Ergebnis-Spalte soll `kunde` heißen.",
                    "placeholder": "SELECT …",
                    "solution": "SELECT name AS kunde FROM clients;",
                    "strict_columns": True,
                    "concepts": ["SELECT"],
                    "hints": [
                        "Die Tabellenspalte heißt `name`. Im Ergebnis soll sie `kunde` heißen: AS.",
                        "SELECT name AS kunde FROM clients.",
                    ],
                },
            ],
            "quiz": [
                Q("Was macht DISTINCT?", [
                    "Es sortiert die Zeilen.",
                    "Es entfernt doppelte Ergebniszeilen.",
                    "Es filtert wie WHERE.",
                    "Es verbindet Tabellen.",
                ], 1, "DISTINCT wirkt auf das fertige Ergebnis: gleiche Zeilen nur einmal."),
                Q("Warum DISTINCT client und nicht SELECT client?", [
                    "Sonst kennt SQL den Kunden nicht.",
                    "Ohne DISTINCT kommt jeder Auftrag — Helio also viele Male.",
                    "DISTINCT ist Pflicht hinter SELECT.",
                    "client darf man sonst nicht auswählen.",
                ], 1, "Jede Auftragszeile hat einen client-Wert. Ohne DISTINCT siehst du Duplikate."),
                Q("Was ändert AS an den gespeicherten Daten?", [
                    "Es benennt die Spalte in der Tabelle dauerhaft um.",
                    "Nichts — nur den Namen in diesem Ergebnis.",
                    "Es löscht die alte Spalte.",
                    "Es erzeugt einen Index.",
                ], 1, "AS ist ein Etikett für die Query, kein ALTER TABLE."),
                Q("Warum schreiben wir FROM orders o?", [
                    "o ist ein Status.",
                    "o ist ein Tabellen-Alias: Kurzname in dieser Query.",
                    "Postgres verlangt immer einen Buchstaben.",
                    "o filtert offene Aufträge.",
                ], 1, "Später bei JOINs: o.order_number und c.name, weil beide Tabellen eine id haben."),
            ],
        },
        {
            "id": "ch-having",
            "chapter": 10,
            "title": "HAVING — Gruppen filtern",
            "minutes": 10,
            "goal": "Du unterscheidest: WHERE filtert Zeilen, HAVING filtert Gruppen nach dem Zählen.",
            "concepts": ["GROUP BY"],
            "model": ["SELECT", "FROM", "WHERE", "GROUP BY", "HAVING"],
            "steps": [
                {
                    "type": "explain",
                    "title": "Zwei Filter, zwei Zeitpunkte",
                    "text": "**WHERE** läuft **bevor** gruppiert wird: Welche Zeilen dürfen in Gruppen?\n\n"
                    "**HAVING** läuft **danach**: Welche Gruppen bleiben — z. B. nur wenn COUNT(*) groß genug ist.\n\n"
                    "`HAVING COUNT(*) > 4` kannst du nicht als WHERE schreiben, weil COUNT erst nach GROUP BY existiert.",
                    "sql": "SELECT client, COUNT(*)\nFROM orders\nWHERE client IS NOT NULL\nGROUP BY client\nHAVING COUNT(*) > 4;",
                    "plain": "Kunden mit mehr als vier Aufträgen.",
                    "parts": [
                        {"match": "WHERE client IS NOT NULL", "token": "WHERE", "question": "Welche Zeilen?", "answer": "Ohne Kundenname raus — bevor gezählt wird."},
                        {"match": "GROUP BY client", "token": "GROUP BY", "question": "Nach was?", "answer": "Eine Gruppe je Kundenname."},
                        {"match": "HAVING COUNT(*) > 4", "token": "HAVING", "question": "Welche Gruppen?", "answer": "Nur Gruppen, in denen mehr als vier Zeilen waren."},
                    ],
                    "concepts": ["GROUP BY"],
                },
                {
                    "type": "write",
                    "title": "Viel-Besteller",
                    "prompt": "Zeig je Kundenname die Anzahl der Aufträge. Nur Kunden mit **mehr als 4** Aufträgen. Zeilen ohne Kundenname weglassen.",
                    "placeholder": "SELECT …",
                    "solution": (
                        "SELECT client, COUNT(*) FROM orders "
                        "WHERE client IS NOT NULL GROUP BY client HAVING COUNT(*) > 4;"
                    ),
                    "concepts": ["GROUP BY"],
                    "hints": [
                        "Zuerst GROUP BY client und COUNT(*). Die Schwelle gehört nicht in WHERE.",
                        "HAVING COUNT(*) > 4. WHERE nur für client IS NOT NULL.",
                    ],
                },
                {
                    "type": "apply",
                    "title": "Offene, dann die Gruppen",
                    "prompt": "Nur **offene** Aufträge zählen — und nur Kunden, die **mehr als 4** offene Aufträge haben. Kundenname und Anzahl.",
                    "placeholder": "SELECT …",
                    "solution": (
                        "SELECT client, COUNT(*) FROM orders "
                        "WHERE status = 'offen' AND client IS NOT NULL "
                        "GROUP BY client HAVING COUNT(*) > 4;"
                    ),
                    "concepts": ["GROUP BY", "WHERE"],
                    "hints": [
                        "Status ist eine Zeilen-Eigenschaft → WHERE. Die Anzahl ist eine Gruppen-Eigenschaft → HAVING.",
                        "WHERE status = 'offen', danach GROUP BY client, HAVING COUNT(*) > 4.",
                    ],
                },
            ],
            "quiz": [
                Q("Wann läuft WHERE im Vergleich zu GROUP BY?", [
                    "Danach, auf die Gruppen.",
                    "Davor, auf einzelne Zeilen.",
                    "Nur zusammen mit JOIN.",
                    "WHERE und GROUP BY sind dasselbe.",
                ], 1, "WHERE wirft Zeilen weg, dann werden die Reste gruppiert."),
                Q("Wann brauchst du HAVING statt WHERE?", [
                    "Immer, wenn du COUNT verwendest.",
                    "Wenn die Bedingung die **Gruppe** betrifft (z. B. COUNT(*) > 4).",
                    "Wenn der Status offen ist.",
                    "HAVING ersetzt FROM.",
                ], 1, "COUNT existiert erst nach dem Gruppieren."),
                Q("Warum nicht WHERE COUNT(*) > 4?", [
                    "Postgres kennt kein COUNT.",
                    "COUNT ist noch nicht berechnet, wenn WHERE läuft.",
                    "Das Größer-Zeichen ist verboten.",
                    "WHERE darf keine Zahlen vergleichen.",
                ], 1, "Die logische Reihenfolge: FROM → WHERE → GROUP BY → HAVING → SELECT."),
                Q("Du willst nur offene Aufträge, dann pro Kunde zählen. Wohin kommt status = 'offen'?", [
                    "Nach HAVING.",
                    "Nach WHERE.",
                    "Nur in SELECT.",
                    "In ON.",
                ], 1, "Status gehört zur Zeile, nicht zur Gruppe."),
            ],
        },
        {
            "id": "ch-keys",
            "chapter": 11,
            "title": "Schlüssel und Relationen",
            "minutes": 12,
            "goal": "Du siehst, warum Daten in mehreren Tabellen stehen und wie id / client_id sie verbinden.",
            "concepts": ["TABLE", "JOIN"],
            "model": ["FROM", "JOIN", "ON"],
            "steps": [
                {
                    "type": "look",
                    "title": "Warum nicht alles in einer Tabelle?",
                    "text": "In `orders` steht der Kundenname zur Übung noch einmal. Das echte Stammdatum liegt in `clients`: Name **und** Land.\n\n"
                    "Würde das Land in jeder Auftragszeile stehen, müsstest du es an vielen Stellen ändern. "
                    "Stattdessen speichern wir das Land **einmal** beim Kunden.",
                    "tables": [
                        clients_table(),
                        orders_table("id", "order_number", "client_id", "client"),
                    ],
                    "note": "Westfeld existiert als Kunde, hat aber keinen Auftrag. Auftrag 4730 hat keine client_id.",
                    "cta": "Schlüssel ansehen",
                },
                {
                    "type": "inspect",
                    "title": "Wo hängt der Auftrag am Kunden?",
                    "text": "Tippe auf die **Spaltenüberschrift**, die auf `clients.id` zeigt.",
                    "table": orders_table("id", "order_number", "client_id", "client"),
                    "interaction": "click_column",
                    "answer": "client_id",
                    "concepts": ["TABLE"],
                    "feedback_ok": "client_id ist der Fremdschlüssel: derselbe Wert wie clients.id.",
                    "feedback_bad": "Nicht `client` — der Name kann sich wiederholen. Tippe auf `client_id`.",
                },
                {
                    "type": "look",
                    "title": "Eins-zu-viele: Positionen",
                    "text": "Ein Auftrag kann **mehrere Positionen** haben. Dafür gibt es `order_items`: "
                    "jede Zeile gehört zu genau einem `order_id`.\n\n"
                    "Auftrag 4730 hat **keine** Position — analog zum Kunden ohne Auftrag.",
                    "table": items_table("id", "order_id", "sku", "qty"),
                    "note": "order_id 1 kommt zweimal vor: zwei Positionen, ein Auftrag. Das ist 1:n.",
                    "cta": "Weiter",
                },
                {
                    "type": "mcq",
                    "title": "Primary Key",
                    "text": "In `clients` ist `id` der Primary Key.",
                    "question": "Was leistet der Primary Key?",
                    "options": [
                        {"text": "Er identifiziert genau eine Zeile.", "correct": True},
                        {"text": "Er speichert das Land.", "correct": False},
                        {"text": "Er sortiert automatisch absteigend.", "correct": False},
                    ],
                    "concepts": ["TABLE"],
                    "explain": "Zwei Kunden dürfen gleich heißen — nicht dieselbe id haben.",
                },
                {
                    "type": "write",
                    "title": "Stammdaten lesen",
                    "prompt": "Zeig id und Name aller Kunden.",
                    "placeholder": "SELECT …",
                    "solution": "SELECT id, name FROM clients;",
                    "strict_columns": True,
                    "concepts": ["SELECT", "TABLE"],
                    "hints": [
                        "Die Kundentabelle heißt `clients`.",
                        "Zwei Spalten: id und name.",
                    ],
                },
                {
                    "type": "apply",
                    "title": "Verweis lesen",
                    "prompt": "Zeig Auftragsnummer und client_id aller Aufträge, die einem Kunden zugeordnet sind.",
                    "placeholder": "SELECT …",
                    "solution": "SELECT order_number, client_id FROM orders WHERE client_id IS NOT NULL;",
                    "strict_columns": True,
                    "concepts": ["WHERE", "TABLE"],
                    "hints": [
                        "Der Verweis heißt client_id. Fehlt er, ist er NULL.",
                        "WHERE client_id IS NOT NULL.",
                    ],
                },
            ],
            "quiz": [
                Q("Was ist ein Primary Key?", [
                    "Ein zweiter Tabellenname.",
                    "Ein eindeutiger Schlüssel für genau eine Zeile.",
                    "Immer der Kundenname.",
                    "Ein JOIN-Befehl.",
                ], 1, "Meist die Spalte id. Eindeutig, nicht null."),
                Q("Was ist orders.client_id?", [
                    "Der Primary Key von orders.",
                    "Ein Foreign Key: Verweis auf clients.id.",
                    "Das Land des Kunden.",
                    "Die Anzahl der Kunden.",
                ], 1, "Gleicher Wert, andere Tabelle. So entsteht die Relation."),
                Q("Warum eine extra Tabelle clients?", [
                    "SQL kann nur drei Spalten pro Tabelle.",
                    "Stammdaten (Name, Land) einmal speichern, Aufträge zeigen nur auf die id.",
                    "Sonst funktioniert WHERE nicht.",
                    "Postgres verlangt immer zwei Tabellen.",
                ], 1, "Keine kopierten Länder in jeder Auftragszeile."),
                Q("Was bedeutet 1:n zwischen Auftrag und Position?", [
                    "Genau eine Position pro Datenbank.",
                    "Ein Auftrag kann viele Positionszeilen haben, jede Position gehört zu einem Auftrag.",
                    "n ist ein Statuscode.",
                    "Es gibt keine Aufträge ohne Position, technisch erzwungen in dieser Übung.",
                ], 1, "order_items.order_id zeigt auf orders.id. Auftrag 4730 hat 0 Positionen — das ist erlaubt."),
            ],
        },
        {
            "id": "ch-dml",
            "chapter": 16,
            "title": "Daten ändern",
            "minutes": 14,
            "goal": "Du fügst Zeilen ein, änderst sie gezielt und löschst nur mit WHERE.",
            "concepts": ["DML"],
            "model": ["INSERT", "UPDATE", "WHERE"],
            "steps": [
                {
                    "type": "explain",
                    "title": "Lesen war bisher alles",
                    "text": "SELECT ändert die Tabelle nicht. Jetzt kommen drei Schreib-Befehle:\n\n"
                    "**INSERT** — neue Zeile\n**UPDATE** — vorhandene Werte ändern\n**DELETE** — Zeile entfernen\n\n"
                    "Ohne WHERE bei UPDATE/DELETE trifft der Befehl **alle** Zeilen.",
                    "sql": "INSERT INTO stock (id, item, quantity, weight)\nVALUES (8, 'Karton H', 4, 18);",
                    "plain": "Eine neue Bestandszeile mit id 8.",
                    "parts": [
                        {"match": "INSERT INTO stock", "token": "INSERT", "question": "Wohin?", "answer": "In die Tabelle stock."},
                        {"match": "(id, item, quantity, weight)", "token": "INSERT", "question": "Welche Felder?", "answer": "Du nennst die Spalten, dann die Werte in derselben Reihenfolge."},
                        {"match": "VALUES (8, 'Karton H', 4, 18)", "token": "INSERT", "question": "Was genau?", "answer": "Eine neue Zeile. Text in Anführungszeichen, Zahlen ohne."},
                    ],
                    "concepts": ["SELECT"],
                },
                {
                    "type": "write",
                    "title": "Eine Zeile anlegen",
                    "prompt": "Füge in `stock` den Artikel **Karton H** ein: id 8, Menge 4, Gewicht 18.",
                    "placeholder": "INSERT …",
                    "allow_write": True,
                    "require": ["INSERT"],
                    "verify": "SELECT id, item, quantity, weight FROM stock WHERE id = 8;",
                    "solution": "INSERT INTO stock (id, item, quantity, weight) VALUES (8, 'Karton H', 4, 18);",
                    "concepts": ["SELECT"],
                    "hints": [
                        "INSERT INTO Tabelle (Spalten) VALUES (Werte);",
                        "id 8, item 'Karton H', quantity 4, weight 18.",
                    ],
                },
                {
                    "type": "explain",
                    "title": "UPDATE braucht ein Ziel",
                    "text": "`SET` sagt den neuen Wert. `WHERE` sagt, **welche Zeilen**. "
                    "Vergiss WHERE, ändert Postgres jede Zeile der Tabelle.",
                    "sql": "UPDATE orders\nSET status = 'fertig'\nWHERE order_number = 4714;",
                    "plain": "Nur Auftrag 4714 wird fertig — nicht alle.",
                    "parts": [
                        {"match": "UPDATE orders", "token": "UPDATE", "question": "Welche Tabelle?", "answer": "orders."},
                        {"match": "SET status = 'fertig'", "token": "UPDATE", "question": "Was ändert sich?", "answer": "Die Spalte status wird auf fertig gesetzt."},
                        {"match": "WHERE order_number = 4714", "token": "WHERE", "question": "Welche Zeile?", "answer": "Nur die mit Nummer 4714."},
                    ],
                    "concepts": ["WHERE"],
                },
                {
                    "type": "apply",
                    "title": "Einen Auftrag abschließen",
                    "prompt": "Setze den Status von Auftrag **4714** auf `fertig`. Nur diese eine Zeile.",
                    "placeholder": "UPDATE …",
                    "allow_write": True,
                    "require": ["UPDATE", "WHERE"],
                    "verify": "SELECT status FROM orders WHERE order_number = 4714;",
                    "solution": "UPDATE orders SET status = 'fertig' WHERE order_number = 4714;",
                    "concepts": ["WHERE"],
                    "hints": [
                        "UPDATE Tabelle SET spalte = wert WHERE …",
                        "Ohne WHERE würdest du alle Aufträge auf fertig setzen.",
                    ],
                },
                {
                    "type": "write",
                    "title": "Eine Zeile entfernen",
                    "prompt": "Lösche die Bestandszeile mit id **7** (Palette G).",
                    "placeholder": "DELETE …",
                    "allow_write": True,
                    "require": ["DELETE", "WHERE"],
                    "verify": "SELECT id FROM stock WHERE id = 7;",
                    "solution": "DELETE FROM stock WHERE id = 7;",
                    "concepts": ["WHERE"],
                    "hints": [
                        "DELETE FROM stock WHERE … — sonst wäre der ganze Bestand weg.",
                        "Die Zeile identifizierst du über id = 7.",
                    ],
                },
            ],
            "quiz": [
                Q("Was passiert bei UPDATE orders SET status = 'fertig' ohne WHERE?", [
                    "Nichts, Postgres verlangt WHERE.",
                    "Jede Zeile in orders wird fertig.",
                    "Nur die erste Zeile ändert sich.",
                    "Die Tabelle wird gelöscht.",
                ], 1, "WHERE ist der Schutz. Ohne Filter gilt SET für alle Zeilen."),
                Q("Welcher Befehl legt eine neue Zeile an?", [
                    "UPDATE",
                    "INSERT",
                    "DELETE",
                    "GROUP BY",
                ], 1, "INSERT INTO … VALUES …"),
                Q("Warum WHERE bei DELETE?", [
                    "DELETE funktioniert sonst nur auf views.",
                    "Sonst werden alle Zeilen der Tabelle gelöscht.",
                    "WHERE sortiert vor dem Löschen.",
                    "Ohne WHERE kennt Postgres den Tabellennamen nicht.",
                ], 1, "DELETE FROM stock; leert stock."),
                Q("Ändert SELECT die gespeicherten Daten?", [
                    "Ja, es speichert das Ergebnis dauerhaft.",
                    "Nein. SELECT liest. INSERT/UPDATE/DELETE schreiben.",
                    "Nur SELECT * schreibt.",
                    "SELECT löscht NULL-Zellen.",
                ], 1, "Lesen und Schreiben sind getrennt. Deshalb war der Anfänger-Pfad zuerst nur SELECT."),
            ],
        },
        {
            "id": "ch-tx",
            "chapter": 17,
            "title": "Transaktionen",
            "minutes": 10,
            "goal": "Du verstehst BEGIN, COMMIT und ROLLBACK als alles-oder-nichts.",
            "concepts": ["TX"],
            "model": ["UPDATE", "WHERE"],
            "steps": [
                {
                    "type": "look",
                    "title": "Mehrere Schritte, eine Entscheidung",
                    "text": "Stell dir vor, du setzt einen Auftrag auf fertig **und** verringerst den Bestand. "
                    "Wenn der zweite Schritt scheitert, soll der erste **nicht** gelten.\n\n"
                    "Eine **Transaktion** bündelt Befehle:\n\n"
                    "`BEGIN` — Anfang\n`COMMIT` — alles festschreiben\n`ROLLBACK` — alles seit BEGIN verwerfen",
                    "table": orders_table("order_number", "client", "status"),
                    "cta": "Ausprobieren",
                },
                {
                    "type": "explain",
                    "title": "ROLLBACK macht die Änderung ungeschehen",
                    "text": "Zwischen BEGIN und ROLLBACK siehst du die Änderung in **dieser** Session — "
                    "danach ist sie weg. Andere bekommen sie nie zu sehen, wenn du nicht COMMIT sendest.",
                    "sql": "BEGIN;\nUPDATE orders SET status = 'fertig' WHERE order_number = 4711;\nROLLBACK;",
                    "plain": "Probeweise fertig, dann verworfen. 4711 bleibt offen.",
                    "parts": [
                        {"match": "BEGIN", "token": "BEGIN", "question": "Was startet?", "answer": "Eine Transaktion. Ab jetzt gehören die nächsten Befehle zusammen."},
                        {"match": "UPDATE orders SET status = 'fertig' WHERE order_number = 4711", "token": "UPDATE", "question": "Änderung?", "answer": "Nur innerhalb der Transaktion."},
                        {"match": "ROLLBACK", "token": "ROLLBACK", "question": "Ende?", "answer": "Verwerfen. Die Tabelle ist wieder wie vor BEGIN."},
                    ],
                    "concepts": ["SELECT"],
                },
                {
                    "type": "write",
                    "title": "Verwerfen üben",
                    "prompt": "Starte eine Transaktion, setze Auftrag 4711 probeweise auf `fertig`, und verwirf die Änderung. Danach soll 4711 weiterhin `offen` sein.",
                    "placeholder": "BEGIN; …",
                    "allow_write": True,
                    "require": ["BEGIN", "ROLLBACK"],
                    "verify": "SELECT status FROM orders WHERE order_number = 4711;",
                    "solution": (
                        "BEGIN; "
                        "UPDATE orders SET status = 'fertig' WHERE order_number = 4711; "
                        "ROLLBACK;"
                    ),
                    "concepts": ["SELECT"],
                    "hints": [
                        "Drei Teile: BEGIN, dann UPDATE mit WHERE, dann ROLLBACK — nicht COMMIT.",
                        "Alles in einem Skript, Befehle mit Semikolon getrennt.",
                    ],
                },
                {
                    "type": "apply",
                    "title": "Festschreiben",
                    "prompt": "Setze Auftrag **4717** (storniert) in einer Transaktion auf `offen` und schreibe fest.",
                    "placeholder": "BEGIN; …",
                    "allow_write": True,
                    "require": ["BEGIN", "COMMIT"],
                    "verify": "SELECT status FROM orders WHERE order_number = 4717;",
                    "solution": (
                        "BEGIN; "
                        "UPDATE orders SET status = 'offen' WHERE order_number = 4717; "
                        "COMMIT;"
                    ),
                    "concepts": ["SELECT"],
                    "hints": [
                        "Wie eben, aber am Ende COMMIT statt ROLLBACK.",
                        "WHERE auf order_number = 4717, sonst änderst du zu viel.",
                    ],
                },
                {
                    "type": "mcq",
                    "title": "Alles oder nichts",
                    "question": "Was bedeutet COMMIT?",
                    "options": [
                        {"text": "Die Transaktion wird verworfen.", "correct": False},
                        {"text": "Alle Änderungen seit BEGIN werden dauerhaft.", "correct": True},
                        {"text": "Die Verbindung zur Datenbank endet.", "correct": False},
                    ],
                    "concepts": ["SELECT"],
                    "explain": "COMMIT = festschreiben. ROLLBACK = verwerfen. Dazwischen ist nichts für andere sichtbar (je nach Isolationsstufe — für den Einstieg reicht: erst COMMIT gilt).",
                },
            ],
            "quiz": [
                Q("Was macht ROLLBACK?", [
                    "Es speichert die Änderung.",
                    "Es verwirft alle Änderungen seit BEGIN.",
                    "Es löscht die Tabelle.",
                    "Es ist ein Synonym für DELETE.",
                ], 1, "Die Transaktion wird abgebrochen. Der vorherige Zustand bleibt."),
                Q("Warum Transaktionen, nicht drei einzelne UPDATEs nacheinander ohne BEGIN?", [
                    "Ohne BEGIN kennt Postgres kein UPDATE.",
                    "Scheitert der zweite Schritt, soll der erste nicht „halb“ gelten.",
                    "COMMIT ist schneller als UPDATE.",
                    "WHERE funktioniert nur in Transaktionen.",
                ], 1, "Atomar: alles oder nichts."),
                Q("BEGIN ohne COMMIT und ohne ROLLBACK — was passiert in dieser App oft?", [
                    "Die Änderung ist für immer gespeichert.",
                    "Die Verbindung endet und Postgres verwirft die offene Transaktion.",
                    "Die ganze Datenbank wird zurückgesetzt.",
                    "INSERT wird verboten.",
                ], 1, "Deshalb gehören BEGIN und COMMIT/ROLLBACK ins selbe Skript."),
                Q("Darfst du in einer Transaktion SELECT nutzen?", [
                    "Nein, nur UPDATE.",
                    "Ja — oft prüfst du nach dem UPDATE mit SELECT, bevor du COMMIT sendest.",
                    "Nur auf leeren Tabellen.",
                    "SELECT beendet die Transaktion automatisch.",
                ], 1, "Lesen in der Transaktion sieht deine noch nicht committeten Änderungen."),
            ],
        },
        {
            "id": "ch-pg",
            "chapter": 18,
            "title": "Wie Postgres denkt",
            "minutes": 12,
            "goal": "Du ordnest Datenbank, Schema, Typen und Index grob ein und liest EXPLAIN als Plan, nicht als Orakel.",
            "concepts": ["TABLE"],
            "model": ["SELECT", "FROM", "WHERE"],
            "steps": [
                {
                    "type": "look",
                    "title": "Schichten",
                    "text": "**Instanz** — der laufende Postgres-Server.\n"
                    "**Datenbank** — ein Behälter darin (hier: die Lern-DB).\n"
                    "**Schema** — Namensraum in der Datenbank. Unsere Übungen liegen in `learn`.\n"
                    "**Tabelle** — orders, clients, stock, order_items.\n\n"
                    "Wenn du `FROM orders` schreibst, sucht Postgres die Tabelle über den `search_path` — bei uns `learn` zuerst.",
                    "tables": [clients_table("id", "name"), orders_table("id", "order_number", "client_id")],
                    "cta": "Weiter zu Typen",
                },
                {
                    "type": "explain",
                    "title": "Typen sind Verträge",
                    "text": "Jede Spalte hat einen Datentyp. `integer` ist eine ganze Zahl, `text` Zeichen, `date` ein Kalendertag.\n\n"
                    "Deshalb ist `status = 0` etwas anderes als `status = 'offen'`. "
                    "Und `quantity IS NULL` ist etwas anderes als `quantity = 0`.",
                    "sql": "SELECT order_number, quantity, created_at\nFROM orders\nWHERE quantity > 10;",
                    "plain": "quantity ist eine Zahl — deshalb funktioniert > 10.",
                    "parts": [
                        {"match": "quantity > 10", "token": "WHERE", "question": "Typ?", "answer": "Zahl verglichen mit Zahl. Text in Anführungszeichen, Zahlen ohne."},
                        {"match": "created_at", "token": "SELECT", "question": "Datum?", "answer": "Ein Datum, kein Text. Damit kannst du ORDER BY vom Neuesten zum Ältesten sortieren."},
                    ],
                    "concepts": ["COMPARE"],
                },
                {
                    "type": "look",
                    "title": "Index wie ein Register",
                    "text": "Ohne Index liest Postgres im Zweifel **die ganze Tabelle** (Seq Scan) und prüft WHERE an jeder Zeile.\n\n"
                    "Ein **Index** ist ein extra Nachschlagewerk: „status offen → diese Zeilen“. "
                    "Für unsere Mini-Tabellen ist das egal. Bei Millionen Zeilen wird es der Unterschied zwischen Sekunden und Millisekunden.\n\n"
                    "Du musst jetzt keine Indexe anlegen. Du sollst die Idee kennen.",
                    "table": orders_table(),
                    "note": "EXPLAIN zeigt den Plan. Kosten-Zahlen sind Schätzungen, kein Urteil über dich.",
                    "cta": "EXPLAIN ansehen",
                },
                {
                    "type": "demo",
                    "title": "Einen Plan lesen",
                    "text": "Ausführen. Du siehst keinen Auftrag, sondern Zeilen wie `Seq Scan on orders`. "
                    "Das heißt: Postgres plant, die Tabelle zu lesen und zu filtern.",
                    "sql": "EXPLAIN SELECT * FROM orders WHERE status = 'offen';",
                    "table": orders_table("order_number", "status"),
                    "allow_write": False,
                    "concepts": ["WHERE"],
                },
                {
                    "type": "write",
                    "title": "Selbst den Plan holen",
                    "prompt": "Lass Postgres den Plan für „alle Bestandszeilen mit Gewicht mindestens 100“ erklären — nicht die Daten ausgeben.",
                    "placeholder": "EXPLAIN …",
                    "check": "explain",
                    "require": ["EXPLAIN"],
                    "solution": "EXPLAIN SELECT * FROM stock WHERE weight >= 100;",
                    "concepts": ["COMPARE"],
                    "hints": [
                        "Vor die ganz normale SELECT-Query das Wort EXPLAIN setzen.",
                        "Dieselbe WHERE-Bedingung wie früher bei den schweren Paletten.",
                    ],
                },
                {
                    "type": "mcq",
                    "title": "Was EXPLAIN nicht ist",
                    "question": "Was zeigt EXPLAIN?",
                    "options": [
                        {"text": "Die gespeicherten Zeilen der Tabelle.", "correct": False},
                        {"text": "Den geplanten Ausführungsweg — noch nicht das fachliche Ergebnis.", "correct": True},
                        {"text": "Ob deine Query inhaltlich die Aufgabe löst.", "correct": False},
                    ],
                    "concepts": ["TABLE"],
                    "explain": "EXPLAIN ist ein Werkzeug zum Verstehen, kein Ersatz für SELECT. Window Functions, JSON und Replikation kommen später — nicht in diesem Grundlagenpfad.",
                },
            ],
            "quiz": [
                Q("In welcher Schicht liegen unsere Übungstabellen?", [
                    "Als eigene Postgres-Instanz pro Tabelle.",
                    "Als Tabellen im Schema learn in der Lern-Datenbank.",
                    "Nur im Browser, nicht in Postgres.",
                    "Im Schema public, unsichtbar.",
                ], 1, "Instanz → Datenbank → Schema learn → Tabelle."),
                Q("Warum ist status = 0 meist falsch, wenn Status Texte sind?", [
                    "0 ist immer NULL.",
                    "Der Typ passt nicht: Status ist Text wie 'offen', keine Zahl.",
                    "WHERE darf keine Vergleiche.",
                    "0 löscht die Spalte.",
                ], 1, "Typen sind Verträge. Text in Anführungszeichen."),
                Q("Was ist ein Index — für den Einstieg?", [
                    "Eine zweite Datenbank.",
                    "Ein Stichwortregister, damit Postgres nicht immer die ganze Tabelle lesen muss.",
                    "Ein Synonym für PRIMARY KEY, das man immer manuell anlegt.",
                    "Ein SQL-Fehler.",
                ], 1, "Primary Keys bekommen in Postgres automatisch einen Index. Weitere Indexe sind eine bewusste Entscheidung."),
                Q("Was gehört nicht zu diesem Grundlagenpfad?", [
                    "SELECT, JOIN, GROUP BY, Transaktionen.",
                    "Replication, Vacuum und Query-Tuning als Alltag.",
                    "NULL und Foreign Keys.",
                    "EXPLAIN grob lesen.",
                ], 1, "Das kannst du später vertiefen. Zuerst sitzen die Konzepte."),
            ],
        },
        {
            "id": "challenge-3",
            "chapter": 19,
            "title": "Challenge: Offene Aufträge in DE",
            "minutes": 10,
            "goal": "Du verbindest Tabellen, filterst, gruppierst und sortierst — ohne Syntax-Liste.",
            "concepts": ["JOIN", "GROUP BY", "WHERE"],
            "challenge": True,
            "model": ["SELECT", "FROM", "JOIN", "ON", "WHERE", "GROUP BY", "ORDER BY"],
            "steps": [
                {
                    "type": "look",
                    "title": "Die Frage steht, nicht das SQL",
                    "text": "Land sitzt in `clients`, Aufträge in `orders`. "
                    "Westfeld hat keinen Auftrag. Ein Auftrag hat keinen Kunden.\n\n"
                    "Du entscheidest JOIN-Art, Filter und ob du zählst oder auflistest.",
                    "tables": [
                        clients_table(),
                        orders_table("order_number", "client", "status"),
                    ],
                    "cta": "Aufgabe öffnen",
                },
                {
                    "type": "challenge",
                    "title": "Auswertung",
                    "prompt": "Wie viele **offene** Aufträge hat jeder Kunde in **DE**? "
                    "Zeig Kundenname und Anzahl. Kunden ohne offene Aufträge sollen **nicht** erscheinen. "
                    "Die größte Anzahl zuerst.",
                    "placeholder": "Übersetze die Frage in SQL…",
                    "solution": (
                        "SELECT c.name, COUNT(*) FROM orders o "
                        "JOIN clients c ON c.id = o.client_id "
                        "WHERE o.status = 'offen' AND c.country = 'DE' "
                        "GROUP BY c.name ORDER BY COUNT(*) DESC;"
                    ),
                    "strict_columns": True,
                    "ordered": True,
                    "concepts": ["JOIN", "GROUP BY", "WHERE"],
                    "hints": [
                        "Land und Name: clients. Offene Aufträge: orders. Welche JOIN-Art lässt Kunden ohne Treffer weg?",
                        "WHERE auf Status und Land, dann GROUP BY Name, ORDER BY COUNT(*) DESC.",
                    ],
                },
            ],
            "quiz": [
                Q("Warum INNER JOIN und nicht LEFT JOIN?", [
                    "LEFT JOIN kann nicht zählen.",
                    "Kunden ohne offene Aufträge sollen nicht erscheinen — INNER JOIN behält nur Paare.",
                    "INNER JOIN filtert automatisch auf DE.",
                    "ON funktioniert nur mit INNER.",
                ], 1, "Westfeld hätte bei LEFT JOIN COUNT 0 oder eine NULL-Gruppe — die Aufgabe will das nicht."),
                Q("Wohin gehört country = 'DE'?", [
                    "Nach HAVING, weil es eine Gruppe ist.",
                    "Nach WHERE (Eigenschaft der Kundenzeile), bevor oder nach dem JOIN — fachlich auf c.country.",
                    "Nur in SELECT.",
                    "In ORDER BY.",
                ], 1, "Land ist kein Aggregat."),
                Q("Warum GROUP BY c.name?", [
                    "Sonst kennt SQL den Namen nicht.",
                    "COUNT(*) braucht eine Gruppe — „pro Kunde“.",
                    "GROUP BY sortiert nach Name.",
                    "Ohne GROUP BY geht JOIN nicht.",
                ], 1, "Eine Ergebniszeile je Kunde."),
                Q("Was hast du in diesem Pfad gelernt, das über Syntax hinausgeht?", [
                    "Die Musterlösung auswendig.",
                    "Fachfragen zerlegen: welche Tabellen, welche Naht, welche Zeilen, welche Gruppen, welche Ordnung.",
                    "Window Functions und JSON.",
                    "Dass SELECT * immer reicht.",
                ], 1, "Die Wörter sind Werkzeug. Die Zerlegung ist die Fähigkeit."),
            ],
        },
    ]


def flashcards():
    cards = []
    for item in GLOSSARY:
        cards.append({
            "id": f"gloss-{item['id']}",
            "front": f"Was ist {item['label']}?",
            "back": item["text"],
            "lesson_id": item.get("lesson_id") or "",
            "lesson": item["label"],
        })
    return cards
