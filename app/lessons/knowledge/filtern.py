from lessons.knowledge.schema import article, card


def articles():
    return [
        article(
            "where",
            "WHERE",
            "filtern",
            "WHERE prüft jede Zeile. Nur wenn die Bedingung wahr ist, bleibt die Zeile.",
            """
`WHERE` beantwortet: **Welche Datensätze?** Jede Zeile wird unabhängig geprüft. Text steht in einfachen Anführungszeichen: `status = 'offen'`.

`WHERE` läuft **vor** `GROUP BY`. Deshalb kannst du hier noch nicht `COUNT(*) > 4` schreiben — die Gruppen existieren noch nicht. Dafür ist `HAVING` da.

Mehrere Bedingungen verbindest du mit `AND` / `OR` / `NOT`. Klammern machen die Absicht sichtbar.
""",
            sql=["SELECT * FROM orders WHERE status = 'offen';", "SELECT * FROM orders WHERE client = 'Helio' AND status = 'offen';"],
            pitfalls=["Doppelte Anführungszeichen sind in Postgres Bezeichner, keine Texte.", "WHERE = NULL ist nie wahr. Nutze IS NULL."],
            related=["and-or", "null", "having", "vergleiche"],
            lesson_id="ch3",
            cards=[
                card("where-begriff", "begriff", "Wozu ist WHERE da?", "Es behält nur Zeilen, für die die Bedingung wahr ist."),
                card("where-wann", "wann", "Wohin kommt status = 'offen' — WHERE oder HAVING?", "WHERE. Status gehört zur Zeile, nicht zur Gruppe."),
                card("where-fehler", "fehler", "Was ist falsch an WHERE status = \"offen\"?", "Doppelte Anführungszeichen sind ein Name, kein Text. Einfache: 'offen'."),
                card("where-luecke", "luecke", "SELECT * FROM orders ______ status = 'offen';", "WHERE", "SELECT * FROM orders WHERE status = 'offen';"),
            ],
        ),
        article(
            "vergleiche",
            "Vergleiche",
            "filtern",
            "= gleich, != ungleich, >, <, >=, <=. Pro Zeile eine Ja/Nein-Frage.",
            """
Ein Vergleich liefert wahr oder nicht wahr. `quantity > 10` ist für 12 wahr, für 10 falsch, für NULL nicht wahr.

`>=` nimmt die Grenze mit, `>` nicht. `BETWEEN 10 AND 20` ist dasselbe wie `>= 10 AND <= 20`.

Zahlen ohne Anführungszeichen, Text mit. `status = offen` sucht eine Spalte namens offen — das ist fast immer falsch.
""",
            sql=["SELECT * FROM orders WHERE quantity > 10;", "SELECT * FROM stock WHERE weight >= 100;"],
            pitfalls=["NULL macht jeden Vergleich außer IS NULL unwahr.", "10 > 10 ist falsch. Grenze mitnehmen: >="],
            related=["where", "between", "null"],
            lesson_id="ch4",
            cards=[
                card("vgl-begriff", "begriff", "Was bedeutet >= 100?", "Mindestens 100 — die 100 zählt mit."),
                card("vgl-wann", "wann", "Wann != 'fertig'?", "Wenn offen und storniert bleiben sollen, fertig nicht."),
                card("vgl-fehler", "fehler", "Warum fehlt eine Zeile mit leerer quantity bei quantity > 10?", "NULL > 10 ist nicht wahr."),
                card("vgl-pred", "predict", "weight >= 100 im Bestand: welche Paletten?", "Palette A (120) und Palette D (100)."),
            ],
        ),
        article(
            "like",
            "LIKE",
            "filtern",
            "LIKE vergleicht Text mit einem Muster. % steht für beliebigen Rest, _ für ein Zeichen.",
            """
`item LIKE 'Palette%'` findet Palette A, Palette B, Palette G. `%` darf vorne, hinten oder beides stehen.

LIKE ist kein regulärer Ausdruck. Für echte Regex gibt es `~` — das brauchst du im Grundlagenpfad nicht.

Groß/Klein: Standard-LIKE in Postgres ist case-sensitive. `LIKE 'palette%'` findet „Palette“ nicht. `ILIKE` ignoriert die Großschreibung.
""",
            sql=["SELECT * FROM stock WHERE item LIKE 'Palette%';", "SELECT * FROM clients WHERE name ILIKE '%lin%';"],
            pitfalls=["% vergessen: LIKE 'Palette' sucht genau dieses Wort.", "LIKE ist kein Ersatz für = bei exakten Werten."],
            related=["where", "in"],
            lesson_id="ch4",
            cards=[
                card("like-begriff", "begriff", "Was bedeutet % in LIKE?", "Beliebig viele Zeichen, auch keines."),
                card("like-wann", "wann", "Wann LIKE statt =?", "Wenn nur ein Teil des Textes feststeht — beginnt mit Palette."),
                card("like-fehler", "fehler", "Warum findet LIKE 'palette%' die Palette A nicht?", "LIKE achtet auf Groß/Klein. ILIKE oder 'Palette%'."),
                card("like-luecke", "luecke", "item LIKE 'Palette___'", "% für den Rest.", "item LIKE 'Palette%';"),
            ],
        ),
        article(
            "in-liste",
            "IN",
            "filtern",
            "IN prüft, ob der Wert in einer Liste steht. Die Liste kann fest oder eine Unterabfrage sein.",
            """
`status IN ('offen', 'storniert')` ist klarer als langes OR.

Die Liste darf aus einer inneren SELECT kommen: `id IN (SELECT order_id FROM order_items)`. Dann ist IN eine Unterabfrage.

`NOT IN` wird unangenehm, sobald die innere Liste NULL enthält. Für „gibt es keine passende Zeile?“ ist `NOT EXISTS` oft der klarere Satz.
""",
            sql=["SELECT * FROM orders WHERE status IN ('offen', 'storniert');", "SELECT * FROM orders WHERE id IN (SELECT order_id FROM order_items);"],
            pitfalls=["IN () leere Liste ist in Postgres ein Fehler bzw. immer falsch.", "NOT IN plus NULL in der Liste liefert keine Treffer."],
            related=["where", "unterabfrage", "and-or"],
            lesson_id="ch4",
            cards=[
                card("in-begriff", "begriff", "Was macht IN ('offen', 'storniert')?", "Der Status muss einer der genannten Werte sein."),
                card("in-wann", "wann", "Wann IN statt OR?", "Bei mehr als einer erlaubten Konstante — die Liste bleibt lesbar."),
                card("in-fehler", "fehler", "Warum ist NOT IN (SELECT …) riskant?", "Kommt NULL in der inneren Liste vor, wird die Logik knifflig. NOT EXISTS ist robuster."),
                card("in-luecke", "luecke", "status ______ ('offen', 'fertig')", "IN", "status IN ('offen', 'fertig');"),
            ],
        ),
        article(
            "between",
            "BETWEEN",
            "filtern",
            "BETWEEN a AND b nimmt beide Grenzen mit. Für Zahlen und Daten.",
            """
`quantity BETWEEN 10 AND 20` heißt 10, 11, …, 20. Es ist inklusiv.

Die Reihenfolge ist von klein nach groß. `BETWEEN 20 AND 10` findet nichts Sinnvolles.

NULL liegt in keinem Bereich. Eine leere Menge ist nicht „zwischen 10 und 20“.
""",
            sql=["SELECT * FROM orders WHERE quantity BETWEEN 10 AND 20;", "SELECT * FROM orders WHERE created_at BETWEEN DATE '2026-09-10' AND DATE '2026-09-16';"],
            pitfalls=["BETWEEN ist inklusiv — 10 und 20 zählen.", "Für offene Intervalle bleib bei > und <."],
            related=["vergleiche", "where"],
            lesson_id="ch4",
            cards=[
                card("bet-begriff", "begriff", "Ist BETWEEN inklusiv?", "Ja. Beide Grenzen gehören dazu."),
                card("bet-wann", "wann", "Wann BETWEEN statt zwei Vergleichen?", "Wenn du einen geschlossenen Bereich meinst und das so lesen willst."),
                card("bet-fehler", "fehler", "Zählt quantity 10 bei BETWEEN 10 AND 20?", "Ja."),
                card("bet-pred", "predict", "NULL BETWEEN 10 AND 20?", "Nicht wahr. Die Zeile fällt weg."),
            ],
        ),
        article(
            "and-or",
            "AND / OR / NOT",
            "filtern",
            "AND: beide wahr. OR: eine reicht. NOT: dreht um. Klammern bei Mischung.",
            """
„Helio und offen“ ist `AND`. „Helio oder offen“ ist fast die ganze Tabelle — OR ist weit.

Mischst du AND und OR, setze Klammern: `(client = 'Helio' OR client = 'Alpin') AND status = 'offen'`.

`NOT` dreht eine Bedingung. `status != 'fertig'` und `NOT status = 'fertig'` meinen dasselbe; `!=` liest sich meist klarer.
""",
            sql=[
                "SELECT * FROM orders WHERE client = 'Helio' AND status = 'offen';",
                "SELECT * FROM orders WHERE client = 'Helio' OR status = 'offen';",
            ],
            pitfalls=["OR ohne Klammern neben AND wird leicht falsch gelesen.", "AND ist nicht „und dann sortieren“."],
            related=["where", "in-liste"],
            lesson_id="ch5",
            cards=[
                card("ao-begriff", "begriff", "Unterschied AND und OR?", "AND: beide Bedingungen. OR: eine genügt."),
                card("ao-wann", "wann", "Helio und offen — AND oder OR?", "AND. Beide müssen gleichzeitig stimmen."),
                card("ao-fehler", "fehler", "Was liefert Helio OR offen zu viel?", "Jedes offene von anderen Kunden und jedes Helio, auch fertig."),
                card("ao-luecke", "luecke", "client = 'Helio' ____ status = 'offen'", "AND", "client = 'Helio' AND status = 'offen';"),
            ],
        ),
        article(
            "null",
            "NULL",
            "filtern",
            "NULL heißt: kein Wert. Nicht 0, nicht leerer Text. Suchen mit IS NULL / IS NOT NULL.",
            """
In `orders` hat 4731 keine Menge, 4730 keinen Kunden. Das ist unbekannt, nicht null Euro und nicht „kein Name als Wort“.

`quantity = NULL` ist nie wahr. `quantity IS NULL` findet die Lücken. `IS NOT NULL` findet gesetzte Werte, 0 bleibt 0.

Vergleiche, SUM und AVG überspringen NULL. COUNT(*) zählt die Zeile trotzdem, COUNT(quantity) nicht.
""",
            sql=["SELECT * FROM orders WHERE quantity IS NULL;", "SELECT * FROM orders WHERE client_id IS NULL;"],
            pitfalls=["= NULL schreiben ist der Klassiker — immer IS NULL.", "0 ist ein Wert. NULL ist keiner."],
            related=["coalesce", "where", "sum"],
            lesson_id="ch7",
            cards=[
                card("null-begriff", "begriff", "Was bedeutet NULL?", "Kein Wert gesetzt. Nicht 0, nicht ''."),
                card("null-wann", "wann", "Wie findest du Aufträge ohne Menge?", "WHERE quantity IS NULL."),
                card("null-fehler", "fehler", "Was ist falsch an WHERE quantity = NULL?", "Der Vergleich ist nie wahr. IS NULL."),
                card("null-pred", "predict", "Welche Auftragsnummer hat keinen Kunden?", "4730."),
            ],
        ),
        article(
            "coalesce",
            "COALESCE",
            "filtern",
            "COALESCE nimmt den ersten Wert, der nicht NULL ist. Die Zeile bleibt, die Zelle wird lesbar.",
            """
`COALESCE(c.name, 'ohne Kunde')` nach einem LEFT JOIN macht aus der leeren Namenszelle einen Text. Auftrag 4730 bleibt in der Liste.

Du kannst mehrere Argumente ketten: `COALESCE(a, b, c, '—')`.

COALESCE filtert nicht. Wer die Zeile weghaben will, schreibt `WHERE c.name IS NOT NULL`.
""",
            sql=[
                "SELECT o.order_number, COALESCE(c.name, 'ohne Kunde') FROM orders o LEFT JOIN clients c ON c.id = o.client_id;",
                "SELECT item, COALESCE(quantity, 0) FROM stock;",
            ],
            pitfalls=["COALESCE ersetzt keinen LEFT JOIN — ohne Join gibt es c.name nicht.", "0 als Ersatz kann SUM verfälschen. Bewusst entscheiden."],
            related=["null", "left-join", "case"],
            lesson_id="ch-case",
            cards=[
                card("coa-begriff", "begriff", "Was macht COALESCE(x, y)?", "Es nimmt x, wenn x nicht NULL ist, sonst y."),
                card("coa-wann", "wann", "Wann COALESCE statt WHERE IS NOT NULL?", "Wenn die Zeile bleiben und die Lücke nur lesbar werden soll."),
                card("coa-fehler", "fehler", "Was steht bei 4730 ohne COALESCE im Namen?", "NULL — die Zelle ist leer."),
                card("coa-pred", "predict", "COALESCE(NULL, 'ohne Kunde')?", "ohne Kunde."),
            ],
        ),
    ]
