from lessons.knowledge.schema import article, card


def articles():
    return [
        article(
            "primary-key",
            "Primary Key",
            "verbinden",
            "Der Primary Key identifiziert eine Zeile eindeutig. Hier meist id.",
            """
Zwei Kunden dürfen denselben Namen haben, nie dieselbe `id`. Der Primary Key ist der feste Haken, an dem andere Tabellen ziehen.

In `orders` ist `id` der Schlüssel, `order_number` die fachliche Nummer. Für Joins nimmst du die `id`, nicht den Namen.

Postgres legt auf den Primary Key automatisch einen Index.
""",
            sql=["SELECT id, name FROM clients;", "SELECT id, order_number FROM orders;"],
            pitfalls=["Namen sind keine Schlüssel.", "order_number ist lesbar, id ist die Naht."],
            related=["foreign-key", "index"],
            lesson_id="ch-keys",
            cards=[
                card("pk-begriff", "begriff", "Was ist ein Primary Key?", "Ein Wert, der eine Zeile eindeutig identifiziert — hier meist id."),
                card("pk-wann", "wann", "Wonach joinest du Kunden an Aufträge?", "clients.id = orders.client_id, nicht über den Namen."),
                card("pk-fehler", "fehler", "Warum ist client = 'Helio' kein Schlüssel?", "Der Name kann doppelt vorkommen. Die id nicht."),
                card("pk-pred", "predict", "Welche id hat Westfeld?", "40."),
            ],
        ),
        article(
            "foreign-key",
            "Foreign Key",
            "verbinden",
            "Ein Foreign Key zeigt auf den Primary Key einer anderen Tabelle.",
            """
`orders.client_id` zeigt auf `clients.id`. So gehört ein Auftrag zu einem Kunden, ohne Name und Land in jede Auftragszeile zu kopieren.

`order_items.order_id` zeigt auf `orders.id`. Ein Auftrag, viele Positionen.

NULL im Foreign Key heißt: kein Ziel. 4730 hat `client_id` leer — kein Kunde, kein Fehler im JOIN-Wort, eine fachliche Lücke.
""",
            sql=["SELECT order_number, client_id FROM orders;", "SELECT order_id, sku FROM order_items;"],
            pitfalls=["Den Namen in orders zu speichern ist eine Kopie, kein Schlüssel.", "Ein leerer client_id ist erlaubt, wenn die Spalte NULL zulässt."],
            related=["primary-key", "join-inner", "order-items"],
            lesson_id="ch-keys",
            cards=[
                card("fk-begriff", "begriff", "Was ist ein Foreign Key?", "Eine Spalte, die auf den Primary Key einer anderen Tabelle zeigt."),
                card("fk-wann", "wann", "Welche Spalte hängt den Auftrag am Kunden?", "orders.client_id → clients.id."),
                card("fk-fehler", "fehler", "Warum kopiert man Land nicht in jede orders-Zeile?", "Land gehört zu clients. Sonst pflegst du es an zwei Stellen."),
                card("fk-pred", "predict", "Wohin zeigt order_items.order_id?", "Auf orders.id."),
            ],
        ),
        article(
            "join-inner",
            "INNER JOIN",
            "verbinden",
            "INNER JOIN behält nur Zeilen, die in beiden Tabellen zusammenpassen.",
            """
`FROM orders o JOIN clients c ON c.id = o.client_id` — kurz INNER JOIN. ON ist die Naht, nicht der fachliche Filter.

Auftrag 4730 hat keinen Kunden. Beim INNER JOIN **verschwindet** er. Wenn er bleiben soll, brauchst du LEFT JOIN.

Das Ergebnis kann mehr Zeilen haben als `orders`, sobald rechts mehrere Treffer passen — bei `order_items` zum Beispiel.
""",
            sql=[
                "SELECT o.order_number, c.name FROM orders o JOIN clients c ON c.id = o.client_id;",
                "SELECT o.order_number, c.country FROM orders o JOIN clients c ON c.id = o.client_id WHERE c.country = 'AT';",
            ],
            pitfalls=["ON ist die Naht. status = 'offen' gehört nach WHERE.", "INNER JOIN verwirft 4730."],
            related=["left-join", "alias", "foreign-key"],
            lesson_id="ch9",
            cards=[
                card("ij-begriff", "begriff", "Was behält INNER JOIN?", "Nur Paare. Fehlt rechts ein Treffer, fällt die linke Zeile weg."),
                card("ij-wann", "wann", "Wann INNER statt LEFT?", "Wenn Zeilen ohne Partner nicht erscheinen sollen — z. B. Kunden ohne offene Aufträge."),
                card("ij-fehler", "fehler", "Warum fehlt 4730 nach JOIN clients?", "Kein client_id, kein Paar, INNER JOIN wirft ihn."),
                card("ij-luecke", "luecke", "FROM orders o JOIN clients c ON ______", "c.id = o.client_id", "ON c.id = o.client_id"),
            ],
        ),
        article(
            "left-join",
            "LEFT JOIN",
            "verbinden",
            "LEFT JOIN behält alle Zeilen der linken Tabelle. Fehlt rechts ein Treffer, stehen dort NULL.",
            """
Was nicht verschwinden darf, gehört nach **links**. `FROM orders o LEFT JOIN clients c` behält jeden Auftrag. Bei 4730 ist `c.name` NULL.

Der Anti-Join: linke Seite behalten, rechte id prüfen. `FROM clients c LEFT JOIN orders o ON o.client_id = c.id WHERE o.id IS NULL` findet Westfeld.

Filter auf die **rechte** Tabelle in WHERE können einen LEFT JOIN faktisch zum INNER machen. `WHERE c.country = 'DE'` wirft 4730, weil country NULL ist. Solche Filter gehören in ON oder du akzeptierst INNER.
""",
            sql=[
                "SELECT o.order_number, c.name FROM orders o LEFT JOIN clients c ON c.id = o.client_id;",
                "SELECT c.name FROM clients c LEFT JOIN orders o ON o.client_id = c.id WHERE o.id IS NULL;",
            ],
            pitfalls=["WHERE auf rechte Spalten macht aus LEFT oft INNER.", "Rechts und links vertauschen ändert, wer überlebt."],
            related=["join-inner", "null", "coalesce", "right-full"],
            lesson_id="ch10",
            cards=[
                card("lj-begriff", "begriff", "Was behält LEFT JOIN?", "Alle Zeilen der linken Tabelle. Rechts NULL, wenn kein Treffer."),
                card("lj-wann", "wann", "Auftrag ohne Kunde soll bleiben — welcher JOIN?", "LEFT JOIN, Auftrag links."),
                card("lj-fehler", "fehler", "Warum wirft WHERE c.country = 'DE' den Auftrag 4730?", "c.country ist NULL. NULL = 'DE' ist nicht wahr."),
                card("lj-pred", "predict", "Wer ist der Kunde ohne Auftrag?", "Westfeld."),
            ],
        ),
        article(
            "right-full",
            "RIGHT JOIN und FULL JOIN",
            "verbinden",
            "RIGHT JOIN ist LEFT JOIN mit vertauschten Seiten. FULL JOIN behält beide Seiten. Nur Nachschlagen.",
            """
In dieser App schreiben wir RIGHT JOIN fast nie. Die führende Tabelle kommt nach links, dann LEFT JOIN.

`FULL OUTER JOIN` behält Zeilen, die nur links, nur rechts oder in beiden vorkommen. Unmatched Felder sind NULL. Für den Grundlagenpfad reicht LEFT plus Anti-Join.

Wenn ein Text „RIGHT JOIN“ sagt, dreh die Tabellen und schreib LEFT — dieselbe Menge.
""",
            sql=[
                "SELECT c.name, o.order_number FROM clients c LEFT JOIN orders o ON o.client_id = c.id;",
                "-- dasselbe wie RIGHT JOIN orders o … FROM clients, nur gedreht",
            ],
            pitfalls=["RIGHT JOIN ist kein anderer Fachfall, nur eine Schreibrichtung.", "FULL JOIN brauchst du im Lagerpfad nicht."],
            related=["left-join", "join-inner"],
            lookup_only=True,
            cards=[
                card("rf-begriff", "begriff", "Was ist RIGHT JOIN?", "LEFT JOIN mit vertauschter linker/rechter Tabelle."),
                card("rf-wann", "wann", "Wie vermeidest du RIGHT JOIN?", "Die Tabelle, die bleiben soll, nach links legen und LEFT JOIN schreiben."),
                card("rf-fehler", "fehler", "Ist FULL JOIN dasselbe wie INNER JOIN?", "Nein. FULL behält auch Zeilen ohne Partner auf beiden Seiten."),
                card("rf-pred", "predict", "RIGHT JOIN clients von orders aus — wer bleibt?", "Alle Kunden, Aufträge ohne Kunde fallen, wenn orders rechts liegt. Deshalb drehen wir lieber."),
            ],
        ),
        article(
            "mehrere-tabellen",
            "Mehrere Tabellen",
            "verbinden",
            "Drei Tabellen: Kopf, Partner, Positionen. Jede Naht hat ihr ON.",
            """
Typische Kette: `orders` → `clients` und `orders` → `order_items`. Du joinest nacheinander, jedes ON nur eine Beziehung.

`FROM orders o JOIN clients c ON c.id = o.client_id JOIN order_items i ON i.order_id = o.id`

Die Zeilenzahl wächst mit den Positionen. GROUP BY holt dich zurück auf „pro Auftrag“ oder „pro Kunde“.
""",
            sql=[
                "SELECT o.order_number, c.name, i.sku, i.qty FROM orders o JOIN clients c ON c.id = o.client_id JOIN order_items i ON i.order_id = o.id;",
                "SELECT c.name, SUM(i.qty) FROM orders o JOIN clients c ON c.id = o.client_id JOIN order_items i ON i.order_id = o.id GROUP BY c.name;",
            ],
            pitfalls=["Zwei Beziehungen in ein ON zwängen macht den Join unlesbar.", "Vergiss nicht: INNER wirft 4730 und Aufträge ohne Positionen."],
            related=["order-items", "join-inner", "group-by"],
            lesson_id="ch-items",
            cards=[
                card("mt-begriff", "begriff", "Wie joinest du drei Tabellen?", "Nacheinander, jedes Paar mit eigenem ON."),
                card("mt-wann", "wann", "Wann brauchst du orders plus items plus clients?", "Wenn Status oder Land und gleichzeitig sku/qty in einer Frage stecken."),
                card("mt-fehler", "fehler", "Warum explodiert die Zeilenzahl?", "Jede Position verdoppelt den Auftrag. Danach oft GROUP BY."),
                card("mt-luecke", "luecke", "JOIN order_items i ON ______", "i.order_id = o.id", "ON i.order_id = o.id"),
            ],
        ),
        article(
            "order-items",
            "order_items",
            "verbinden",
            "Positionen: ein Auftrag, viele Zeilen. sku und qty leben hier, nicht im Kopf.",
            """
`order_items` ist die 1:n-Tabelle zu `orders`. Spalten: `order_id`, `sku`, `qty`.

Auftrag 4730 hat keine Position. INNER JOIN auf items lässt ihn weg. SUM(qty) GROUP BY Auftrag addiert die Zeilen.

Artikel stecken nur hier. „Welche SKUs in offenen Aufträgen?“ braucht den Kopf für den Status und die Position für sku.
""",
            sql=[
                "SELECT o.order_number, i.sku, i.qty FROM orders o JOIN order_items i ON i.order_id = o.id;",
                "SELECT i.sku, SUM(i.qty) FROM order_items i JOIN orders o ON o.id = i.order_id WHERE o.status = 'offen' GROUP BY i.sku;",
            ],
            pitfalls=["qty in items ist nicht dasselbe wie orders.quantity.", "4730 in items suchen liefert nichts — das ist der Lehrfall."],
            related=["foreign-key", "join-inner", "sum"],
            lesson_id="ch-items",
            cards=[
                card("oi-begriff", "begriff", "Was steht in order_items?", "Die Positionen eines Auftrags: Artikel (sku) und Menge (qty)."),
                card("oi-wann", "wann", "Wann orders.quantity, wann items.qty?", "quantity am Kopf ist eine grobe Menge. qty ist die Zeile am Artikel."),
                card("oi-fehler", "fehler", "Welcher Auftrag hat keine Position?", "4730."),
                card("oi-pred", "predict", "Naht items → orders?", "order_items.order_id = orders.id."),
            ],
        ),
    ]
