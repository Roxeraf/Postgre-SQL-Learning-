from lessons.knowledge.schema import article, card


def articles():
    return [
        article(
            "tabelle",
            "Tabelle",
            "lesen",
            "Eine Relation: Zeilen sind Datensätze, Spalten sind Attribute. Jede Zelle hält einen Wert oder NULL.",
            """
Eine **Tabelle** ist die Grundform, in der Postgres Daten hält. Zeilen gehören zusammen (ein Auftrag, ein Kunde). Spalten haben Namen und einen Typ.

In dieser App heißt die Auftragstabelle `orders`, die Kunden `clients`, der Bestand `stock`, die Positionen `order_items`. Du fragst sie mit SQL — du klickst sie nicht wie in einer Tabellenkalkulation.

Die Reihenfolge der Zeilen in der Tabelle ist **keine** fachliche Reihenfolge. Wenn du „die neuesten zuerst“ willst, sagst du das mit `ORDER BY`.
""",
            sql=["SELECT * FROM orders;", "SELECT * FROM clients;"],
            pitfalls=[
                "Die sichtbare Reihenfolge ohne ORDER BY ist kein Versprechen.",
                "Eine leere Zelle ist NULL, nicht 0 und nicht leerer Text.",
            ],
            related=["select", "from", "null"],
            lesson_id="ch0",
            cards=[
                card("tabelle-begriff", "begriff", "Was ist eine Tabelle in SQL?", "Zeilen (Datensätze) und Spalten (Attribute). Eine Zelle hält einen Wert oder NULL."),
                card("tabelle-wann", "wann", "Wann denkst du in Tabellen statt in Dateien?", "Sobald mehrere gleichartige Datensätze dieselben Felder teilen — Aufträge, Kunden, Positionen."),
                card("tabelle-fehler", "fehler", "Warum ist „die erste Zeile der Tabelle“ keine stabile Aussage?", "Ohne ORDER BY legt Postgres die Reihenfolge nicht fest."),
                card("tabelle-luecke", "luecke", "Ergänze: SELECT * FROM ____;", "orders — oder jede andere Tabelle im Schema learn.", "SELECT * FROM orders;"),
            ],
        ),
        article(
            "select",
            "SELECT",
            "lesen",
            "SELECT bestimmt, welche Spalten (und Ausdrücke) im Ergebnis erscheinen. Es filtert keine Zeilen.",
            """
`SELECT` ist die Antwort auf: **Was will ich sehen?** Spaltennamen, Sterne, Ausdrücke wie `COUNT(*)` oder `COALESCE(c.name, 'ohne Kunde')`.

`SELECT` wirft keine Zeilen weg. Dafür ist `WHERE` da. Viele Anfänger schreiben `SELECT *` und wundern sich über zu viele Spalten — der Stern bedeutet alle.

Spalten kommen in der Reihenfolge, die du nennst. Aliase (`AS`) machen Überschriften lesbar.
""",
            sql=["SELECT order_number, status FROM orders;", "SELECT client, COUNT(*) FROM orders GROUP BY client;"],
            pitfalls=[
                "SELECT filtert keine Zeilen — das ist WHERE.",
                "Nach GROUP BY darf in SELECT nur Gruppenspalte oder Aggregat stehen.",
            ],
            related=["select-stern", "from", "alias", "where"],
            lesson_id="ch2",
            cards=[
                card("select-begriff", "begriff", "Wozu ist SELECT da?", "Es wählt, was im Ergebnis erscheint: Spalten und Ausdrücke. Nicht, welche Zeilen bleiben."),
                card("select-wann", "wann", "Wann nennst du Spalten statt *?", "Wenn die Frage bestimmte Felder will — Nummer und Status, nicht die ganze Zeile."),
                card("select-fehler", "fehler", "Warum hilft SELECT * nicht gegen zu viele Zeilen?", "Der Stern ändert die Breite, nicht die Länge. Zeilen filtert WHERE."),
                card("select-luecke", "luecke", "Ergänze: ______ order_number, status FROM orders;", "SELECT", "SELECT order_number, status FROM orders;"),
            ],
        ),
        article(
            "select-stern",
            "SELECT *",
            "lesen",
            "Der Stern holt alle Spalten der Tabelle. Praktisch zum Anschauen, selten die richtige Fachantwort.",
            """
`SELECT * FROM orders` ist der schnellste Blick: jede Spalte, jede Zeile (bis LIMIT). In der Akademie darfst du das zum Entdecken nutzen.

In einer Lagerfrage ist `*` oft zu viel. „Zeig Nummer und Status“ heißt zwei Spalten. `*` nimmt auch `note`, `created_at` und alles, was später dazukommt.

Bei JOINs verdoppelt `*` leicht ids aus beiden Tabellen. Dann lieber `o.order_number, c.name` schreiben.
""",
            sql=["SELECT * FROM stock;", "SELECT o.order_number, c.name FROM orders o JOIN clients c ON c.id = o.client_id;"],
            pitfalls=["Nach einem JOIN ist * oft doppeldeutig.", "* ändert sich, wenn jemand eine Spalte ergänzt."],
            related=["select", "join-inner"],
            lesson_id="ch2",
            cards=[
                card("stern-begriff", "begriff", "Was bedeutet SELECT *?", "Alle Spalten der FROM-Tabelle (oder aller Join-Tabellen)."),
                card("stern-wann", "wann", "Wann ist * in Ordnung?", "Zum Anschauen und Debuggen. Selten als Antwort auf eine konkrete Frage."),
                card("stern-fehler", "fehler", "Was ist nach INNER JOIN an SELECT * unschön?", "ids und gleichnamige Spalten aus beiden Tabellen landen doppelt im Ergebnis."),
                card("stern-pred", "predict", "SELECT * FROM clients — wie viele Spalten?", "Drei in dieser App: id, name, country."),
            ],
        ),
        article(
            "from",
            "FROM",
            "lesen",
            "FROM sagt, aus welcher Tabelle die Zeilen kommen. Ohne FROM weiß SQL nicht, woher.",
            """
Jede Lese-Frage braucht eine Herkunft. `FROM orders` heißt: nimm die Aufträge als Ausgangsmenge.

Später kommt der JOIN dazu: `FROM orders o JOIN clients c ON …`. FROM bleibt der Start — oft die Tabelle, die **nicht verschwinden** darf (bei LEFT JOIN die linke).

Tabellennamen in dieser App: `orders`, `clients`, `stock`, `order_items`. Sie liegen im Schema `learn`.
""",
            sql=["SELECT * FROM orders;", "SELECT * FROM order_items;"],
            pitfalls=["SELECT ohne FROM ist in Postgres ein Fehler, sobald du Tabellenspalten willst.", "Den Tabellennamen nicht in Anführungszeichen setzen."],
            related=["select", "join-inner", "schema"],
            lesson_id="ch1",
            cards=[
                card("from-begriff", "begriff", "Wozu ist FROM da?", "Es nennt die Tabelle (oder die Join-Kette), aus der die Zeilen kommen."),
                card("from-wann", "wann", "Welche Tabelle kommt nach FROM bei „alle Aufträge, Kunde extra“?", "orders — die Aufträge sollen bleiben, Kunden kommen per JOIN dazu."),
                card("from-fehler", "fehler", "Was fehlt an SELECT order_number?", "FROM orders. Sonst weiß Postgres nicht, welche Tabelle gemeint ist."),
                card("from-luecke", "luecke", "SELECT * ______ stock;", "FROM", "SELECT * FROM stock;"),
            ],
        ),
        article(
            "distinct",
            "DISTINCT",
            "lesen",
            "DISTINCT entfernt doppelte Ergebniszeilen. Du willst Wertelisten, nicht jede Rohzeile.",
            """
In `orders` kommt Helio oft vor — jeder Treffer ist ein Auftrag. `SELECT DISTINCT client FROM orders` liefert jeden Kundennamen einmal.

DISTINCT gilt für die **ganze Ergebniszeile**. `SELECT DISTINCT client, status` macht Paare eindeutig, nicht nur den Kunden.

Zählen eindeutiger Werte geht mit `COUNT(DISTINCT client)`. Das ist etwas anderes als `COUNT(*)`.
""",
            sql=["SELECT DISTINCT country FROM clients;", "SELECT COUNT(DISTINCT client) FROM orders WHERE client IS NOT NULL;"],
            pitfalls=["DISTINCT ist kein Filter auf die Tabelle, sondern auf das Ergebnis.", "NULL gilt als eigener Wert — eine leere client-Zelle erscheint einmal."],
            related=["select", "alias", "count"],
            lesson_id="ch-alias",
            cards=[
                card("distinct-begriff", "begriff", "Was macht DISTINCT?", "Es entfernt doppelte Ergebniszeilen."),
                card("distinct-wann", "wann", "Wann DISTINCT statt GROUP BY?", "Wenn du nur eindeutige Werte listen willst, ohne zu rechnen."),
                card("distinct-fehler", "fehler", "Warum liefert DISTINCT client, status mehr Zeilen als DISTINCT client?", "Paare müssen eindeutig sein. Derselbe Kunde mit zwei Status bleibt zweimal."),
                card("distinct-pred", "predict", "SELECT DISTINCT country FROM clients — welche Länder?", "AT, DE, CH. DE nur einmal, obwohl zwei Kunden in DE sitzen."),
            ],
        ),
        article(
            "alias",
            "Alias (AS)",
            "lesen",
            "AS gibt einer Spalte oder Tabelle in dieser Query einen Kurznamen.",
            """
`SELECT order_number AS nummer` ändert nur die Überschrift im Ergebnis, nicht die Tabelle.

Tabellen-Aliase (`orders o`, `clients c`) machen JOINs lesbar: `o.order_number`, `c.name`. Sobald zwei Tabellen eine `id` haben, **musst** du den Alias setzen.

In Postgres darfst du `AS` bei Tabellen weglassen: `FROM orders o`. Bei Spalten ist `AS` üblich und klar.
""",
            sql=["SELECT order_number AS nummer FROM orders;", "SELECT o.order_number, c.name FROM orders o JOIN clients c ON c.id = o.client_id;"],
            pitfalls=["Der Alias gilt nur in dieser Query.", "WHERE sieht Spalten-Aliase in Postgres nicht — filtere den Originalnamen."],
            related=["select", "join-inner"],
            lesson_id="ch-alias",
            cards=[
                card("alias-begriff", "begriff", "Was ist ein Alias?", "Ein Kurz- oder Anzeigename für Spalte oder Tabelle, nur in dieser Query."),
                card("alias-wann", "wann", "Wann brauchst du o. und c.?", "Sobald beide Tabellen eine id (oder gleichnamige Spalten) haben."),
                card("alias-fehler", "fehler", "Warum scheitert WHERE nummer = 4711 nach SELECT order_number AS nummer?", "WHERE läuft fachlich vor der SELECT-Liste. Der Alias nummer existiert dort noch nicht."),
                card("alias-luecke", "luecke", "FROM orders __ JOIN clients __ ON …", "o und c — freie Kurznamen, üblich ein Buchstabe.", "FROM orders o JOIN clients c ON c.id = o.client_id;"),
            ],
        ),
        article(
            "order-by",
            "ORDER BY",
            "lesen",
            "ORDER BY legt die Reihenfolge des Ergebnisses fest. ASC aufsteigend, DESC absteigend.",
            """
Ohne `ORDER BY` ist die Reihenfolge nicht die fachliche Antwort. „Neueste zuerst“ heißt `ORDER BY created_at DESC`.

Du kannst mehrere Schlüssel ketten: erst Status, dann Nummer. `ASC` ist Standard und darfst du weglassen.

Sortieren nach einem Ausdruck geht: `ORDER BY COUNT(*) DESC` nach dem Gruppieren.
""",
            sql=["SELECT * FROM orders ORDER BY created_at DESC;", "SELECT status, COUNT(*) FROM orders GROUP BY status ORDER BY COUNT(*) DESC;"],
            pitfalls=["ORDER BY ändert keine Zeilenmenge.", "NULL sortiert in Postgres bei ASC nach hinten, bei DESC nach vorn — merken, nicht raten."],
            related=["limit", "group-by"],
            lesson_id="ch6",
            cards=[
                card("ob-begriff", "begriff", "Wozu ist ORDER BY da?", "Es sortiert das Ergebnis. Es filtert nicht."),
                card("ob-wann", "wann", "Wie holst du die neuesten Aufträge zuerst?", "ORDER BY created_at DESC."),
                card("ob-fehler", "fehler", "Warum reicht SELECT * nicht für „aktuell“?", "Ohne ORDER BY ist „oben in der Liste“ Zufall."),
                card("ob-luecke", "luecke", "ORDER BY created_at ______", "DESC für die neuesten zuerst.", "ORDER BY created_at DESC;"),
            ],
        ),
        article(
            "limit",
            "LIMIT",
            "lesen",
            "LIMIT schneidet das Ergebnis nach n Zeilen ab. Sinnvoll fast immer zusammen mit ORDER BY.",
            """
`LIMIT 5` heißt: höchstens fünf Ergebniszeilen. Welche fünf das sind, bestimmt die Sortierung.

`LIMIT 5` ohne `ORDER BY` ist „irgendwelche fünf“. Für „die fünf neuesten“ gehört `ORDER BY created_at DESC LIMIT 5` zusammen.

`OFFSET` überspringt Zeilen (Seiten). In dieser App brauchst du das selten.
""",
            sql=["SELECT * FROM orders ORDER BY created_at DESC LIMIT 5;", "SELECT * FROM stock ORDER BY weight DESC NULLS LAST LIMIT 3;"],
            pitfalls=["LIMIT ohne ORDER BY ist nicht reproduzierbar.", "LIMIT ersetzt kein WHERE."],
            related=["order-by", "select"],
            lesson_id="ch6",
            cards=[
                card("limit-begriff", "begriff", "Was macht LIMIT 5?", "Es behält höchstens fünf Ergebniszeilen."),
                card("limit-wann", "wann", "Wann LIMIT plus ORDER BY?", "Immer wenn „die n größten / neuesten“ gemeint sind."),
                card("limit-fehler", "fehler", "Warum ist LIMIT 1 ohne ORDER BY gefährlich?", "Du bekommst irgendeine Zeile, nicht „die erste fachlich“."),
                card("limit-pred", "predict", "ORDER BY created_at DESC LIMIT 1 — was kommt?", "Der neueste Auftrag, eine Zeile."),
            ],
        ),
    ]
