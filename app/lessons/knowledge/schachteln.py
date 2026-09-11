from lessons.knowledge.schema import article, card


def articles():
    return [
        article(
            "unterabfrage",
            "Unterabfrage",
            "schachteln",
            "Eine SELECT in der anderen. IN nimmt eine Werteliste. Skalare Unterabfragen liefern einen Wert.",
            """
`WHERE id IN (SELECT order_id FROM order_items)` — innen die ids mit Position, außen die Aufträge.

Die innere Frage darf nur so viele Spalten liefern, wie außen erwartet werden. Für IN: eine Spalte.

Eine skalare Unterabfrage steht in SELECT: `(SELECT MAX(quantity) FROM orders)` neben jeder Zeile. Das ist erlaubt, oft reicht aber ein Join oder ein CTE.
""",
            sql=[
                "SELECT order_number, status FROM orders WHERE id IN (SELECT order_id FROM order_items);",
                "SELECT * FROM orders WHERE quantity = (SELECT MAX(quantity) FROM orders);",
            ],
            pitfalls=["Die innere SELECT-Liste muss zur Stelle passen.", "IN und JOIN können dieselbe Menge liefern — JOIN kann extra Spalten zeigen."],
            related=["exists", "in-liste", "with-cte"],
            lesson_id="ch-subq",
            cards=[
                card("uq-begriff", "begriff", "Was ist eine Unterabfrage?", "Ein SELECT, das in einem anderen SELECT steckt."),
                card("uq-wann", "wann", "Wann IN (SELECT …) statt JOIN?", "Wenn du nur prüfen willst, ob die id vorkommt — ohne Spalten der inneren Tabelle."),
                card("uq-fehler", "fehler", "Was muss die innere Query bei IN liefern?", "Eine Spalte mit Werten, keine ganzen Zeilen-Sterne nötig, aber eine Liste."),
                card("uq-pred", "predict", "Welche Auftragsnummer fehlt in IN (SELECT order_id FROM order_items)?", "4730."),
            ],
        ),
        article(
            "exists",
            "EXISTS",
            "schachteln",
            "EXISTS ist wahr, sobald die innere Query mindestens eine Zeile findet. NOT EXISTS findet Lücken.",
            """
`EXISTS (SELECT 1 FROM orders o WHERE o.client_id = c.id)` — gibt es irgendeinen Auftrag zu diesem Kunden?

`SELECT 1` ist üblich: uns interessiert nicht der Wert, nur ob eine Zeile da ist.

`NOT EXISTS` ist der saubere Anti-Join als Unterabfrage. Westfeld hat keine orders-Zeile. `NOT IN` wird unschön, wenn innen NULL vorkommt.
""",
            sql=[
                "SELECT name FROM clients c WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.client_id = c.id);",
                "SELECT order_number FROM orders o WHERE EXISTS (SELECT 1 FROM order_items i WHERE i.order_id = o.id);",
            ],
            pitfalls=["Die innere Query muss die äußere Zeile referenzieren (korreliert).", "EXISTS kümmert sich nicht um die SELECT-Liste innen."],
            related=["unterabfrage", "left-join"],
            lesson_id="ch-subq",
            cards=[
                card("ex-begriff", "begriff", "Wann ist EXISTS wahr?", "Sobald die innere Abfrage mindestens eine Zeile liefert."),
                card("ex-wann", "wann", "Wie findest du Kunden ohne Auftrag per Unterabfrage?", "NOT EXISTS (SELECT 1 FROM orders o WHERE o.client_id = c.id)."),
                card("ex-fehler", "fehler", "Warum NOT EXISTS statt NOT IN bei möglichen NULLs?", "NOT IN plus NULL in der Liste wird unbrauchbar. EXISTS prüft nur: gibt es eine Zeile?"),
                card("ex-pred", "predict", "NOT EXISTS gegen orders — welcher Kundenname?", "Westfeld."),
            ],
        ),
        article(
            "with-cte",
            "WITH (CTE)",
            "schachteln",
            "WITH benennt eine Zwischenergebnis-Tabelle für den Rest der Query. Nur Nachschlagen im Pfad, im Playground erlaubt.",
            """
`WITH offen AS (SELECT * FROM orders WHERE status = 'offen') SELECT COUNT(*) FROM offen;`

CTEs machen lange Fragen lesbar: erst die offenen, dann der Join, dann die Gruppe. Postgres behandelt einfache WITH oft wie eine Unterabfrage.

`WITH` ist in der Sandbox erlaubt. Im offiziellen Pfad ist es kein Pflicht-Kapitel — du darfst es trotzdem schreiben.
""",
            sql=[
                "WITH offen AS (SELECT * FROM orders WHERE status = 'offen') SELECT client, COUNT(*) FROM offen WHERE client IS NOT NULL GROUP BY client;",
                "WITH pos AS (SELECT order_id, SUM(qty) AS qty FROM order_items GROUP BY order_id) SELECT o.order_number, pos.qty FROM orders o JOIN pos ON pos.order_id = o.id;",
            ],
            pitfalls=["Der CTE-Name gilt nur in dieser Query.", "WITH ersetzt kein GROUP BY — es macht nur Schritte sichtbar."],
            related=["unterabfrage", "group-by"],
            lookup_only=True,
            cards=[
                card("with-begriff", "begriff", "Was ist WITH / ein CTE?", "Ein benanntes Zwischenergebnis, das die restliche Query wie eine Tabelle nutzt."),
                card("with-wann", "wann", "Wann WITH statt verschachtelter IN?", "Wenn du dieselbe Teilmenge mehrfach brauchst oder die Frage in Schritten lesen willst."),
                card("with-fehler", "fehler", "Lebt der CTE nach der Query weiter?", "Nein. Nur in dieser Anweisung."),
                card("with-luecke", "luecke", "______ offen AS (SELECT * FROM orders WHERE status = 'offen')", "WITH", "WITH offen AS (...)"),
            ],
        ),
    ]
