from lessons.knowledge.schema import article, card


def articles():
    return [
        article(
            "insert",
            "INSERT",
            "aendern",
            "INSERT fügt neue Zeilen ein. Tabelle, Spalten, Werte.",
            """
`INSERT INTO stock (id, item, quantity, weight) VALUES (8, 'Karton H', 4, 18);`

Danach ist die Zeile Teil der Tabelle, bis UPDATE oder DELETE. In der Lern-App gilt das nur im Schema `learn`. Ein Reset holt den Samenstand zurück.

Spaltenliste schreiben. Dann siehst du, welche Werte wohin gehören. Typen müssen passen: Text in Anführungszeichen, Zahlen ohne.
""",
            sql=["INSERT INTO stock (id, item, quantity, weight) VALUES (8, 'Karton H', 4, 18);", "SELECT * FROM stock WHERE id = 8;"],
            pitfalls=["id doppelt verletzt den Primary Key.", "Vergessene Anführungszeichen bei item."],
            related=["update", "delete", "transaktion"],
            lesson_id="ch-dml",
            cards=[
                card("ins-begriff", "begriff", "Was macht INSERT?", "Es legt neue Zeilen an."),
                card("ins-wann", "wann", "Welche Klauseln braucht ein klares INSERT?", "INTO Tabelle, Spaltenliste, VALUES."),
                card("ins-fehler", "fehler", "Was passiert bei doppelter id?", "Primary-Key-Verletzung. Die Zeile kommt nicht rein."),
                card("ins-luecke", "luecke", "INSERT ______ stock (id, item) VALUES (9, 'Test');", "INTO", "INSERT INTO stock ..."),
            ],
        ),
        article(
            "update",
            "UPDATE",
            "aendern",
            "UPDATE ändert vorhandene Zeilen. SET setzt Werte. WHERE ist Pflicht im Kopf.",
            """
`UPDATE orders SET status = 'fertig' WHERE order_number = 4714;`

Ohne WHERE ändert Postgres **jede** Zeile. Das ist der teuerste Tippfehler im Lager.

Mehrere Spalten: `SET status = 'fertig', quantity = 0`. Transaktionen (`BEGIN` … `ROLLBACK`) retten dich beim Üben.
""",
            sql=["UPDATE orders SET status = 'fertig' WHERE order_number = 4714;", "UPDATE stock SET quantity = 0 WHERE id = 7;"],
            pitfalls=["UPDATE ohne WHERE trifft die ganze Tabelle.", "SET ist nicht WHERE."],
            related=["delete", "transaktion", "where"],
            lesson_id="ch-dml",
            cards=[
                card("upd-begriff", "begriff", "Was macht UPDATE?", "Es ändert Werte in vorhandenen Zeilen."),
                card("upd-wann", "wann", "Warum WHERE bei UPDATE?", "Sonst gilt SET für jede Zeile."),
                card("upd-fehler", "fehler", "Was ist das Risiko von UPDATE orders SET status = 'fertig'?", "Alle Aufträge werden fertig."),
                card("upd-luecke", "luecke", "UPDATE orders SET status = 'fertig' ______ order_number = 4714;", "WHERE", "WHERE order_number = 4714"),
            ],
        ),
        article(
            "delete",
            "DELETE",
            "aendern",
            "DELETE entfernt Zeilen. Auch hier: WHERE, sonst ist die Tabelle leer.",
            """
`DELETE FROM stock WHERE id = 7;`

`DELETE FROM stock` ohne WHERE leert die Tabelle. Schema und Spalten bleiben, die Daten nicht.

DELETE ist nicht DROP. DROP wäre die Tabelle selbst — in der Sandbox gesperrt.
""",
            sql=["DELETE FROM stock WHERE id = 7;", "SELECT * FROM stock WHERE id = 7;"],
            pitfalls=["DELETE ohne WHERE.", "DELETE verwechselt mit DROP TABLE."],
            related=["update", "insert", "transaktion"],
            lesson_id="ch-dml",
            cards=[
                card("del-begriff", "begriff", "Was macht DELETE?", "Es entfernt Zeilen. Die Tabelle bleibt."),
                card("del-wann", "wann", "Wie entfernst du eine Bestandszeile sicher?", "DELETE FROM stock WHERE id = …"),
                card("del-fehler", "fehler", "Was macht DELETE FROM stock ohne WHERE?", "Die Tabelle ist leer."),
                card("del-pred", "predict", "Ist DELETE dasselbe wie DROP?", "Nein. DROP entfernt das Objekt. DELETE nur Zeilen."),
            ],
        ),
        article(
            "returning",
            "RETURNING",
            "aendern",
            "RETURNING gibt die geänderten Zeilen zurück. Nur Nachschlagen — praktisch nach INSERT.",
            """
`INSERT INTO stock (id, item, quantity, weight) VALUES (8, 'Karton H', 4, 18) RETURNING id, item;`

Ohne RETURNING siehst du nur „INSERT 0 1“. Mit RETURNING kommt die Zeile wie ein SELECT zurück.

Geht auch bei UPDATE und DELETE. In der App prüft der Pfad über ein zweites SELECT (`verify`). RETURNING darfst du im Playground nutzen.
""",
            sql=["INSERT INTO stock (id, item, quantity, weight) VALUES (8, 'Karton H', 4, 18) RETURNING *;", "UPDATE orders SET status = 'fertig' WHERE id = 1 RETURNING order_number, status;"],
            pitfalls=["RETURNING ist kein Ersatz für WHERE.", "Nicht jeder Client zeigt RETURNING automatisch."],
            related=["insert", "update"],
            lookup_only=True,
            cards=[
                card("ret-begriff", "begriff", "Was macht RETURNING?", "Es liefert die Zeilen, die INSERT/UPDATE/DELETE gerade betroffen hat."),
                card("ret-wann", "wann", "Wann RETURNING nach INSERT?", "Wenn du die neue id oder die ganze Zeile sofort sehen willst."),
                card("ret-fehler", "fehler", "Ersetzt RETURNING das WHERE beim UPDATE?", "Nein. Ohne WHERE ändert es weiter alle Zeilen — und gibt alle zurück."),
                card("ret-luecke", "luecke", "INSERT INTO stock (…) VALUES (…) ________ *;", "RETURNING", "RETURNING *"),
            ],
        ),
        article(
            "transaktion",
            "Transaktion",
            "aendern",
            "BEGIN … COMMIT macht mehrere Änderungen zu einer Einheit. ROLLBACK verwirft alles seit BEGIN.",
            """
Entweder alles gilt oder nichts. `BEGIN;` ändern; bei Zweifel `ROLLBACK;` sonst `COMMIT;`.

Ohne Transaktion ist jedes Statement sofort fest. Beim Üben in der App: erst BEGIN, dann UPDATE, dann ROLLBACK — die Tabelle ist wieder wie vorher.

Savepoints und Isolation Levels sind Vertiefung. Hier reicht: eine Entscheidung für mehrere Schritte.
""",
            sql=["BEGIN; UPDATE orders SET status = 'fertig' WHERE id = 1; ROLLBACK;", "BEGIN; UPDATE orders SET status = 'fertig' WHERE id = 1; COMMIT;"],
            pitfalls=["Nach COMMIT hilft ROLLBACK nicht mehr.", "Ein Fehler ohne BEGIN lässt schon geschriebene Statements stehen."],
            related=["update", "delete", "insert"],
            lesson_id="ch-tx",
            cards=[
                card("tx-begriff", "begriff", "Was ist eine Transaktion?", "Mehrere Änderungen, die zusammen gelten oder zusammen fallen."),
                card("tx-wann", "wann", "Wann ROLLBACK?", "Wenn du die Änderungen seit BEGIN verwerfen willst."),
                card("tx-fehler", "fehler", "Hilft ROLLBACK nach COMMIT?", "Nein. COMMIT hat festgeschrieben."),
                card("tx-luecke", "luecke", "BEGIN; UPDATE …; ________;", "ROLLBACK oder COMMIT", "ROLLBACK;"),
            ],
        ),
        article(
            "on-conflict",
            "ON CONFLICT",
            "aendern",
            "Upsert: INSERT, und wenn der Schlüssel schon da ist, UPDATE oder nichts. Nur Nachschlagen.",
            """
`INSERT INTO stock (id, item, quantity, weight) VALUES (1, 'Palette A', 40, 120) ON CONFLICT (id) DO NOTHING;`

`DO UPDATE SET quantity = EXCLUDED.quantity` überschreibt bei Kollision.

Im Pfad übst du INSERT und UPDATE getrennt. ON CONFLICT ist die Kurzform für „anlegen oder auffrischen“.
""",
            sql=[
                "INSERT INTO stock (id, item, quantity, weight) VALUES (1, 'Palette A', 40, 120) ON CONFLICT (id) DO NOTHING;",
                "INSERT INTO stock (id, item, quantity, weight) VALUES (1, 'Palette A', 99, 120) ON CONFLICT (id) DO UPDATE SET quantity = EXCLUDED.quantity;",
            ],
            pitfalls=["ON CONFLICT braucht einen echten Unique-/Primary-Key.", "DO UPDATE ohne SET-Liste ist unvollständig."],
            related=["insert", "update"],
            lookup_only=True,
            cards=[
                card("oc-begriff", "begriff", "Was ist ON CONFLICT?", "Ein Anhang an INSERT: bei Schlüsselkollision nichts tun oder updaten."),
                card("oc-wann", "wann", "Wann DO NOTHING?", "Wenn die vorhandene Zeile bleiben soll und du keinen Fehler willst."),
                card("oc-fehler", "fehler", "Geht ON CONFLICT ohne Unique-Constraint?", "Nein. Postgres muss wissen, welcher Konflikt gemeint ist."),
                card("oc-pred", "predict", "INSERT id=1 nochmal, ON CONFLICT DO NOTHING — was ändert sich?", "Nichts an der bestehenden Palette A."),
            ],
        ),
    ]
