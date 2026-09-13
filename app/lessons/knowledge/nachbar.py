from lessons.knowledge.schema import article, card


def articles():
    return [
        article(
            "union",
            "UNION",
            "nachbar",
            "UNION stapelt zwei Ergebnisse untereinander. UNION ALL behält Doppelte. Nur Nachschlagen.",
            """
Beide SELECTs brauchen dieselbe Spaltenzahl und verträgliche Typen.

`UNION` entfernt doppelte Zeilen. `UNION ALL` nicht und ist billiger, wenn du Duplikate willst oder ausschließen kannst.

Das ist kein JOIN. JOIN stellt Spalten nebeneinander. UNION stellt Zeilen untereinander.
""",
            sql=[
                "SELECT name FROM clients WHERE country = 'DE' UNION SELECT name FROM clients WHERE country = 'AT';",
                "SELECT sku FROM order_items UNION ALL SELECT item FROM stock;",
            ],
            pitfalls=["UNION ist kein JOIN.", "Unterschiedliche Spaltenzahl scheitert."],
            related=["select", "join-inner"],
            lookup_only=True,
            cards=[
                card("un-begriff", "begriff", "Unterschied UNION und JOIN?", "UNION stapelt Zeilen. JOIN verbindet Spalten über eine Naht."),
                card("un-wann", "wann", "Wann UNION ALL?", "Wenn Duplikate bleiben dürfen oder du weißt, dass es keine gibt."),
                card("un-fehler", "fehler", "Darf das zweite SELECT mehr Spalten haben?", "Nein. Dieselbe Breite."),
                card("un-pred", "predict", "UNION ohne ALL — Doppelte?", "Werden entfernt."),
            ],
        ),
        article(
            "window",
            "Window Functions",
            "nachbar",
            "OVER() rechnet über eine Fenster-Menge, ohne Zeilen zu einer Gruppe zusammenzuziehen. Nur Nachschlagen.",
            """
`ROW_NUMBER() OVER (PARTITION BY client ORDER BY created_at DESC)` nummeriert Aufträge pro Kunde. Alle Zeilen bleiben sichtbar.

GROUP BY verdichtet. Window nicht. Deshalb siehst du Nummer, Status und Rang in einer Zeile.

Im Grundlagenpfad übst du das nicht. PARTITION BY ist „pro Gruppe“, ORDER BY im Fenster die Reihenfolge für Rang.
""",
            sql=[
                "SELECT order_number, client, ROW_NUMBER() OVER (PARTITION BY client ORDER BY created_at DESC) FROM orders WHERE client IS NOT NULL;",
                "SELECT order_number, quantity, SUM(quantity) OVER () FROM orders;",
            ],
            pitfalls=["OVER() ohne PARTITION gilt über alle Zeilen.", "Window ersetzt HAVING nicht 1:1."],
            related=["group-by", "order-by"],
            lookup_only=True,
            cards=[
                card("win-begriff", "begriff", "Was unterscheidet Window von GROUP BY?", "Window behält die Einzelzeilen. GROUP BY verdichtet sie."),
                card("win-wann", "wann", "Wozu ROW_NUMBER() OVER (PARTITION BY client …)?", "Rang pro Kunde, ohne die anderen Aufträge zu verlieren."),
                card("win-fehler", "fehler", "Ist das ein Pflicht-Thema im Pfad?", "Nein. Nur Nachschlagen."),
                card("win-luecke", "luecke", "ROW_NUMBER() ______ (ORDER BY created_at DESC)", "OVER", "OVER (...)"),
            ],
        ),
        article(
            "json",
            "JSON in Postgres",
            "nachbar",
            "jsonb speichert Dokumente. Der Operator -> holt Felder. Nur Nachschlagen — nicht im Pfad.",
            """
PostgreSQL kann JSON. In `learn` brauchst du das nicht: die Lagerdaten sind normale Spalten.

`->` liefert JSON, `->>` Text. Filter über `WHERE daten->>'ort' = 'DE'`.

Solange die Frage feste Felder hat (Status, Menge, Land), bleiben Tabellennormalform und JOIN die bessere Antwort.
""",
            sql=["SELECT jsonb_build_object('nummer', order_number, 'status', status) FROM orders;", "-- in learn gibt es keine JSON-Spalte zum Filtern"],
            pitfalls=["JSON ist kein Ersatz für clients/orders.", "-> und ->> sind leicht zu verwechseln."],
            related=["select", "typen"],
            lookup_only=True,
            cards=[
                card("js-begriff", "begriff", "Was ist jsonb grob?", "Ein JSON-Dokument als Postgres-Typ, durchsuchbar."),
                card("js-wann", "wann", "Wann normale Spalten statt JSON?", "Wenn Felder fest und gleichartig sind — Status, Menge, Land."),
                card("js-fehler", "fehler", "Ist JSON Teil des Grundlagenpfads?", "Nein."),
                card("js-pred", "predict", "-> vs ->> ?", "-> bleibt JSON, ->> wird Text."),
            ],
        ),
        article(
            "is-null-vs-equals",
            "IS NULL statt = NULL",
            "nachbar",
            "Der häufigste Filterfehler: = NULL ist nie wahr. Immer IS NULL.",
            """
SQL drewertig: wahr, falsch, unbekannt. `quantity = NULL` ist unbekannt, nicht wahr. WHERE behält nur Wahres.

`IS NULL` / `IS NOT NULL` sind die Operatoren für Lücken. Das gilt für JOIN-Reste (`c.name IS NULL`) genauso wie für Mengen.

COALESCE ersetzt den Wert. IS NULL findet die Zeile.
""",
            sql=["SELECT * FROM orders WHERE quantity IS NULL;", "SELECT * FROM orders WHERE quantity = NULL; -- findet nichts"],
            pitfalls=["= NULL in der Probe „zum Testen“ ist trotzdem falsch.", "IS NULL ist kein Vergleich mit dem Wort NULL."],
            related=["null", "coalesce", "where"],
            lesson_id="ch7",
            cards=[
                card("eqn-begriff", "begriff", "Warum nicht = NULL?", "Der Vergleich ergibt unbekannt. WHERE will wahr."),
                card("eqn-wann", "wann", "Wie filterst du leere Kundenzellen nach LEFT JOIN?", "WHERE c.id IS NULL oder c.name IS NULL."),
                card("eqn-fehler", "fehler", "Was liefert WHERE quantity = NULL?", "Keine Zeile."),
                card("eqn-luecke", "luecke", "WHERE quantity ______ NULL", "IS", "WHERE quantity IS NULL"),
            ],
        ),
        article(
            "join-vs-subquery",
            "JOIN oder Unterabfrage",
            "nachbar",
            "Dieselbe Menge, andere Form. JOIN holt Spalten dazu. IN/EXISTS prüft nur Zugehörigkeit.",
            """
„Welche Aufträge haben Positionen?“ — `id IN (SELECT order_id FROM order_items)` oder `JOIN order_items`. Die Menge kann gleich sein.

„Nummer plus sku plus qty“ braucht den JOIN. Die Unterabfrage kennt sku nicht, wenn sie nur ids liefert.

„Kunden ohne Auftrag“: Anti-Join (`LEFT JOIN … WHERE o.id IS NULL`) oder `NOT EXISTS`. Beide sind richtig. EXISTS ist oft klarer, sobald NULL in ids steckt.
""",
            sql=[
                "SELECT order_number FROM orders WHERE id IN (SELECT order_id FROM order_items);",
                "SELECT DISTINCT o.order_number FROM orders o JOIN order_items i ON i.order_id = o.id;",
            ],
            pitfalls=["JOIN ohne DISTINCT verdoppelt Aufträge mit mehreren Positionen.", "IN allein zeigt keine sku."],
            related=["join-inner", "unterabfrage", "exists"],
            lesson_id="ch-subq",
            cards=[
                card("jvs-begriff", "begriff", "Wann reicht IN, wann brauchst du JOIN?", "IN: nur Zugehörigkeit. JOIN: Spalten der zweiten Tabelle."),
                card("jvs-wann", "wann", "Wie vermeidest du Doppelzeilen beim JOIN auf items, wenn du nur die Nummer willst?", "DISTINCT oder EXISTS/IN."),
                card("jvs-fehler", "fehler", "Liefert JOIN immer weniger Zeilen als IN?", "Nein. JOIN kann mehr Zeilen erzeugen (1:n)."),
                card("jvs-pred", "predict", "Zwei Positionen, ein Auftrag, JOIN ohne GROUP BY — wie oft die Nummer?", "Zweimal."),
            ],
        ),
        article(
            "where-vs-on",
            "WHERE oder ON",
            "nachbar",
            "ON ist die Naht zwischen Tabellen. WHERE ist der fachliche Filter. Bei LEFT JOIN ändert das die Menge.",
            """
`ON c.id = o.client_id` sagt, wie Zeilen zusammengehören. `WHERE o.status = 'offen'` sagt, welche Aufträge du willst.

Bei INNER JOIN landen Filter in ON oder WHERE oft bei derselben Menge. Bei LEFT JOIN wirft WHERE auf rechte Spalten die „Lücken“-Zeilen weg.

Regel: Schlüssel in ON. Fachfilter in WHERE. Ausnahme: du filterst die rechte Tabelle **im Join**, ohne die linke zu verlieren — dann die Bedingung nach ON.
""",
            sql=[
                "SELECT o.order_number, c.name FROM orders o LEFT JOIN clients c ON c.id = o.client_id WHERE o.status = 'offen';",
                "SELECT o.order_number, c.name FROM orders o LEFT JOIN clients c ON c.id = o.client_id AND c.country = 'DE';",
            ],
            pitfalls=["country in WHERE nach LEFT JOIN löscht 4730.", "ON ohne Schlüssel, nur mit Status, ist keine Naht."],
            related=["left-join", "where", "join-inner"],
            lesson_id="ch10",
            cards=[
                card("wo-begriff", "begriff", "ON gegen WHERE?", "ON verbindet Tabellen. WHERE filtert das Ergebnis fachlich."),
                card("wo-wann", "wann", "Wohin gehört c.id = o.client_id?", "Nach ON."),
                card("wo-fehler", "fehler", "Warum nicht WHERE c.country = 'DE' nach LEFT JOIN orders→clients, wenn 4730 bleiben soll?", "country ist NULL, die Zeile fällt."),
                card("wo-pred", "predict", "INNER JOIN: Filter in ON oder WHERE für status?", "Meist dieselbe Menge. Lesbarkeit: WHERE."),
            ],
        ),
    ]
