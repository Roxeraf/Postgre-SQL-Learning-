from lessons.knowledge.schema import article, card


def articles():
    return [
        article(
            "count",
            "COUNT",
            "rechnen",
            "COUNT(*) zählt Zeilen. COUNT(spalte) zählt gesetzte Werte. COUNT(DISTINCT …) zählt eindeutige.",
            """
Ohne GROUP BY kommt **eine** Zahl. `SELECT COUNT(*) FROM orders WHERE status = 'offen'` ist die Anzahl offener Aufträge.

`COUNT(*)` zählt Zeilen, auch wenn Spalten NULL sind. `COUNT(quantity)` überspringt leere Mengen. `COUNT(DISTINCT client)` zählt Kundennamen einmal.

Nach GROUP BY gilt COUNT innerhalb der Gruppe: pro Status, pro Kunde.
""",
            sql=["SELECT COUNT(*) FROM orders WHERE status = 'offen';", "SELECT status, COUNT(*) FROM orders GROUP BY status;"],
            pitfalls=["COUNT(*) ist nicht SUM.", "COUNT(quantity) ist kleiner, sobald Mengen fehlen."],
            related=["group-by", "sum", "having"],
            lesson_id="ch8",
            cards=[
                card("cnt-begriff", "begriff", "Was liefert COUNT(*) ohne GROUP BY?", "Eine Zahl: wie viele Zeilen nach WHERE übrig sind."),
                card("cnt-wann", "wann", "Wann COUNT(quantity) statt COUNT(*)?", "Wenn du nur Zeilen mit gesetzter Menge zählen willst."),
                card("cnt-fehler", "fehler", "Zählt COUNT(*) den Auftrag 4731 (leere Menge)?", "Ja. Die Zeile existiert. COUNT(quantity) zählt ihn nicht."),
                card("cnt-luecke", "luecke", "SELECT ______ FROM orders;", "COUNT(*)", "SELECT COUNT(*) FROM orders;"),
            ],
        ),
        article(
            "sum",
            "SUM",
            "rechnen",
            "SUM addiert Zahlen einer Spalte. NULL geht nicht in die Summe.",
            """
`SUM(quantity)` addiert Mengen. Offene Aufträge: zuerst WHERE, dann SUM.

4731 ist offen und hat keine Menge — die Zeile bleibt in der Tabelle, die Summe überspringt NULL. Das ist kein 0.

Mit GROUP BY bekommst du eine Summe pro Gruppe: pro Kunde, pro sku in `order_items`.
""",
            sql=["SELECT SUM(quantity) FROM orders WHERE status = 'offen';", "SELECT client, SUM(quantity) FROM orders WHERE client IS NOT NULL GROUP BY client;"],
            pitfalls=["SUM zählt keine Zeilen — das ist COUNT.", "COALESCE(quantity, 0) vor SUM macht aus Lücken Nullen. Bewusst tun."],
            related=["avg", "count", "group-by"],
            lesson_id="ch-agg",
            cards=[
                card("sum-begriff", "begriff", "Was macht SUM(quantity)?", "Es addiert die Zahlen in quantity. NULL zählt nicht."),
                card("sum-wann", "wann", "Wann SUM statt COUNT?", "Wenn die Frage „wie viel Menge?“ heißt, nicht „wie viele Aufträge?“."),
                card("sum-fehler", "fehler", "Warum fehlt 4731 in der offenen Summe?", "quantity ist NULL."),
                card("sum-pred", "predict", "SUM ohne GROUP BY — wie viele Ergebniszeilen?", "Eine."),
            ],
        ),
        article(
            "avg",
            "AVG",
            "rechnen",
            "AVG ist der Mittelwert der gesetzten Zahlen. NULL fließt nicht ein.",
            """
`AVG(quantity)` teilt die Summe durch die Anzahl gesetzter Werte, nicht durch COUNT(*).

Leere Mengen machen das Mittel größer oder kleiner als „Summe / alle Zeilen“. Wenn du 0 mitmeinen willst, musst du das sagen: `AVG(COALESCE(quantity, 0))`.

Wie SUM: ohne GROUP BY eine Zahl, mit GROUP BY eine Zahl pro Gruppe.
""",
            sql=["SELECT AVG(quantity) FROM orders;", "SELECT client, AVG(quantity) FROM orders WHERE client IS NOT NULL GROUP BY client;"],
            pitfalls=["AVG ignoriert NULL, teilt also durch weniger Zeilen.", "AVG von Text geht nicht."],
            related=["sum", "min-max", "group-by"],
            lesson_id="ch-agg",
            cards=[
                card("avg-begriff", "begriff", "Was ist AVG?", "Der Mittelwert der nicht-NULL-Werte einer Zahlen-Spalte."),
                card("avg-wann", "wann", "Wann AVG pro Kunde?", "GROUP BY client, SELECT client, AVG(quantity)."),
                card("avg-fehler", "fehler", "Teilt AVG durch COUNT(*)?", "Nein. Nur durch die Zeilen, deren Spalte gesetzt ist."),
                card("avg-luecke", "luecke", "SELECT client, ______ (quantity) FROM orders GROUP BY client;", "AVG", "SELECT client, AVG(quantity) FROM orders GROUP BY client;"),
            ],
        ),
        article(
            "min-max",
            "MIN und MAX",
            "rechnen",
            "MIN holt den kleinsten Wert, MAX den größten. Geht für Zahlen, Text und Daten.",
            """
`MAX(quantity)` ist die größte Menge. `MIN(created_at)` das älteste Datum.

Mit GROUP BY gilt das pro Gruppe: schwerster Artikel je … — in `stock` ohne Gruppe: `SELECT MAX(weight) FROM stock`.

Bei Text ist die Ordnung die Sortierung der Zeichen. Für Status ist MIN/MAX selten die fachliche Antwort.
""",
            sql=["SELECT MAX(quantity) FROM orders;", "SELECT MIN(created_at), MAX(created_at) FROM orders;"],
            pitfalls=["MAX filtert nicht — es verdichtet.", "NULL ist weder Min noch Max."],
            related=["sum", "order-by", "group-by"],
            lesson_id="ch-agg",
            cards=[
                card("mm-begriff", "begriff", "Unterschied MIN und MAX?", "Kleinster gegen größter gesetzter Wert."),
                card("mm-wann", "wann", "Wie holst du das neueste Auftragsdatum?", "MAX(created_at) oder ORDER BY created_at DESC LIMIT 1."),
                card("mm-fehler", "fehler", "Ist MAX dasselbe wie ORDER BY DESC LIMIT 1?", "Für eine Spalte oft ja. LIMIT 1 kann die ganze Zeile liefern, MAX nur den Wert."),
                card("mm-pred", "predict", "MAX(weight) im Bestand?", "120 — Palette A."),
            ],
        ),
        article(
            "group-by",
            "GROUP BY",
            "rechnen",
            "GROUP BY macht eine Ergebniszeile je Gruppe. Was in SELECT nicht aggregiert ist, muss gruppiert sein.",
            """
`GROUP BY status` — eine Zeile für offen, fertig, storniert. Daneben `COUNT(*)` oder `SUM(quantity)`.

Postgres verlangt: jede SELECT-Spalte ist entweder in GROUP BY oder in einer Aggregatfunktion. `SELECT client, status, COUNT(*)` ohne `GROUP BY client, status` ist ein Fehler.

WHERE filtert **vorher**. HAVING filtert **nachher** die Gruppen.
""",
            sql=["SELECT status, COUNT(*) FROM orders GROUP BY status;", "SELECT client, SUM(quantity) FROM orders WHERE client IS NOT NULL GROUP BY client;"],
            pitfalls=["SELECT client, COUNT(*) ohne GROUP BY client scheitert.", "Eine NULL-Gruppe entsteht, wenn client leer ist und du nicht filterst."],
            related=["having", "count", "sum"],
            lesson_id="ch8",
            cards=[
                card("gb-begriff", "begriff", "Wozu ist GROUP BY da?", "Gleichartige Zeilen zu einer Ergebniszeile zusammenziehen."),
                card("gb-wann", "wann", "Wann GROUP BY client?", "Wenn die Frage „pro Kunde“ heißt."),
                card("gb-fehler", "fehler", "Warum ist SELECT client, status, COUNT(*) ohne beide in GROUP BY falsch?", "status wäre weder gruppiert noch aggregiert."),
                card("gb-luecke", "luecke", "SELECT status, COUNT(*) FROM orders ________ status;", "GROUP BY", "GROUP BY status"),
            ],
        ),
        article(
            "having",
            "HAVING",
            "rechnen",
            "HAVING filtert Gruppen nach dem Aggregat. WHERE filtert Zeilen davor.",
            """
`HAVING COUNT(*) > 4` kannst du nicht als WHERE schreiben: COUNT existiert erst nach GROUP BY.

Die Reihenfolge: FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY.

„Nur offene, dann Kunden mit mehr als vier offenen“: Status in WHERE, Schwelle in HAVING.
""",
            sql=[
                "SELECT client, COUNT(*) FROM orders WHERE client IS NOT NULL GROUP BY client HAVING COUNT(*) > 4;",
                "SELECT client, COUNT(*) FROM orders WHERE status = 'offen' AND client IS NOT NULL GROUP BY client HAVING COUNT(*) > 4;",
            ],
            pitfalls=["HAVING status = 'offen' geht, ist aber der falsche Ort — das ist WHERE.", "Ohne GROUP BY ist HAVING selten sinnvoll."],
            related=["group-by", "where", "count"],
            lesson_id="ch-having",
            cards=[
                card("hav-begriff", "begriff", "Wann HAVING statt WHERE?", "Wenn die Bedingung die Gruppe betrifft — COUNT(*) > 4."),
                card("hav-wann", "wann", "Wohin kommt status = 'offen' beim Zählen offener pro Kunde?", "Nach WHERE. Die Anzahl-Schwelle nach HAVING."),
                card("hav-fehler", "fehler", "Warum nicht WHERE COUNT(*) > 4?", "COUNT ist noch nicht da, wenn WHERE läuft."),
                card("hav-luecke", "luecke", "GROUP BY client ______ COUNT(*) > 4", "HAVING", "HAVING COUNT(*) > 4"),
            ],
        ),
        article(
            "case",
            "CASE",
            "rechnen",
            "CASE setzt je nach Bedingung einen anderen Wert. Die Zeile bleibt.",
            """
Zwei Schreibweisen: `CASE status WHEN 'offen' THEN 'läuft' … END` und `CASE WHEN quantity > 10 THEN 'groß' ELSE 'klein' END`.

Ohne ELSE wird der Rest NULL. ELSE 'anders' macht unbekannte Status sichtbar.

CASE gehört in SELECT, ORDER BY oder manchmal WHERE. Es ersetzt keinen JOIN.
""",
            sql=[
                "SELECT order_number, CASE status WHEN 'offen' THEN 'läuft' WHEN 'fertig' THEN 'erledigt' ELSE 'anders' END FROM orders;",
                "SELECT item, CASE WHEN weight >= 100 THEN 'schwer' ELSE 'leicht' END FROM stock;",
            ],
            pitfalls=["END nicht vergessen.", "CASE filtert nicht — das bleibt WHERE."],
            related=["coalesce", "select"],
            lesson_id="ch-case",
            cards=[
                card("case-begriff", "begriff", "Was macht CASE?", "Es wählt je Bedingung einen Ergebniswert. Die Zeile bleibt."),
                card("case-wann", "wann", "Wann CASE statt mehrerer Queries?", "Wenn du Labels oder Klassen in einer Ergebnisliste brauchst."),
                card("case-fehler", "fehler", "Was passiert ohne ELSE, wenn kein WHEN trifft?", "Das Ergebnis der Spalte ist NULL."),
                card("case-luecke", "luecke", "CASE status WHEN 'offen' THEN 'läuft' ELSE 'anders' ____", "END", "END"),
            ],
        ),
    ]
