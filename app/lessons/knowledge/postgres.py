from lessons.knowledge.schema import article, card


def articles():
    return [
        article(
            "schema",
            "Schema",
            "postgres",
            "Instanz → Datenbank → Schema → Tabelle. Diese App arbeitet im Schema learn.",
            """
PostgreSQL schichtet. Die Instanz ist der Server. Darin Datenbanken. In einer Datenbank Schemas. In einem Schema Tabellen.

`learn.orders` ist eindeutig. Der `search_path` sagt, wo `orders` ohne Präfix gesucht wird. In der App reicht der kurze Name.

Schema-Änderungen (`CREATE TABLE`, `DROP`) sind in der Sandbox gesperrt. Du lernst fragen und ändern von **Daten**, nicht das Datenmodell umbauen.
""",
            sql=["SELECT * FROM orders;", "SELECT * FROM learn.orders;"],
            pitfalls=["learn ist das Schema, learnsql die Datenbank.", "Ohne search_path findest du Tabellen nur mit learn.tabelle."],
            related=["typen", "index"],
            lesson_id="ch-pg",
            cards=[
                card("sch-begriff", "begriff", "Was ist ein Schema?", "Ein Namensraum in der Datenbank. Hier: learn mit orders, clients, stock, order_items."),
                card("sch-wann", "wann", "Wann schreibst du learn.orders?", "Wenn der Suchpfad das Schema nicht kennt — in der App meist unnötig."),
                card("sch-fehler", "fehler", "Ist learn die Datenbank?", "Nein. Die Datenbank heißt learnsql. learn ist das Schema."),
                card("sch-pred", "predict", "Welche vier Trainingstabellen gibt es?", "orders, clients, stock, order_items."),
            ],
        ),
        article(
            "typen",
            "Datentypen",
            "postgres",
            "Typen sind Verträge. Text in Anführungszeichen, Zahlen ohne. Der falsche Typ knallt oder vergleicht falsch.",
            """
`status` ist Text (`offen`). `quantity` ist eine Zahl. `created_at` ein Datum.

`WHERE status = 0` ist der falsche Vertrag. `WHERE quantity = 'offen'` ebenso.

Postgres wandelt manchmal still. Verlass dich nicht darauf. Im Grundlagenpfad: Anführungszeichen = Text.
""",
            sql=["SELECT order_number, status, quantity, created_at FROM orders;", "SELECT item, weight FROM stock WHERE weight >= 100;"],
            pitfalls=["0 ist nicht NULL und nicht '0' als Status.", "Datum und Text sortieren unterschiedlich."],
            related=["vergleiche", "schema"],
            lesson_id="ch-pg",
            cards=[
                card("typ-begriff", "begriff", "Warum sind Typen Verträge?", "Die Spalte erwartet eine Art von Wert. Falsche Art: Fehler oder Unsinn."),
                card("typ-wann", "wann", "Wann Anführungszeichen?", "Bei Text und bei Datums-Literalen, die du als Text schreibst. Nicht bei Zahlen."),
                card("typ-fehler", "fehler", "Was ist falsch an status = 0?", "Status ist Text wie 'offen', keine Zahl."),
                card("typ-pred", "predict", "Ist quantity bei 4731 0 oder NULL?", "NULL — unbekannt, nicht null Stück."),
            ],
        ),
        article(
            "index",
            "Index",
            "postgres",
            "Ein Index ist ein Stichwortregister. Postgres findet passende Zeilen, ohne immer die ganze Tabelle zu lesen.",
            """
Primary Keys bekommen automatisch einen Index. Weitere Indexe sind eine bewusste Entscheidung: oft auf Spalten, die du häufig in WHERE oder JOIN nutzt.

Ein Index beschleunigt Lesen und kostet Schreiben. Für 24 Aufträge merkst du nichts. Die Idee zählt.

Du legst in der Sandbox keine Indexe an. `EXPLAIN` zeigt, ob ein Plan einen Index nutzen würde.
""",
            sql=["EXPLAIN SELECT * FROM orders WHERE status = 'offen';", "EXPLAIN SELECT * FROM orders WHERE id = 1;"],
            pitfalls=["Index ist kein zweites SELECT.", "Mehr Indexe machen INSERT/UPDATE langsamer."],
            related=["explain", "primary-key"],
            lesson_id="ch-pg",
            cards=[
                card("idx-begriff", "begriff", "Was ist ein Index — für den Einstieg?", "Ein Register, damit Postgres nicht immer jede Zeile anfassen muss."),
                card("idx-wann", "wann", "Welche Spalte hat automatisch einen Index?", "Der Primary Key, hier id."),
                card("idx-fehler", "fehler", "Ist ein Index dasselbe wie eine zweite Tabelle zum Abfragen?", "Nein. Du schreibst weiter SELECT auf orders. Der Index ist intern."),
                card("idx-pred", "predict", "Warum ist EXPLAIN kein Tuning-Kurs?", "Er zeigt den Plan. Entscheiden, ob ein Index fehlt, kommt später."),
            ],
        ),
        article(
            "explain",
            "EXPLAIN",
            "postgres",
            "EXPLAIN zeigt den Plan, nicht die Datenzeilen. Du willst sehen, wie Postgres die Frage angehen würde.",
            """
`EXPLAIN SELECT * FROM orders WHERE status = 'offen';` — eine Spalte `QUERY PLAN`, keine Aufträge.

`EXPLAIN ANALYZE` führt die Query aus und misst. Zum Lernen reicht EXPLAIN.

Seq Scan heißt: ganze Tabelle lesen. Index Scan heißt: über das Register. Bei kleinen Tabellen ist Seq Scan normal und kein Fehler.
""",
            sql=["EXPLAIN SELECT * FROM orders WHERE status = 'offen';", "EXPLAIN SELECT o.order_number FROM orders o JOIN clients c ON c.id = o.client_id;"],
            pitfalls=["EXPLAIN ohne SELECT danach ist unvollständig.", "Den Plan mit dem Ergebnis verwechseln."],
            related=["index", "select"],
            lesson_id="ch-pg",
            cards=[
                card("exx-begriff", "begriff", "Was liefert EXPLAIN?", "Den geplanten Ausführungsweg, nicht die Ergebniszeilen."),
                card("exx-wann", "wann", "Wann schreibst du EXPLAIN vor ein SELECT?", "Wenn du den Plan willst, nicht die Daten."),
                card("exx-fehler", "fehler", "Ist Seq Scan immer schlecht?", "Nein. Bei wenigen Zeilen ist die ganze Tabelle lesen oft richtig."),
                card("exx-luecke", "luecke", "______ SELECT * FROM orders WHERE status = 'offen';", "EXPLAIN", "EXPLAIN SELECT ..."),
            ],
        ),
    ]
