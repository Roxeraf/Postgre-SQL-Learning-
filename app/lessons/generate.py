# -*- coding: utf-8 -*-
"""Erzeugt lessons.json aus der Einarbeitungs-Dokumentation."""
import json
from pathlib import Path

LESSONS = []


def L(**kwargs):
    LESSONS.append(kwargs)


def EX(id, why, task, look, starter, hints, solution, **extra):
    data = {
        "id": id,
        "why": why,
        "task": task,
        "look": look,
        "prompt": task,
        "starter": starter,
        "hints": hints,
        "solution": solution,
    }
    data.update(extra)
    return data


# ---------------------------------------------------------------------------
L(
    id="sql",
    letter="SQL",
    track="einstieg",
    title="SQL-Grundlagen: SELECT und JOINs",
    minutes=14,
    goals=[
        "SELECT, FROM und WHERE als Gerüst einer Abfrage nutzen",
        "INNER JOIN und LEFT JOIN unterscheiden",
        "NULL nach einem JOIN als fehlenden Treffer lesen",
    ],
    content="""## Was ist eine Abfrage?

Eine SQL-Abfrage fragt Tabellen. Drei Bausteine reichen für den Start:

- **SELECT** — welche Spalten willst du sehen?
- **FROM** — aus welcher Tabelle?
- **WHERE** — welche Zeilen behalten? (ohne WHERE kommen alle Zeilen)

```sql
SELECT order_number, task_status
FROM instance_1.flowapp_demo_order_head
WHERE order_number = '100504_A';
```

In dieser App stehen die Tabellen immer voll qualifiziert: `instance_1.flowapp_demo_…`. Rechts im Übungsteil siehst du den deutschen Namen (**Auftrag**) und darunter den technischen (`order_head`).

## INNER JOIN

Ein **INNER JOIN** behält nur Zeilen, die **in beiden Tabellen** einen Treffer haben.

Auftrag ohne Position? Fliegt raus. Position ohne Auftrag? Fliegt raus.

```sql
SELECT oh.order_number, op.quantity
FROM instance_1.flowapp_demo_order_head oh
INNER JOIN instance_1.flowapp_demo_order_position op
  ON op.order_head_id = oh.id;
```

`ON` sagt, *worüber* die Tabellen zusammengehören. Hier: die Position hängt am Auftrag (`order_head_id` = `oh.id`).

In der Übungs-DB haben nur drei Aufträge Positionen — INNER JOIN liefert also drei Zeilen. `JOIN` ohne Wort davor ist dasselbe wie `INNER JOIN`.

## LEFT JOIN

**LEFT JOIN** (ausgeschrieben **LEFT OUTER JOIN**) behält **alle Zeilen der linken Tabelle**. Fehlt rechts ein Treffer, stehen dort **NULL**.

```sql
SELECT oh.order_number, op.quantity
FROM instance_1.flowapp_demo_order_head oh
LEFT JOIN instance_1.flowapp_demo_order_position op
  ON op.order_head_id = oh.id;
```

Dieselbe Verknüpfung wie eben — aber jetzt bleiben Aufträge ohne Position in der Liste, `quantity` ist dann leer. In der Übungs-DB: sieben Aufträge, vier davon ohne Position.

Im Lageralltag: Auftragsliste mit Mandant, auch wenn `client_id` fehlt. Deshalb steht bei uns fast immer **LEFT JOIN**.

## RIGHT und FULL JOIN

**RIGHT OUTER JOIN** ist LEFT JOIN mit vertauschten Tabellen: alle Zeilen **rechts** bleiben. Bei uns liegt der Auftrag üblicherweise links — dann schreibst du LEFT JOIN, nicht RIGHT.

**FULL OUTER JOIN** behält Zeilen **beider** Seiten, auch ohne Treffer. Mandant `DEMO` hat in der Übungs-DB keinen Auftrag: ein FULL JOIN Auftrag/Mandant würde ihn trotzdem zeigen. Im Shop selten nötig; wenn, dann für Abgleiche („was hängt nirgends?“).

## Welchen JOIN wann?

Sprache aus dem Lager: **Auftrag**, **Mandant**, **Position**.

| Ziel | JOIN |
|---|---|
| Nur Aufträge, die wirklich Positionen haben | **INNER JOIN** |
| Alle Aufträge, Lücken sichtbar lassen | **LEFT JOIN** Auftrag → Position |
| Auftrag plus Mandant, Auftrag darf nicht verschwinden | **LEFT JOIN** Auftrag → Mandant |
| Zwei Listen vollständig gegeneinander halten | **FULL OUTER JOIN** (selten) |

Faustregel: Was darf nicht verloren gehen? Das gehört **nach links**, dann LEFT JOIN.

## NULL nach dem JOIN

NULL heißt hier: **kein Treffer**, nicht die Zahl 0.

- `quantity IS NULL` — dieser Auftrag hat keine Position.
- `quantity = 0` — findet diese Lücken **nicht** (NULL ist nicht 0).
- `c.code IS NULL` — dieser Auftrag hat keinen Mandanten.

Die Zeile links existiert. Rechts ist die Zelle leer. Genau das willst du sehen, wenn du mit LEFT JOIN nach fehlenden Daten suchst.

JOIN-Arten sitzen jetzt. Teil A nimmt Postgres-Eigenheiten (Schema, UUID, Window Functions).""",
    exercises=[
        EX(
            "sql-ex1",
            why="Bevor Joins kommen: eine Zeile gezielt finden.",
            task="Gib Auftragsnummer und Status für den Auftrag 100504_A aus.",
            look=[
                "Rechts „Auftrag“ (order_head) öffnen.",
                "SELECT: order_number und task_status.",
                "WHERE filtert auf genau diese Auftragsnummer.",
            ],
            starter="-- Eine Zeile: Auftrag 100504_A.\n-- Rechts: Tabelle „Auftrag“.\n\nSELECT\n  -- Spalten einsetzen\n  \nFROM instance_1.flowapp_demo_order_head\nWHERE\n",
            hints=[
                "SELECT order_number, task_status — beide Spalten stehen rechts bei Auftrag.",
                "WHERE order_number = '100504_A' — Text in einfachen Anführungszeichen.",
            ],
            solution="SELECT order_number, task_status FROM instance_1.flowapp_demo_order_head WHERE order_number = '100504_A';",
        ),
        EX(
            "sql-ex2",
            why="Nur Aufträge, die wirklich Positionen haben — der Rest soll nicht in der Liste stehen.",
            task="Verknüpfe Auftrag und Position per INNER JOIN. Gib Auftragsnummer und Menge aus.",
            look=[
                "SELECT: oh.order_number und op.quantity.",
                "ON op.order_head_id = oh.id — die Position hängt am Auftrag.",
            ],
            starter="-- Nur Treffer in beiden Tabellen.\n-- Rechts: „Auftrag“ und „Position“ (hängt am Auftrag).\n\nSELECT\n  \nFROM instance_1.flowapp_demo_order_head oh\nINNER JOIN instance_1.flowapp_demo_order_position op\n  ON \n",
            hints=[
                "SELECT oh.order_number, op.quantity — Alias oh und op stehen schon im FROM.",
                "ON op.order_head_id = oh.id — nicht order_id (integer) mit id (UUID) mischen.",
            ],
            solution="SELECT oh.order_number, op.quantity FROM instance_1.flowapp_demo_order_head oh INNER JOIN instance_1.flowapp_demo_order_position op ON op.order_head_id = oh.id;",
        ),
        EX(
            "sql-ex3",
            why="Dieselbe Liste, aber Aufträge ohne Position sollen bleiben — Menge dann leer (NULL).",
            task="Verknüpfe Auftrag und Position per LEFT JOIN. Gib Auftragsnummer und Menge aus.",
            look=[
                "Gleicher SELECT wie eben: oh.order_number, op.quantity.",
                "ON bleibt op.order_head_id = oh.id. LEFT statt INNER hält Aufträge ohne Position.",
            ],
            starter="-- Alle Aufträge, auch ohne Position.\n-- Rechts: „Auftrag“ und „Position“.\n\nSELECT\n  \nFROM instance_1.flowapp_demo_order_head oh\nLEFT JOIN instance_1.flowapp_demo_order_position op\n  ON \n",
            hints=[
                "SELECT oh.order_number, op.quantity",
                "ON op.order_head_id = oh.id — wer LEFT durch INNER ersetzt, verliert die Aufträge ohne Position.",
            ],
            solution="SELECT oh.order_number, op.quantity FROM instance_1.flowapp_demo_order_head oh LEFT JOIN instance_1.flowapp_demo_order_position op ON op.order_head_id = oh.id;",
        ),
    ],
    quiz=[
        {
            "q": "Was bleibt bei einem INNER JOIN Auftrag → Position übrig?",
            "options": [
                "Alle Aufträge, Positionen ohne Treffer als NULL",
                "Nur Aufträge, die mindestens eine Position haben",
                "Alle Positionen, auch ohne Auftrag",
                "Immer genau eine Zeile",
            ],
            "correct": 1,
            "explain": "INNER JOIN behält nur Zeilen mit Treffer in beiden Tabellen. Auftrag ohne Position fliegt raus.",
        },
        {
            "q": "Was bedeutet NULL in der Spalte der rechten Tabelle nach einem LEFT JOIN?",
            "options": [
                "Die Menge ist 0",
                "Die Zeile ist gelöscht",
                "Links gab es keine passende Zeile rechts",
                "Der JOIN ist fehlgeschlagen und muss wiederholt werden",
            ],
            "correct": 2,
            "explain": "Die linke Zeile bleibt. Rechts war kein Treffer — die Zelle ist leer (NULL), nicht 0.",
        },
        {
            "q": "Du willst alle Aufträge sehen, auch ohne Mandant. Welcher JOIN?",
            "options": [
                "INNER JOIN",
                "LEFT JOIN, Auftrag links",
                "RIGHT JOIN, Mandant links",
                "FULL JOIN ist die einzige Möglichkeit",
            ],
            "correct": 1,
            "explain": "Was nicht verloren gehen darf, gehört nach links: LEFT JOIN Auftrag → Mandant. So bleibt der Auftrag, Mandanten-Spalten werden NULL.",
        },
        {
            "q": "Warum schreiben wir im Shop selten RIGHT JOIN?",
            "options": [
                "Postgres kennt kein RIGHT JOIN",
                "RIGHT JOIN liefert immer 0 Zeilen",
                "Wir legen die führende Tabelle nach links und schreiben LEFT JOIN",
                "RIGHT JOIN ignoriert die ON-Bedingung",
            ],
            "correct": 2,
            "explain": "RIGHT JOIN ist LEFT JOIN mit vertauschten Seiten. Üblich: Auftrag links, dann LEFT JOIN.",
        },
    ],
    flashcards=[
        {"id": "sql-fc1", "front": "SELECT / FROM / WHERE?", "back": "SELECT = Spalten, FROM = Tabelle, WHERE = Filter. Ohne WHERE kommen alle Zeilen."},
        {"id": "sql-fc2", "front": "INNER JOIN", "back": "Nur Zeilen mit Treffer in beiden Tabellen. JOIN ohne Zusatzwort ist INNER JOIN."},
        {"id": "sql-fc3", "front": "LEFT JOIN", "back": "Alle Zeilen links bleiben. Kein Treffer rechts → NULL. Bei uns die übliche Form (Auftrag links)."},
        {"id": "sql-fc4", "front": "NULL nach einem JOIN", "back": "Kein Treffer, nicht die Zahl 0. Suchen mit IS NULL, nicht mit = 0."},
    ],
)

L(
    id="a",
    letter="A",
    track="einstieg",
    title="PostgreSQL Grundlagen",
    minutes=12,
    goals=[
        "Schema vs. Tabelle vs. vollqualifizierter Name unterscheiden",
        "UUID- vs. Integer-Schlüssel nicht durcheinander joinen",
        "Window Functions und CTEs als Standardwerkzeuge nutzen",
    ],
    content="""## A.1 Was ist PostgreSQL?

PostgreSQL ("Postgres") ist ein relationales Datenbanksystem (RDBMS). Daten stehen in Tabellen mit fest definierten Spalten. Tabellen werden über Primary Keys / Foreign Keys verknüpft, abgefragt wird mit SQL (Structured Query Language).

Wichtig für uns: Postgres kann zusätzlich **JSON/JSONB**, **Window Functions** und **CTEs (WITH)** — das nutzen wir in FlowApp intensiv.

## A.2 Datenbank, Schema, Tabelle

- Eine Instanz kann mehrere Datenbanken enthalten.
- Eine Datenbank enthält mehrere Schemas (Namensräume) — bei uns z. B. das Schema der Instanz (`instance_1`) und ein separates Schema `subscription` für Print-Subscriptions.
- Ein Schema enthält die eigentlichen Tabellen.

Tabellen werden bei uns **immer voll qualifiziert** angesprochen: `instance_1.flowapp_demo_<tabellenname>` (siehe Teil B).

> **Merke:** Ohne `instance_1.` sucht Postgres im falschen Schema und findet die Tabelle nicht. Im Übungsteil siehst du den deutschen Namen (**Auftrag**) und darunter den technischen (`order_head`).

Komplette Beispielabfrage — so sieht eine erste Liste aus:

```sql
SELECT order_number, task_status
FROM instance_1.flowapp_demo_order_head;
```

## A.3 Wichtige Datentypen

| Datentyp | Bedeutung | Hinweis |
|---|---|---|
| integer / bigint | Ganzzahl | z. B. lesbare Order-Nummer `order_id` |
| uuid | Universally Unique Identifier | Primärschlüssel vieler Tabellen (`id`) |
| varchar / text | Zeichenketten | z. B. Statuscodes wie `task_state` |
| timestamptz | Zeitstempel MIT Zeitzone (i. d. R. UTC) | braucht Konvertierung, siehe Teil E |
| timestamp (ohne tz) | Zeitstempel OHNE Zeitzone | bei uns bereits lokale Zeit |
| jsonb | binäres JSON, indexierbar | z. B. `name->>'de'` |
| boolean | Wahr/Falsch | — |

## A.4 JOINs in dieser Datenbank

JOIN-Arten (INNER, LEFT, RIGHT, FULL) und NULL bei fehlendem Treffer stehen in den [SQL-Grundlagen](/lesson/sql). Hier die FlowApp-Falle:

**Datentypen müssen zusammenpassen.** `integer = uuid` führt zum Laufzeitfehler — häufig, weil manche Felder integer sind (z. B. `order_id`) und der Primärschlüssel UUID (`order_head.id`). Die Verknüpfung geht über `ON … = …`, oft UUID (`id`) oder fachliche Referenzfelder (Teil D.4).

Auftrag mit Mandant — LEFT JOIN, damit der Auftrag bleibt, falls `client_id` fehlt (in der Übungs-DB hat jeder Auftrag einen Mandanten, INNER und LEFT sind hier gleich):

```sql
SELECT oh.order_number, c.code
FROM instance_1.flowapp_demo_order_head oh
LEFT JOIN instance_1.flowapp_demo_client c
  ON c.id = oh.client_id;
```

## A.5 Primary Keys & Foreign Keys

PK: eindeutiger Schlüssel pro Zeile (meist `id` als UUID). FK: Verweis auf den PK einer anderen Tabelle.

**Besonderheit bei uns:** FK-Constraints sind größtenteils **NICHT** technisch erzwungen. Referentielle Integrität wird nicht automatisch garantiert — vor jeder Änderung selbst prüfen, welche Kind-Tabellen abhängig sind.

## A.6 Window Functions

Berechnen Werte über eine Gruppe von Zeilen, ohne sie wie bei `GROUP BY` zusammenzufassen. Wir nutzen das oft zur Deduplizierung:

```sql
ROW_NUMBER() OVER (PARTITION BY <schlüssel_spalte> ORDER BY <datum_spalte> DESC) AS rn
-- anschließend: WHERE rn = 1
```

Damit holt man z. B. pro Handling Unit immer nur den neuesten Qualifikations-Datensatz.

## A.7 CTEs — WITH-Klausel

```sql
WITH basis AS (
  SELECT ...
)
SELECT * FROM basis WHERE ...;
```

In Metabase werden einmal referenzierte CTEs automatisch inline eingebaut. Bei Performance-Problemen: `WITH basis AS MATERIALIZED (...)`.

## A.8 Transaktionen

`BEGIN` / `COMMIT` / `ROLLBACK` fassen mehrere Anweisungen zu einer Einheit zusammen. Pflicht bei jeder datenverändernden Aktion — siehe das Sicherheitsmuster in Teil G.

## A.9 Views

Eine View ist eine gespeicherte SELECT-Abfrage. Views übernehmen **nicht automatisch** neue Spalten der Basistabelle — nach Erweiterung muss die View per `CREATE OR REPLACE VIEW ...` angepasst werden.""",
    exercises=[
        EX(
            "a-ex1",
            why="Ein Kollege braucht eine einfache Auftragsliste: Nummer und Status, sonst nichts.",
            task="Lies aus der Tabelle Auftrag die Auftragsnummer und den Status.",
            look=[
                "Rechts im Schema „Auftrag“ öffnen (technisch: order_head).",
                "Die Spalten order_number und task_status anklicken — sie landen in der SELECT-Liste.",
                "FROM ist schon vorbereitet. Du trägst nur die zwei Spalten nach SELECT ein.",
            ],
            starter="-- Alltag: Auftragsliste für einen Kollegen.\n-- Rechts: Tabelle „Auftrag“ aufklappen.\n\nSELECT\n  -- hier die zwei Spalten aus dem Schema einsetzen\n  \nFROM instance_1.flowapp_demo_order_head;\n",
            hints=[
                "Rechts bei Auftrag siehst du order_number (Auftragsnummer) und task_status (Status). Kein JOIN nötig.",
                "SELECT order_number, task_status FROM instance_1.flowapp_demo_order_head;",
            ],
            solution="SELECT order_number, task_status FROM instance_1.flowapp_demo_order_head;",
        ),
        EX(
            "a-ex2",
            why="Dieselbe Liste, aber der Kollege will auch den Mandanten sehen.",
            task="Verknüpfe Auftrag mit Mandant und gib Auftragsnummer plus Mandanten-Code aus.",
            look=[
                "JOIN-Arten wie in den SQL-Grundlagen. Hier: LEFT JOIN Auftrag → Mandant.",
                "SELECT: oh.order_number und c.code.",
                "ON c.id = oh.client_id — der JOIN fehlt noch.",
            ],
            starter="-- SELECT-Liste und JOIN-Bedingung ergänzen.\n\nSELECT\n  \nFROM instance_1.flowapp_demo_order_head oh\nLEFT JOIN instance_1.flowapp_demo_client c\n  ON \n",
            hints=[
                "SELECT oh.order_number, c.code — Alias oh und c stehen schon im FROM.",
                "ON c.id = oh.client_id — nicht client_id mit code verwechseln.",
            ],
            solution="SELECT oh.order_number, c.code FROM instance_1.flowapp_demo_order_head oh LEFT JOIN instance_1.flowapp_demo_client c ON c.id = oh.client_id;",
        ),
        EX(
            "a-ex3",
            why="Bestand (Quant) hat oft mehrere Zeilen pro HU-Position. Für Reports willst du nur die neueste.",
            task="Pro handling_unit_position_id nur den neuesten Quant behalten und handling_unit_position_id, batch_a, updated_date ausgeben.",
            look=[
                "Rechts „Quant“ (stock_quant) öffnen: handling_unit_position_id, batch_a, updated_date.",
                "Das Muster aus A.6/A.7: ROW_NUMBER in einer CTE, außen WHERE rn = 1.",
                "PARTITION BY die Positions-ID, ORDER BY updated_date DESC (neueste zuerst).",
            ],
            starter="-- Nur den neuesten Quant je HU-Position.\n-- Rechts: Tabelle „Quant“.\n\nWITH ranked AS (\n  SELECT\n    handling_unit_position_id,\n    batch_a,\n    updated_date,\n    ROW_NUMBER() OVER (\n      PARTITION BY handling_unit_position_id\n      ORDER BY updated_date DESC\n    ) AS rn\n  FROM instance_1.flowapp_demo_stock_quant\n)\nSELECT\n  -- die drei Spalten, nur wo rn = 1\n  \nFROM ranked\nWHERE\n",
            hints=[
                "Außen dieselben drei Spalten wie in der CTE: handling_unit_position_id, batch_a, updated_date.",
                "WHERE rn = 1 filtert auf die neueste Zeile je Position.",
            ],
            solution="WITH ranked AS (SELECT handling_unit_position_id, batch_a, updated_date, ROW_NUMBER() OVER (PARTITION BY handling_unit_position_id ORDER BY updated_date DESC) AS rn FROM instance_1.flowapp_demo_stock_quant) SELECT handling_unit_position_id, batch_a, updated_date FROM ranked WHERE rn = 1;",
        ),
    ],
)

L(
    id="b",
    letter="B",
    track="einstieg",
    title="Unsere Systemumgebung",
    minutes=8,
    goals=[
        "Tabellen immer als instance_1.flowapp_demo_… ansprechen",
        "subscription als separates Schema für Print kennen",
        "Mandanten früh filtern und Read-Replica-Abbrüche einordnen",
    ],
    content="""## B.1 Überblick FlowApp/WMX

Wir arbeiten in einer technischen Implementierungs- und Support-Rolle für das Lagerverwaltungssystem FlowApp/WMX. Die Arbeit umfasst SQL-basierte operative Analysen, Datenkorrekturen, Konfigurationsmigrationen und kundenseitiges Reporting — hauptsächlich über Metabase-Dashboards auf einer PostgreSQL-Datenbank.

## B.2 Instanz & Schema

- Instanz: `instance_1`
- Tabellen-Präfix in dieser Lern-DB: `flowapp_demo_`
- Jede Tabelle wird **immer voll qualifiziert** angesprochen:

```sql
instance_1.flowapp_demo_<tabellenname>
-- Beispiel:
SELECT * FROM instance_1.flowapp_demo_order_head;
```

> **Merke:** In der echten Umgebung steht statt `demo` ein Kunden-Hash. Das Muster bleibt gleich: Schema + Präfix + Tabellenname. Hier heißt das Präfix absichtlich `flowapp_demo_`, damit du es lesen kannst.

Die Print-/Ausgabekonfiguration liegt in einem **separaten Schema** `subscription`, NICHT in `instance_1` (z. B. `subscription.processevents_*` für Drucker-Umgebungen).

## B.3 Read Replica (Hot Standby)

Für Reporting nutzen wir eine Lesekopie der DB. Lang laufende Abfragen können mit *"canceling statement due to conflict with recovery"* abbrechen, wenn auf dem Primary parallel Änderungen repliziert werden.

Gegenmaßnahmen:

- Abfragen schlank halten (Filter früh, unnötige Joins vermeiden).
- Komplexe CTEs ggf. `AS MATERIALIZED`.
- Bei wiederholten Abbrüchen kleinere Zeiträume wählen oder Kollegen informieren.

## B.4 Multi-Tenant-Prinzip (Mandanten)

Das System ist multi-tenant-fähig: Jeder Kunde wird als eigener Mandant (`client`) abgebildet, mit eigenem Datenbestand in derselben Datenbank. Fast jede fachliche Tabelle trägt direkt oder indirekt einen Mandantenbezug — über `client_id` oder über eine übergeordnete Tabelle.

Für die tägliche Arbeit: Bei praktisch jeder Abfrage über mehrere Mandanten hinweg **früh auf den Mandanten filtern** — wegen Index-Nutzung und damit Daten nicht vermischt werden.

In dieser Lern-Datenbank liegen sechs Übungs-Mandanten: `NORD`, `SUED`, `WEST`, `OST`, `ZENTRAL`, `DEMO`. Das sind erfundene Beispieldaten — keine echten Kunden.""",
    quiz=[
        {"q": "Wie lautet die korrekte, voll qualifizierte Ansprache einer Tabelle bei uns?", "options": ["order_head", "flowapp_demo_order_head", "instance_1.flowapp_demo_order_head", "instance_1.order_head"], "correct": 2, "explain": "Immer Schema + Präfix + Tabellenname. Ohne instance_1 sucht Postgres im search_path (meist public) und findet nichts."},
        {"q": "In welchem Schema liegen die Print-Subscription-Tabellen?", "options": ["instance_1", "subscription", "flowapp_demo_print", "public"], "correct": 1, "explain": "Print liegt bewusst nicht in instance_1, sondern im Schema subscription (z. B. processevents_*)."},
        {"q": "Was ist eine typische Fehlermeldung bei zu lang laufenden Abfragen gegen die Read Replica?", "options": ["syntax error at or near SELECT", "canceling statement due to conflict with recovery", "relation does not exist", "permission denied for schema"], "correct": 1, "explain": "Die Replica bricht ab, wenn Recovery mit deiner langen Query kollidiert. Schlanker machen oder Zeitraum verkleinern."},
        {"q": "Warum filtert man Abfragen früh auf den Mandanten?", "options": ["Postgres verlangt das zwingend", "Index-Nutzung und kein Vermischen von Kundendaten", "Sonst fehlen JSONB-Felder", "Nur für Metabase Field Filters"], "correct": 1, "explain": "Multi-Tenant: fast jede fachliche Tabelle hängt direkt oder indirekt an einem client. Früher Filter ist Performance und Sicherheit."},
    ],
)

L(
    id="c",
    letter="C",
    track="einstieg",
    title="Werkzeuge (DBeaver & Metabase)",
    minutes=8,
    goals=[
        "DBeaver als Entwicklungs-Client vs. Metabase als Dashboard-Schicht trennen",
        "Field-Filter-Regeln (unaliaster Tabellenname, keine Checkboxen) anwenden",
        "Schema-CSV und FK/PK-Excel gezielt einsetzen",
    ],
    content="""## C.1 DBeaver

DBeaver ist unser primärer SQL-Client: hier entwickelt man neue Abfragen, testet Datenkorrekturen und exploriert das Schema.

**Verbindung zur echten Umgebung** bekommst du intern — Host, Datenbank und User stehen dann in den Zugangsdaten, nicht in dieser Lern-App.

Alle Übungen zu dieser Einarbeitung machst du **hier in der App** (Lektionen und SQL-Playground), inklusive UPDATE/DELETE.

## C.2 Metabase

Metabase ist unsere BI-Oberfläche für Dashboards auf Basis von SQL-Fragen mit Filtervariablen.

- **Field Filters** brauchen den unaliasten, vollen Tabellennamen im JOIN: `JOIN flowapp_demo_client ON flowapp_demo_client.id = ...`
- JSONB-Ausdrücke, CASE-Ergebnisse und berechnete Spalten können **keine** Field Filters nutzen — stattdessen Text-Variablen mit `ILIKE concat('%', {{variable}}, '%')`.
- Plain `timestamptz`-Spalten unterstützen Field Filters, auch mit Zeitzonen-Anzeige.
- Berechnete Spalten (Dwell Time, Status-CASE) brauchen `{{variable}}`.
- Optionale Filter: `[[AND ...]]` — Variable auf "Required = Nein".
- Ja/Nein-Filter als Text-Variable mit `'ja'`/`'nein'`.
- **Checkbox-Variablen nicht verwenden** — sie erzeugen "missing parameter"-Fehler.
- Einmal referenzierte CTEs werden automatisch inline gebaut; bei Last `AS MATERIALIZED`.

## C.3 Referenzdateien für die Schemasuche

Vor jeder neuen Abfrage immer zuerst die Spaltennamen prüfen:

- **Datenprofil / Schema-CSV** mit deutschen Bezeichnungen und technischen Tabellennamen — so findest du z. B. „Auftrag“ = `order_head`.
- **FK/PK-Excel** (Tabellenblatt "Abfrageergebnis") — für strukturelle Fremdschlüssel-Analyse, auch tatsächliche (nicht erzwungene) Beziehungen.

In dieser App ersetzt der **Schema-Bereich rechts** auf dem Tab „Üben“ beides für die Übungsdatenbank: deutscher Name, Eltern-Profil, Spalten, Vorschau der ersten Zeilen.""",
    quiz=[
        {"q": "Was brauchen Metabase Field Filters im JOIN?", "options": ["Ein Alias reicht", "Den unaliasten, vollen Tabellennamen", "Nur die Spalte, keine Tabelle", "Ein CASE-Statement"], "correct": 1, "explain": "Metabase bindet Field Filters an den echten Tabellennamen. Alias wie c.id funktioniert dafür nicht."},
        {"q": "Warum sollte man Checkbox-Variablen in Metabase vermeiden?", "options": ["Sie sind langsam", "Sie erzeugen 'missing parameter'-Fehler", "Sie unterstützen kein JSONB", "Sie sind veraltet"], "correct": 1, "explain": "Checkboxen führen bei uns regelmäßig zu missing-parameter-Fehlern. Ja/Nein als Text-Variable abbilden."},
        {"q": "Welche Datei dokumentiert auch tatsächliche, nicht technisch erzwungene FK-Beziehungen?", "options": ["Schema-CSV", "FK/PK-Excel-Datei", "Metabase-Export", "pg_constraint-Dump"], "correct": 1, "explain": "Die Schema-CSV kennt nur Spalten. Fachliche (nicht erzwungene) Beziehungen stehen in der FK/PK-Excel."},
    ],
)

L(
    id="d",
    letter="D",
    track="einstieg",
    title="Datenmodell: Die wichtigsten Konzepte",
    minutes=14,
    goals=[
        "JSONB-Texte mit ->> 'de' lesen",
        "item_master über parent_id dem Mandanten zuordnen",
        "Referenzketten Auftrag ↔ Task ↔ HU nachvollziehen",
    ],
    content="""## D.1 Mehrsprachige Felder (JSONB)

Übersetzungstabellen (`*_translation`) wurden entfernt. Mehrsprachige Texte liegen als JSONB in der Haupttabelle. Den deutschen Text holst du mit `->>'de'`.

Im Schema: **Artikelstamm** (`item_master`) — die Spalte heißt `designation_a` (nicht `designation`). **Mandant** (`client`) hat `name`.

Komplette Beispielabfrage — deutsche Artikelbezeichnung plus Mandanten-Code:

```sql
SELECT
  im.designation_a->>'de' AS bezeichnung,
  c.code AS mandant
FROM instance_1.flowapp_demo_item_master im
JOIN instance_1.flowapp_demo_client c
  ON im.parent_id = c.accounting_area_item_master_id;
```

Alte Abfragen können noch `*_translation` + `language = 'de'` nutzen — siehe Teil K.8. Für **neue** Abfragen gilt JSONB.

## D.2 Artikelstamm & Mandant

`item_master` hat **keine** Spalte `client_id`. Im Datenprofil hängt der Artikelstamm am **Buchungskreis Artikelstamm**, nicht direkt am Mandanten.

Deshalb der Join über:

```sql
item_master.parent_id = client.accounting_area_item_master_id
```

Die Artikelgruppe kann aus zwei Quellen kommen — immer mit `COALESCE` kombinieren:

```sql
COALESCE(im.item_group, ic.designation->>'de')
-- im = Artikelstamm, ic = Kategorie (Artikel), über cat_item_group_id
```

## D.3 Zonen-Zuordnung (Zonierung)

Die Tabelle **Zonierung** (`order_consolidation`) speichert **nicht** den Auftragskopf, sondern Zonen-Einträge (eine Zeile pro Auftrag + Zonentyp). Im Datenprofil: Eltern = Auftrag. Verknüpfung: `order_consolidation.parent_id = order_head.id` (UUID, nicht die lesbare Nummer).

`consolidation_type` ist ein varchar-Zahlencode:

| Code | Zonentyp |
|---|---|
| 1 | Wareneingangszone |
| 2 | Merging-Zone |
| 3 | Packzone |
| 4 | Versandbereitstellungszone |
| 5 | Warenausgangszone |
| 6 | Verladezone |

Komplettes Beispiel für die lesbare Auftragsnummer 100501:

```sql
SELECT oc.consolidation_type
FROM instance_1.flowapp_demo_order_head oh
JOIN instance_1.flowapp_demo_order_consolidation oc
  ON oc.parent_id = oh.id
WHERE oh.order_id = 100501;
```

## D.4 Referenzketten & Auftragsnummern

**Auftrag → Vorgang (Task):** `order_head.order_id` (integer) → `task_position_reference.reference_value` (Filter `reference_key = '#X.order-id'` oder `'#X.order-number'`, `source_slug_name = 'order-head'`) → `task_position.id` → `task_head.id`

**Handling Unit → Auftrag (Standardweg):** `handling_unit_position` → `handling_unit_position_reference` (Filter `source_slug_name = 'order-position'`, `reference_key = '#X.order-id-pos'`) → `order_position_reference` → `order_position` → `order_head`

**Handling Unit → Auftrag (alternativ):** `handling_unit_position_reference` mit `reference_link = 'product-outgoing-order'` verweist über `related_id` direkt auf `order_position.id`.

Auftragsnummern vergleichen — Suffixe wie `_A` stören. Komplettes Beispiel:

```sql
SELECT
  split_part(order_number, '_', 1) AS order_number_norm,
  order_id
FROM instance_1.flowapp_demo_order_head;
```

**Weitere Hinweise:**

- Deduplizierung von Bestands-Qualifikationen: `ROW_NUMBER() OVER (PARTITION BY hup.id ORDER BY qsq.updated_date DESC)` und `WHERE rn = 1`.
- `sink_handling_unit` / `source_handling_unit` sind Integer-Felder → referenzieren `handling_unit.handling_unit_id` (**nicht** die UUID-Spalte `id`).
- `order_head.order_id` = lesbare Nummer, `order_head.id` = UUID-Primärschlüssel — nicht verwechseln!""",
    exercises=[
        EX(
            "d-ex1",
            why="Support fragt: Welche Artikel gehören zu welchem Mandanten? Am Artikelstamm gibt es keine client_id.",
            task="Gib die deutsche Artikelbezeichnung und den Mandanten-Code aus.",
            look=[
                "SELECT: deutscher Text — im.designation_a->>'de' (die Spalte heißt designation_a).",
                "Dazu: c.code für den Mandanten.",
                "Der Join steht schon da (parent_id, nicht client_id).",
            ],
            starter="-- Deutsche Bezeichnung und Mandanten-Code. Join ist schon da.\n\nSELECT\n  \nFROM instance_1.flowapp_demo_item_master im\nJOIN instance_1.flowapp_demo_client c\n  ON im.parent_id = c.accounting_area_item_master_id;\n",
            hints=[
                "Bezeichnung: im.designation_a->>'de'. Nicht designation, sondern designation_a.",
                "Mandant: c.code. Join-Spalte am Mandanten: accounting_area_item_master_id.",
            ],
            solution="SELECT im.designation_a->>'de' AS bezeichnung, c.code AS mandant FROM instance_1.flowapp_demo_item_master im JOIN instance_1.flowapp_demo_client c ON im.parent_id = c.accounting_area_item_master_id;",
        ),
        EX(
            "d-ex2",
            why="Jemand will wissen, in welchen Zonen Auftrag 100501 geplant ist.",
            task="Gib für die lesbare Nummer 100501 alle Zonentypen (consolidation_type) aus der Zonierung aus.",
            look=[
                "SELECT: oc.consolidation_type — nur das soll in der Ergebnisliste stehen.",
                "ON oc.parent_id = oh.id — UUID, nicht order_id.",
                "WHERE oh.order_id = 100501 — ohne Anführungszeichen, das ist ein Integer.",
            ],
            starter="-- SELECT, JOIN-Spalte und WHERE-Wert ergänzen.\n\nSELECT\n  \nFROM instance_1.flowapp_demo_order_head oh\nJOIN instance_1.flowapp_demo_order_consolidation oc\n  ON oc.parent_id = oh.\nWHERE oh.order_id =\n",
            hints=[
                "Ausgeben: oc.consolidation_type. Join auf oh.id (UUID), nicht auf order_id.",
                "WHERE oh.order_id = 100501 — ohne Anführungszeichen, das ist ein Integer.",
            ],
            solution="SELECT oc.consolidation_type FROM instance_1.flowapp_demo_order_head oh JOIN instance_1.flowapp_demo_order_consolidation oc ON oc.parent_id = oh.id WHERE oh.order_id = 100501;",
        ),
        EX(
            "d-ex3",
            why="Beim Vergleich von Aufträgen stört das Suffix _A in der Auftragsnummer (100501_A vs. 100501).",
            task="Schneide alles nach dem ersten Unterstrich ab und gib die normalisierte Nummer plus order_id aus.",
            look=[
                "Rechts nur „Auftrag“: Spalten order_number und order_id.",
                "Funktion: split_part(order_number, '_', 1) — wie im Lerntext D.4.",
                "FROM ist vorbereitet. Zwei Spalten nach SELECT einsetzen.",
            ],
            starter="-- 100501_A soll zu 100501 werden.\n-- Rechts: Auftrag → order_number, order_id.\n\nSELECT\n  -- Spalten rechts anklicken\nFROM instance_1.flowapp_demo_order_head;\n",
            hints=[
                "split_part(order_number, '_', 1) AS order_number_norm",
                "Zweite Spalte: order_id. Kein JOIN nötig.",
            ],
            solution="SELECT split_part(order_number, '_', 1) AS order_number_norm, order_id FROM instance_1.flowapp_demo_order_head;",
        ),
    ],
    flashcards=[
        {"id": "d-fc1", "front": "Wie liest man den deutschen JSONB-Text aus item_master?", "back": "item_master.designation_a->>'de'  (Spalte heißt designation_a, nicht designation)"},
        {"id": "d-fc2", "front": "Wie kommt item_master zum Mandanten?", "back": "item_master.parent_id = client.accounting_area_item_master_id — es gibt keine client_id am Artikel."},
        {"id": "d-fc3", "front": "Was speichert order_consolidation wirklich?", "back": "Zonen-Einträge (eine Zeile pro Auftrag + Zonentyp), nicht den Auftragskopf. Join: parent_id = order_head.id"},
        {"id": "d-fc4", "front": "Auftrag → Task: welcher reference_key?", "back": "#X.order-id (oder #X.order-number), source_slug_name = 'order-head'"},
    ],
)

L(
    id="e",
    letter="E",
    track="einstieg",
    title="Zeitzonen richtig behandeln",
    minutes=8,
    goals=[
        "timestamptz genau einmal nach Europe/Berlin wandeln",
        "timestamp ohne TZ als lokale Zeit belassen",
        "Niemals doppelte Konvertierung in WHERE-Filtern",
    ],
    content="""Ein sehr häufiger Fehlerquell: Zeitstempel falsch konvertieren.

## E.1 timestamptz-Spalten

Brauchen genau **eine** Konvertierung:

```sql
spalte AT TIME ZONE 'Europe/Berlin'
```

> **Merke:** Genau einmal nach `Europe/Berlin`. Doppelt (`AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Berlin'`) verschiebt die Uhr um zwei Stunden — und darf in WHERE-Filtern nie vorkommen.

## E.2 timestamp ohne Zeitzone

Beispiele: `task_position.storage_date`, `planned_processing_date`. Diese Spalten sind **bereits in lokaler Zeit** gespeichert — hier reicht ein einfacher `::date`-Cast, keine Zeitzonen-Konvertierung nötig.

## E.3 Faustregel

- Für Filterung/Berechnung: immer die korrekte einfache Konvertierungsform.
- Für reine Anzeige in SELECT-Listen wird gelegentlich doppelt konvertiert (falls im Dashboard so vorgesehen), aber **niemals** für WHERE-Filter oder Berechnungen.""",
    exercises=[
        EX(
            "e-ex1",
            why="Ein Dashboard zeigt die letzte Änderung am Vorgang zwei Stunden falsch, weil die Zeitzone doppelt gewandelt wurde.",
            task="Gib id und updated_date des Vorgangs genau einmal nach Europe/Berlin konvertiert aus.",
            look=[
                "Rechts „Vorgang“ (task_head): Spalten id und updated_date (timestamptz).",
                "Spalte rechts anklicken — sie landet in der SELECT-Liste. Danach AT TIME ZONE 'Europe/Berlin' dazuschreiben.",
                "FROM ist vorbereitet. Genau einmal konvertieren, kein Alias nötig.",
            ],
            starter="-- timestamptz: genau EINE Konvertierung, nie doppelt.\n-- Rechts: Vorgang → id, updated_date.\n\nSELECT\n  -- Spalten rechts anklicken\nFROM instance_1.flowapp_demo_task_head;\n",
            hints=[
                "updated_date AT TIME ZONE 'Europe/Berlin' — Alias ist optional.",
                "Zwei Spalten: id und die konvertierte Zeit.",
            ],
            solution="SELECT id, updated_date AT TIME ZONE 'Europe/Berlin' AS updated_berlin FROM instance_1.flowapp_demo_task_head;",
            require=["AT TIME ZONE", "Europe/Berlin"],
            forbid=["AT TIME ZONE 'UTC'"],
        ),
        EX(
            "e-ex2",
            why="Für den Einlagerungstag braucht ihr nur das Datum, keine Uhrzeit und keine Zeitzonen-Rechnung.",
            task="Gib id und das reine Datum von storage_date aus — ohne AT TIME ZONE.",
            look=[
                "Rechts „Position“ unter Vorgang (task_position): id und storage_date (timestamp ohne tz).",
                "Spalte rechts anklicken — sie landet nach SELECT. Dann ::date an storage_date hängen.",
            ],
            starter="-- storage_date ist bereits lokal — kein AT TIME ZONE.\n-- Rechts: Position (Vorgang) → id, storage_date.\n\nSELECT\n  -- Spalten rechts anklicken\nFROM instance_1.flowapp_demo_task_position;\n",
            hints=[
                "storage_date::date — Alias ist optional.",
                "Zwei Spalten: id und das Datum.",
            ],
            solution="SELECT id, storage_date::date AS storage_day FROM instance_1.flowapp_demo_task_position;",
            require=["storage_date"],
            forbid=["AT TIME ZONE"],
        ),
    ],
    flashcards=[
        {"id": "e-fc1", "front": "Wie wandelt man timestamptz korrekt nach Berlin?", "back": "spalte AT TIME ZONE 'Europe/Berlin' — genau einmal, nie doppelt in Filtern."},
        {"id": "e-fc2", "front": "Was gilt für timestamp ohne Zeitzone (z. B. storage_date)?", "back": "Bereits lokale Zeit. Nur ::date casten, kein AT TIME ZONE."},
    ],
)

L(
    id="f",
    letter="F",
    track="einstieg",
    title="Task- & Buchungslogik",
    minutes=10,
    goals=[
        "WE vs. WA über booking_base / alias unterscheiden",
        "task_state 90 + storage_date als präzisen WE-Abschluss nutzen",
        "task_status gehört zum Auftrag, nicht zum Task",
    ],
    content="""## F.1 Buchungskategorien

| Tabelle/Feld | Bedeutung |
|---|---|
| `task_booking_base` | grobe Kategorie: 1000 = Wareneingang (WE), 3000 = Warenausgang (WA), 9000 = Sonstiges |
| `task_booking_class` | Subtyp; Join über `task_head.task_booking_class_id`. `booking_base` hält den Subtyp-Code (z. B. 1100) |

Für konkrete Bewegungsarten filtert man über `tbc.alias`, z. B. `'goods-receipt-single-hu-movement'` oder `'outgoing-goods-single-hu-movement'`.

## F.2 Statuscodes

| Feld | Wert | Bedeutung |
|---|---|---|
| `task_state` | '90' | Task abgeschlossen |
| `task_status` | 'X0' | Auftrag storniert |
| `putaway_status` | '80' | WE abgeschlossen (Auftragsebene) |
| `loading_status`/`task_status` | '80' | WA abgeschlossen |

Für eine **granularere** WE-Abschlussprüfung auf HU-Ebene: `th.task_state = '90' UND tp.storage_date IS NOT NULL` — präziser als der Auftragsstatus `putaway_status`.

`storage_date` (auf `task_position`) ist das korrekte Feld für den physischen Einlagerungszeitpunkt. `th.updated_date` zeigt dagegen nur die letzte Änderung am Datensatz — nicht zwingend das Einlagerungsereignis selbst.

Die feinere Statuslogik auf `order_head` (Codes `'00'`, `'80'`, `'X0'`, `'--'`) folgt in Teil L.""",
    exercises=[
        EX(
            "f-ex1",
            why="Du sollst alle Vorgänge finden, die eine bestimmte Buchungsart haben — nicht über eine UUID, sondern über den sprechenden Alias.",
            task="Gib die IDs aller Vorgänge aus, deren Buchungsklasse den Alias 'goods-receipt-single-hu-movement' hat.",
            look=[
                "Rechts „Vorgang“ (task_head): id und task_booking_class_id.",
                "Rechts „Klasse (Vorgangsbuchung)“: id und alias.",
                "FROM und JOIN sind vorbereitet. SELECT und WHERE ergänzen.",
            ],
            starter="-- Welche Vorgänge haben diese Buchungsklasse?\n-- Rechts: Vorgang und Klasse (Vorgangsbuchung) → alias.\n\nSELECT\n  -- Spalten rechts anklicken\nFROM instance_1.flowapp_demo_task_head th\nJOIN instance_1.flowapp_demo_task_booking_class tbc\n  ON tbc.id = th.task_booking_class_id\nWHERE\n",
            hints=[
                "Ausgeben: th.id",
                "WHERE tbc.alias = 'goods-receipt-single-hu-movement'",
            ],
            solution="SELECT th.id FROM instance_1.flowapp_demo_task_head th JOIN instance_1.flowapp_demo_task_booking_class tbc ON tbc.id = th.task_booking_class_id WHERE tbc.alias = 'goods-receipt-single-hu-movement';",
        ),
        EX(
            "f-ex2",
            why="Für einen WE-Abschlussbericht zählen nur Vorgänge, die wirklich fertig und physisch eingelagert sind — nicht nur der Auftragsstatus.",
            task="Finde abgeschlossene Wareneingangs-Vorgänge auf HU-Ebene. Gib task_head.id eindeutig aus.",
            look=[
                "Drei Tabellen rechts: Vorgang, Position (Vorgang), Klasse (Vorgangsbuchung).",
                "WE: alias beginnt mit goods-receipt. Fertig: task_state = '90'. Eingelagert: storage_date IS NOT NULL.",
                "JOIN ist vorbereitet. SELECT DISTINCT und die drei Filter mit AND.",
            ],
            starter="-- WE fertig und physisch eingelagert.\n-- Rechts: Vorgang.task_state, Position.storage_date, Klasse.alias.\n\nSELECT\n  -- Spalten rechts anklicken\nFROM instance_1.flowapp_demo_task_head th\nJOIN instance_1.flowapp_demo_task_position tp\n  ON tp.task_head_id = th.id\nJOIN instance_1.flowapp_demo_task_booking_class tbc\n  ON tbc.id = th.task_booking_class_id\nWHERE\n",
            hints=[
                "SELECT DISTINCT th.id — sonst verdoppelt der Join über Positionen denselben Vorgang.",
                "WHERE tbc.alias LIKE 'goods-receipt%' AND th.task_state = '90' AND tp.storage_date IS NOT NULL",
            ],
            solution="SELECT DISTINCT th.id FROM instance_1.flowapp_demo_task_head th JOIN instance_1.flowapp_demo_task_position tp ON tp.task_head_id = th.id JOIN instance_1.flowapp_demo_task_booking_class tbc ON tbc.id = th.task_booking_class_id WHERE tbc.alias LIKE 'goods-receipt%' AND th.task_state = '90' AND tp.storage_date IS NOT NULL;",
        ),
    ],
)

L(
    id="g",
    letter="G",
    track="einstieg",
    title="Sicherheitsmuster für UPDATE/DELETE",
    minutes=12,
    goals=[
        "Das 5-Schritte-Muster auswendig anwenden",
        "Kind-Tabellen vor Eltern-Tabellen löschen",
        "Reale FKs in pg_constraint prüfen, nicht nur in der CSV",
    ],
    content="""Da Foreign-Key-Constraints bei uns größtenteils nicht technisch erzwungen sind, ist Vorsicht bei jeder datenverändernden Aktion Pflicht. Dieses Muster wird **immer** eingehalten:

1. **Vorab-Prüfung**: `SELECT` der betroffenen Zeilen, um zu verstehen, was verändert wird.
2. **BEGIN** — Transaktion starten.
3. **DELETE/UPDATE** ausführen.
4. **Verifikations-SELECT** — prüfen, ob das Ergebnis stimmt.
5. **COMMIT** — Änderung endgültig übernehmen (`ROLLBACK` als auskommentierte Alternative bereithalten).

Bei mehreren abhängigen Tabellen (FK-Hierarchie): **immer von unten nach oben löschen** (erst Kind-Tabellen, dann Eltern-Tabelle).

**Wichtig für ausgelieferte Skripte:** Das finale Skript wird immer mit einem **einkommentierten COMMIT** ausgeliefert — ein auskommentiertes COMMIT führt in der Praxis zu Verwirrung darüber, ob die Änderung tatsächlich übernommen wurde.

Vor jedem DELETE: die tatsächlichen Fremdschlüssel-Abhängigkeiten über die **Systemkataloge** (`pg_constraint`) prüfen, nicht nur über die Schema-CSV, da diese reale Constraints nicht zuverlässig abbildet.

```sql
-- Beispiel-Muster
SELECT * FROM instance_1.flowapp_demo_task_position WHERE id = '...';

BEGIN;
DELETE FROM instance_1.flowapp_demo_task_position WHERE id = '...';
SELECT * FROM instance_1.flowapp_demo_task_position WHERE id = '...'; -- muss leer sein
COMMIT;
-- ROLLBACK;
```

*In dieser App darfst du das Muster direkt im SQL-Playground bzw. in den Übungen unten ausführen (SELECT, UPDATE, DELETE, BEGIN/COMMIT). DROP/ALTER sind gesperrt. Wenn die Beispieldaten durcheinandergeraten, setzt du sie über **Datenbank zurücksetzen** wieder auf den Ausgangszustand. Niemals gegen die echte Produktivumgebung üben.*""",
    exercises=[
        EX(
            "g-ex1",
            why="Der Auftrag 100507_A soll fachlich als abgeschlossen gelten (Status 80). Das darf nie ohne Vorab-SELECT und Transaktion passieren.",
            task="Setze task_status von Auftrag 100507_A auf '80'. Muster: SELECT → BEGIN → UPDATE → Kontroll-SELECT → COMMIT.",
            look=[
                "Rechts „Auftrag“: order_number und task_status.",
                "Das Vorab-SELECT steht schon da. Darunter BEGIN, UPDATE, dieselbe SELECT nochmal, COMMIT.",
            ],
            starter="-- Erst nachschauen, dann ändern, dann kontrollieren.\n-- Rechts: Auftrag → order_number, task_status.\n\nSELECT order_number, task_status\nFROM instance_1.flowapp_demo_order_head\nWHERE order_number = '100507_A';\n\n-- BEGIN;\n-- UPDATE …\n-- SELECT … (Kontrolle)\n-- COMMIT;\n",
            hints=[
                "Nach dem SELECT: BEGIN; dann UPDATE … SET task_status = '80' WHERE order_number = '100507_A';",
                "Danach dieselbe SELECT-Zeile zur Kontrolle, zum Schluss COMMIT;",
            ],
            solution="SELECT order_number, task_status FROM instance_1.flowapp_demo_order_head WHERE order_number = '100507_A';\nBEGIN;\nUPDATE instance_1.flowapp_demo_order_head SET task_status = '80' WHERE order_number = '100507_A';\nSELECT order_number, task_status FROM instance_1.flowapp_demo_order_head WHERE order_number = '100507_A';\nCOMMIT;",
            kind="write",
            verify="SELECT order_number, task_status FROM instance_1.flowapp_demo_order_head WHERE order_number = '100507_A'",
            expected=[{"order_number": "100507_A", "task_status": "80"}],
        ),
        EX(
            "g-ex2",
            why="Eine offene Vorgangsposition soll weg. Daran hängen noch Referenzen — Kind zuerst, sonst bleiben Reste.",
            task="Lösche die Position aaaaaaab-0000-0000-0000-000000000002. Erst die Referenz, dann die Position. Mit BEGIN → DELETE → Kontrolle → COMMIT.",
            look=[
                "Rechts „Referenz“ (task_position_reference) hängt an Position (Eltern: Position).",
                "Rechts „Position“ (task_position) unter Vorgang.",
                "Vorab-SELECT steht. In der Transaktion: erst Kind löschen, dann Eltern.",
            ],
            starter="-- Kind zuerst, dann Eltern.\n-- Rechts: Referenz (Vorgangsposition) und Position (Vorgang).\n\nSELECT id, task_position_id\nFROM instance_1.flowapp_demo_task_position_reference\nWHERE task_position_id = 'aaaaaaab-0000-0000-0000-000000000002';\n",
            hints=[
                "Erst DELETE FROM …_task_position_reference WHERE task_position_id = '…'; sonst bleibt die Kind-Zeile.",
                "Danach DELETE FROM …_task_position WHERE id = '…'; Kontroll-SELECT muss leer sein, dann COMMIT;",
            ],
            solution="SELECT id FROM instance_1.flowapp_demo_task_position_reference WHERE task_position_id = 'aaaaaaab-0000-0000-0000-000000000002';\nBEGIN;\nDELETE FROM instance_1.flowapp_demo_task_position_reference WHERE task_position_id = 'aaaaaaab-0000-0000-0000-000000000002';\nDELETE FROM instance_1.flowapp_demo_task_position WHERE id = 'aaaaaaab-0000-0000-0000-000000000002';\nSELECT id FROM instance_1.flowapp_demo_task_position WHERE id = 'aaaaaaab-0000-0000-0000-000000000002';\nCOMMIT;",
            kind="write",
            verify="SELECT id FROM instance_1.flowapp_demo_task_position WHERE id = 'aaaaaaab-0000-0000-0000-000000000002'",
            expected=[],
        ),
    ],
    quiz=[
        {"q": "Was kommt in unserem Sicherheitsmuster nach BEGIN?", "options": ["COMMIT", "DELETE/UPDATE ausführen", "Verifikations-SELECT", "ROLLBACK"], "correct": 1, "explain": "Reihenfolge: SELECT → BEGIN → Änderung → Verifikations-SELECT → COMMIT. Nach BEGIN kommt die eigentliche Änderung."},
        {"q": "In welcher Reihenfolge löscht man bei abhängigen Tabellen?", "options": ["Von oben nach unten (Eltern zuerst)", "Reihenfolge egal", "Von unten nach oben (Kind-Tabellen zuerst)", "Alphabetisch"], "correct": 2, "explain": "Erst Kinder, dann Eltern. Sonst bleiben verwaiste Referenzen — und FKs sind bei uns oft nicht erzwungen, also merkt die DB das nicht."},
        {"q": "Wie wird ein finales, ausgeliefertes Änderungsskript committed?", "options": ["Mit auskommentiertem COMMIT", "Mit einkommentiertem COMMIT", "Ganz ohne COMMIT", "Nur mit ROLLBACK"], "correct": 1, "explain": "COMMIT muss aktiv im Skript stehen. Ein auskommentiertes COMMIT lässt offen, ob die Änderung wirklich durch ist."},
        {"q": "Wo prüft man reale FK-Abhängigkeiten zuverlässig?", "options": ["In der Schema-CSV", "Im Systemkatalog pg_constraint", "Im Metabase-Dashboard", "Im DBeaver-ER-Diagramm ausschließlich"], "correct": 1, "explain": "Nur pg_constraint zeigt, was die Datenbank wirklich erzwingt. Die Schema-CSV ist dafür unvollständig."},
    ],
)

L(
    id="h",
    letter="H",
    track="einstieg",
    title="Häufige Fallstricke",
    minutes=6,
    goals=[
        "Die fünf häufigsten falschen Spaltennamen korrigieren können",
        "relation does not exist als fehlende dynamische Tabelle deuten",
        "integer = uuid vor dem Ausführen prüfen",
    ],
    content="""| Falsch angenommen | Richtig | Tabelle |
|---|---|---|
| `location_id` | `storage_location_id` | `handling_unit` |
| `task_booking_class` | `task_booking_class_id` (FK) | `task_head` |
| `task_head.task_status` | `order_head.task_status` | `order_head` |
| `batch` | `batch_a`, `batch_b` | `stock_quant` |
| `designation` | `designation_a` (JSONB) | `item_master` |

**Weitere häufige Fehlerquellen:**

- Dynamisch erzeugte Tabellen (über `ProcessModelFactory.create_table()`) existieren auf Prod evtl. nicht, wenn ein Table-Rebuild-Deploy-Schritt übersprungen wurde → bei `relation does not exist` in Betracht ziehen (Teil K.1).
- Views übernehmen keine neuen Spalten automatisch (siehe A.9).
- Datentyp-Mismatches bei Joins (`integer = uuid`) vor dem Ausführen prüfen.
- Übersetzungstabellen (`*_translation`) existieren nicht mehr als empfohlener Weg — mehrsprachige Werte liegen als JSONB (D.1 / K.8).
- Print-/Ausgabekonfiguration liegt im Schema `subscription`, nicht in `instance_1` (K.3).""",
    quiz=[
        {"q": "Wie heißt die Spalte für den Lagerort korrekt in 'handling_unit'?", "options": ["location_id", "storage_location_id", "storage_id", "hu_location"], "correct": 1, "explain": "Es heißt storage_location_id. location_id ist der klassische Anfängerfehler in dieser Tabelle."},
        {"q": "In welcher Tabelle liegt task_status wirklich (statt task_head)?", "options": ["order_head", "task_position", "handling_unit", "client"], "correct": 0, "explain": "task_status ist ein Auftragsfeld auf order_head. Am Task heißt das Pendant task_state."},
        {"q": "Wie heißen die Batch-Spalten in stock_quant?", "options": ["batch", "batch_1 / batch_2", "batch_a / batch_b", "lot_a / lot_b"], "correct": 2, "explain": "batch_a und batch_b — nicht batch."},
        {"q": "Welcher Fehler deutet auf eine fehlende, dynamisch erzeugte Tabelle hin?", "options": ["permission denied", "relation does not exist", "syntax error", "division by zero"], "correct": 1, "explain": "ProcessModelFactory-Tabellen fehlen, wenn der Rebuild-Deploy übersprungen wurde. Symptom: relation does not exist."},
    ],
    flashcards=[
        {"id": "h-fc1", "front": "handling_unit: Lagerort-Spalte?", "back": "storage_location_id — nicht location_id"},
        {"id": "h-fc2", "front": "task_status vs. task_state", "back": "task_status liegt auf order_head. task_state liegt auf task_head."},
        {"id": "h-fc3", "front": "item_master: Bezeichnungsspalte?", "back": "designation_a (JSONB), nicht designation"},
    ],
)

L(
    id="i",
    letter="I",
    track="einstieg",
    title="Typischer Arbeitsablauf",
    minutes=6,
    goals=[
        "Vor dem SQL-Schreiben Spalten und Datentypen prüfen",
        "Im SQL-Playground mit LIMIT testen, bevor Metabase drankommt",
        "Bei Writes das Sicherheitsmuster aus Teil G nicht überspringen",
    ],
    content="""1. **Spaltennamen prüfen** gegen die Schema-CSV, bevor man eine Abfrage schreibt (gefilterter Auszug für die gewünschte Tabelle, Spalte "Tabelle" = `flowapp_demo_<tabellenname>`).
2. **Für Fremdschlüssel-Fragen**: nicht die Schema-CSV verwenden (unvollständig), sondern die echten Constraints über `pg_constraint` abfragen.
3. **Datentypen** der zu verknüpfenden Spalten prüfen, bevor man JOINs schreibt (siehe A.4).
4. Bei großen Wertelisten (VALUES-Listen): die Datei komplett neu generieren statt zu patchen. In einer Staging-CTE alle Werte als Text anführen, erst in einer zweiten CTE casten (Teil K.6).
5. **Im SQL-Playground testen**, bei Bedarf zunächst mit `LIMIT` auf einen kleinen Ausschnitt begrenzen.
6. Bei datenverändernden Skripten: **Sicherheitsmuster aus Teil G** anwenden.
7. Für Dashboards: Abfrage nach Metabase übertragen, Variablen/Field Filters gemäß Teil C.2 konfigurieren.""",
    exercises=[
        EX(
            "i-ex1",
            why="Bevor du eine große Query baust, schaust du erst eine Zeile an — so testest du Spaltennamen ohne die ganze Tabelle zu laden.",
            task="Lies storage_location_id aus der Handling-Unit, aber nur eine Zeile (LIMIT 1).",
            look=[
                "Rechts „Handling-Unit“: die Spalte heißt storage_location_id, nicht location_id.",
                "FROM und LIMIT sind vorbereitet. Nur die Spalte nach SELECT.",
            ],
            starter="-- Erst eine Zeile, dann skalieren.\n-- Rechts: Handling-Unit → storage_location_id (nicht location_id).\n\nSELECT\n  -- Spalten rechts anklicken\nFROM instance_1.flowapp_demo_handling_unit\nLIMIT 1;\n",
            hints=[
                "Eine Spalte reicht: storage_location_id.",
                "LIMIT 1 steht schon am Ende.",
            ],
            solution="SELECT storage_location_id FROM instance_1.flowapp_demo_handling_unit LIMIT 1;",
        )
    ],
)

L(
    id="j",
    letter="J",
    track="einstieg",
    title="Checkliste & Glossar",
    minutes=6,
    goals=[
        "Die Einstiegs-Checkliste als Arbeitsritual verinnerlichen",
        "WE, WA, HU, CTE, Sendung, TNR und TARIC sicher übersetzen",
    ],
    content="""## Checkliste für den Einstieg

- Zugänge zu DBeaver und Metabase für die **echte** Umgebung einrichten lassen (nicht für diese Lern-App).
- Die Referenzdateien (Schema-CSV, FK/PK-Excel) kennen und griffbereit haben.
- Verstehen, dass FK-Constraints nicht technisch erzwungen sind → vor jeder Änderung selbst prüfen.
- Das Sicherheitsmuster (BEGIN → Änderung → Verifikation → COMMIT) für **jede** Datenänderung anwenden, ohne Ausnahme.
- Zeitzonen-Regeln aus Teil E verinnerlichen — eine der häufigsten Fehlerquellen.
- Die zentralen Referenzketten (Auftrag ↔ Task ↔ Handling Unit) aus Teil D.4 nachvollziehen können.
- Bei Unsicherheit: erst mit `SELECT` und `LIMIT` gegen die Read Replica testen, niemals ungetestet direkt in Metabase-Dashboards produktiv setzen.
- Kommunikation mit Fachkollegen und Kunden ist meist knapp und direkt — Rückfragen lieber konkret stellen.

Ab hier folgt die Vertiefung: Eigenheiten der Installation (K), Statuslogik (L), Alias-Filter (M), Verpackung (N), Zoll (O) und Rückverfolgbarkeit (P).

## Kurzglossar

| Begriff | Erklärung |
|---|---|
| WE | Wareneingang (Goods Receipt) |
| WA | Warenausgang (Goods Issue) |
| HU | Handling Unit (z. B. Palette, Behälter) |
| Mandant | Kunde/Client innerhalb der Multi-Tenant-Umgebung |
| CTE | Common Table Expression, WITH-Klausel |
| FK / PK | Foreign Key / Primary Key |
| Field Filter | Metabase-Filtermechanismus, direkt an eine Tabellenspalte gebunden |
| Read Replica / Hot Standby | Lesekopie der Datenbank fürs Reporting |
| Sendung | Gruppierung mehrerer WA-Aufträge über eine gemeinsame `shipment_number` |
| Welle / Wave | Übergeordnete Steuerungsebene oberhalb der Sendung für gemeinsame Verladung |
| TARIC | EU-Zolltarifnummer zur Warenklassifizierung |
| AES | Automated Export System — US-Ausfuhrverfahren |
| TNR | Externe/kundenseitige Tracking-Nummer einer Handling Unit |
| Gebindeeinheit | Palettentyp / größte Verpackungsebene einer Verpackungsstruktur |""",
    quiz=[
        {"q": "Wofür steht 'HU'?", "options": ["Handling Unit", "Hot Unit", "Header Update", "Hub Unit"], "correct": 0, "explain": "Handling Unit — Palette, Behälter oder vergleichbarer Ladehilfsmittel-Datensatz."},
        {"q": "Was ist eine 'Read Replica'?", "options": ["Ein Backup-Skript", "Eine Lesekopie der DB fürs Reporting", "Ein Metabase-Plugin", "Ein zweiter Primary-Server für Schreibzugriffe"], "correct": 1, "explain": "Hot Standby nur zum Lesen, damit Reporting den Primary nicht belastet."},
        {"q": "Wofür steht CTE?", "options": ["Common Table Expression", "Client Type Extension", "Central Task Engine", "Column Transform Expression"], "correct": 0, "explain": "WITH-Klausel. In Metabase werden referenzierte CTEs oft inline gebaut — bei Last AS MATERIALIZED nutzen."},
        {"q": "Was ist eine Sendung in unserem Modell?", "options": ["Ein einzelner Task", "Gruppierung mehrerer WA-Aufträge über shipment_number", "Ein Mandant", "Eine Handling Unit"], "correct": 1, "explain": "Mehrere Warenausgangs-Aufträge teilen sich dieselbe shipment_number; die Sendung selbst ist auch eine order_head-Zeile mit anderer Auftragsklasse."},
        {"q": "Wofür steht TNR?", "options": ["Task-Nummer", "Externe Tracking-Nummer einer HU", "Tarifnummer", "Transaktionsnummer"], "correct": 1, "explain": "TNR ist eine externe/kundenseitige Kennung in handling_unit_identification, typisiert über einen Identification-Type."},
    ],
    flashcards=[
        {"id": "j-fc1", "front": "WE", "back": "Wareneingang (Goods Receipt). booking_base 1000er-Bereich."},
        {"id": "j-fc2", "front": "WA", "back": "Warenausgang (Goods Issue). booking_base 3000er-Bereich."},
        {"id": "j-fc3", "front": "HU", "back": "Handling Unit — Palette, Behälter, Ladehilfsmittel."},
        {"id": "j-fc4", "front": "CTE", "back": "Common Table Expression, die WITH-Klausel."},
        {"id": "j-fc5", "front": "Field Filter", "back": "Metabase-Filter, gebunden an eine echte Tabellenspalte — braucht unaliasten Tabellennamen."},
        {"id": "j-fc6", "front": "Sendung", "back": "Mehrere WA-Aufträge, gruppiert über dieselbe shipment_number."},
        {"id": "j-fc7", "front": "TARIC", "back": "EU-Zolltarifnummer. Spalte: item_master.customs_tariff_number_taric"},
        {"id": "j-fc8", "front": "TNR", "back": "Externe Tracking-Nummer einer HU (handling_unit_identification)."},
    ],
)

L(
    id="k",
    letter="K",
    track="vertiefung",
    title="Eigenheiten unserer Datenbank",
    minutes=14,
    goals=[
        "ProcessModelFactory-Tabellen von Tippfehlern unterscheiden",
        "Test/Prod über Business Keys + MD5 statt UUID vergleichen",
        "Die fünf Installations-Fallen aus K.7 kennen",
    ],
    content="""Dieser Teil sammelt Besonderheiten **unserer** Installation — nichts, was in einem allgemeinen Postgres-Tutorial steht.

## K.1 Dynamisch erzeugte Tabellen (ProcessModelFactory)

Ein Teil der Tabellen wird nicht über klassische Migrationen angelegt, sondern zur Laufzeit über `ProcessModelFactory.create_table()`.

- Auf einer Testumgebung kann so eine Tabelle fehlen, wenn der Rebuild-Deploy-Schritt nicht gelaufen ist.
- Fehlermeldung: `relation "..." does not exist` — oft **kein** Tippfehler, sondern fehlender Rebuild.
- Bevor man lange nach Schreibfehlern sucht: Tabelle im Schema-Explorer prüfen.

## K.2 Test → Prod Konfigurationsabgleich

UUIDs unterscheiden sich zwischen Test und Prod grundsätzlich, auch wenn die fachlichen Daten identisch sind. Ein Vergleich über `id` funktioniert deshalb **nicht**.

Stattdessen: fachliche Schlüssel (Name, Code, Alias) und ein Fingerprint der ganzen Zeile:

```sql
SELECT code,
       MD5(to_jsonb(t)::text) AS fingerprint
FROM instance_1.flowapp_demo_client t;
```

Zwei Datensätze mit demselben Hash sind inhaltlich identisch — ohne jede Spalte einzeln zu vergleichen.

## K.3 Print-Konfiguration im Schema subscription

Drucker-Events liegen **nicht** in `instance_1`, sondern in `subscription.processevents_*`. Beim Einrichten neuer Drucker-Umgebungen werden Event-Zuordnungen dort eingefügt. Schema in der Abfrage nicht vergessen.

## K.4 Bestandskorrekturen

Wiederkehrendes Szenario: `stock_quant.quantity_unit_id` passt nicht zur Basiseinheit im Artikelstamm (`item_master.quantity_unit_id`). Erst die Einheit im Stamm prüfen, dann den Bestand anpassen.

Bei manchen Mandanten wird dieselbe Artikelnummer über mehrere (Unter-)Mandanten wiederverwendet — Korrekturen dann über fachliche Kennung plus Mandant, nicht nur über UUID.

Für jede Bestandskorrektur gilt das Sicherheitsmuster aus Teil G.

## K.5 Warum die Schema-CSV allein nicht reicht

Die CSV zeigt Spalten und Typen, aber **nicht zuverlässig** echte FKs. Viele Beziehungen sind nicht als Constraint hinterlegt.

- Echte Constraints: `pg_constraint`
- Dokumentierte (auch nicht erzwungene) Beziehungen: FK/PK-Excel, Blatt "Abfrageergebnis"
- Erst wenn beide Quellen nichts zeigen, und dann trotzdem fachlich gegenchecken.

## K.6 Große VALUES-Listen

1. Alle Werte zuerst als Text in eine Staging-CTE schreiben (auch Zahlen und UUIDs als Text).
2. Erst in einer zweiten CTE in die Zieltypen casten (`::uuid`, `::integer`, …).
3. Bei Korrekturen die ganze Liste neu generieren, nicht einzelne Werte patchen.

## K.7 Die 5 wichtigsten Fallen

| # | Falle | Was zu tun ist |
|---|---|---|
| 1 | FKs nicht technisch erzwungen | Vor DELETE/UPDATE immer `pg_constraint` + FK-Excel prüfen |
| 2 | timestamptz doppelt konvertiert | Nur **einmal** `AT TIME ZONE 'Europe/Berlin'` |
| 3 | UUID-Vergleich zwischen Umgebungen | Business Keys + `MD5(to_jsonb(...))` |
| 4 | Tabelle fehlt auf Testumgebung | ProcessModelFactory-Rebuild prüfen |
| 5 | View zeigt neue Spalte nicht | `CREATE OR REPLACE VIEW` nach Tabellenänderung |

## K.8 Zwei Generationen von Mehrsprachigkeit

Ältere Abfragen joinen noch `*_translation` über `foreign_id_id` und `language = 'de'`:

```sql
LEFT JOIN instance_1.flowapp_demo_item_mastertranslation imt
  ON im.id = imt.foreign_id_id AND imt.language = 'de'
```

Nach der Umstellung auf JSONB (D.1) ist das für **neue** Abfragen nicht mehr der Weg. Viele Metabase-Fragen laufen aber weiter mit dem alten Muster. Zuerst erkennen, welches Muster eine bestehende Query nutzt, bevor man sie anfasst.

## K.9 Alias-basierte Filterung

Stammdaten filtert man über sprechende `alias`-Spalten statt über UUIDs — Details in Teil M.""",
    exercises=[
        EX(
            "k-ex1",
            why="Ein Drucker-Job ist fehlgeschlagen. Die Events liegen nicht in instance_1, sondern im Print-Schema.",
            task="Lies event_type und payload aus den Druck-Events.",
            look=[
                "Rechts nach „Druck-Event“ suchen (processevents_printer).",
                "Schema ist subscription — ohne flowapp-Präfix. FROM ist vorbereitet.",
            ],
            starter="-- Print liegt in subscription, nicht in instance_1.\n-- Rechts: Druck-Event → event_type, payload.\n\nSELECT\n  -- Spalten rechts anklicken\nFROM subscription.processevents_printer;\n",
            hints=[
                "Zwei Spalten: event_type, payload.",
                "Kein instance_1 und kein flowapp_demo_ vor dem Tabellennamen.",
            ],
            solution="SELECT event_type, payload FROM subscription.processevents_printer;",
        ),
        EX(
            "k-ex2",
            why="Bestand und Artikelstamm haben unterschiedliche Mengeneinheiten — das fällt in Reports als Mengen-Mismatch auf.",
            task="Gib HU-Positions-ID, Bestandseinheit und Artikeleinheit (jeweils alias) aus, nur wo sie ungleich sind. Je Position den neuesten Quant.",
            look=[
                "Rechts: Quant, Position (HU), Artikelstamm, Einheit (Mengen) — Einheit zweimal joinen (Bestand vs. Stamm).",
                "CTE ranked ist vorbereitet (neueste Zeile). Außen JOIN und WHERE alias ungleich.",
            ],
            starter="-- Neueste Quant-Zeile je HU-Position, dann Einheiten vergleichen.\n-- Rechts: Quant, Position (Handling-Unit), Artikelstamm, Einheit (Mengen).\n\nWITH ranked AS (\n  SELECT sq.*,\n         ROW_NUMBER() OVER (\n           PARTITION BY sq.handling_unit_position_id\n           ORDER BY sq.updated_date DESC\n         ) AS rn\n  FROM instance_1.flowapp_demo_stock_quant sq\n)\nSELECT\n  -- Spalten rechts anklicken\nFROM ranked r\nJOIN instance_1.flowapp_demo_handling_unit_position hup ON hup.id = r.handling_unit_position_id\nJOIN instance_1.flowapp_demo_item_master im ON im.id = hup.item_master_id\nJOIN instance_1.flowapp_demo_quantity_unit qu_stock ON qu_stock.id = r.quantity_unit_id\nJOIN instance_1.flowapp_demo_quantity_unit qu_item ON qu_item.id = im.quantity_unit_id\nWHERE r.rn = 1\n  AND \n",
            hints=[
                "SELECT r.handling_unit_position_id, qu_stock.alias AS bestand_einheit, qu_item.alias AS artikel_einheit",
                "AND qu_stock.alias <> qu_item.alias",
            ],
            solution="WITH ranked AS (SELECT sq.*, ROW_NUMBER() OVER (PARTITION BY sq.handling_unit_position_id ORDER BY sq.updated_date DESC) AS rn FROM instance_1.flowapp_demo_stock_quant sq) SELECT r.handling_unit_position_id, qu_stock.alias AS bestand_einheit, qu_item.alias AS artikel_einheit FROM ranked r JOIN instance_1.flowapp_demo_handling_unit_position hup ON hup.id = r.handling_unit_position_id JOIN instance_1.flowapp_demo_item_master im ON im.id = hup.item_master_id JOIN instance_1.flowapp_demo_quantity_unit qu_stock ON qu_stock.id = r.quantity_unit_id JOIN instance_1.flowapp_demo_quantity_unit qu_item ON qu_item.id = im.quantity_unit_id WHERE r.rn = 1 AND qu_stock.alias <> qu_item.alias;",
        ),
        EX(
            "k-ex3",
            why="Test und Prod haben verschiedene UUIDs. Zum Konfigurationsabgleich brauchst du Mandanten-Code plus Hash der ganzen Zeile.",
            task="Gib code und MD5(to_jsonb(c)::text) für jeden Mandanten aus.",
            look=[
                "Rechts „Mandant“: Alias der Tabelle im FROM ist c.",
                "FROM ist vorbereitet. Zwei Ausdrücke nach SELECT.",
            ],
            starter="-- Nie die UUID vergleichen — Business Key + Fingerprint.\n-- Rechts: Mandant.\n\nSELECT\n  -- Spalten rechts anklicken\nFROM instance_1.flowapp_demo_client c;\n",
            hints=[
                "Erste Spalte: code",
                "Zweite: MD5(to_jsonb(c)::text) AS fingerprint",
            ],
            solution="SELECT code, MD5(to_jsonb(c)::text) AS fingerprint FROM instance_1.flowapp_demo_client c;",
        ),
    ],
    quiz=[
        {"q": "Warum vergleicht man Konfiguration nicht über UUID zwischen Test und Prod?", "options": ["UUIDs sind zu langsam", "UUIDs unterscheiden sich zwischen Installationen grundsätzlich", "UUIDs sind nicht indexiert", "Metabase verbietet UUID-Filter"], "correct": 1, "explain": "Jede Installation vergibt eigene ids. Fachlich gleiche Zeilen haben trotzdem verschiedene UUIDs. Business Keys + MD5(to_jsonb)."},
        {"q": "Was ist die erste Vermutung bei 'relation does not exist' auf Test?", "options": ["Falsches Passwort", "ProcessModelFactory-Rebuild fehlt", "Read Replica voll", "JSONB-Syntaxfehler"], "correct": 1, "explain": "Dynamische Tabellen entstehen erst durch den Factory-Rebuild. Erst prüfen ob die Tabelle existiert, dann Tippfehler suchen."},
        {"q": "Welches Schema beherbergt Drucker-Events?", "options": ["instance_1", "public", "subscription", "print"], "correct": 2, "explain": "subscription.processevents_* — nicht instance_1."},
    ],
    flashcards=[
        {"id": "k-fc1", "front": "Test/Prod vergleichen — womit statt UUID?", "back": "Business Keys (code, alias, Name) plus MD5(to_jsonb(zeile)::text)."},
        {"id": "k-fc2", "front": "relation does not exist — erste Idee?", "back": "ProcessModelFactory.create_table() / Rebuild-Deploy auf der Umgebung prüfen."},
        {"id": "k-fc3", "front": "Zwei Generationen Mehrsprachigkeit?", "back": "Alt: *_translation + language='de'. Neu: JSONB ->>'de'. Neue Queries immer JSONB."},
    ],
)

L(
    id="l",
    letter="L",
    track="vertiefung",
    title="Auftrags- und Sendungsstatus",
    minutes=12,
    goals=[
        "Statuscodes '00', '80', 'X0' und '--' richtig lesen",
        "Sendung vs. Einzelauftrag über shipment_number trennen",
        "Stornos und '--' in Filtern normalisieren",
    ],
    content="""Die Status-Logik rund um Aufträge und Sendungen gehört zu den komplexeren fachlichen Themen.

## L.1 Das Status-Code-System

Viele Felder auf `order_head` (`loading_status`, `packaging_status`, `task_status`, `reservation_status`, `allocation_status`) folgen zweistelligen Textcodes:

| Codewert | Bedeutung |
|---|---|
| `'00'` | Ausgangszustand, noch nicht gestartet |
| `> '00'` (z. B. `'10'`, `'40'`) | in Bearbeitung |
| `'80'` | abgeschlossen |
| `'X0'` | storniert |
| `'--'` | Feld für diesen Auftragstyp nicht relevant / inaktiv |

Da die Felder `varchar` sind, verfälscht `'--'` Größer/Kleiner-Vergleiche. Standardmuster:

```sql
COALESCE(NULLIF(loading_status, '--'), '00') = '80'
```

Stornierte Aufträge sind in praktisch jedem Auftragsreport Pflichtfilter:

```sql
WHERE task_status <> 'X0'
-- bzw. bei möglichem NULL:
WHERE COALESCE(task_status, '') != 'X0'
```

## L.2 Sendung vs. Einzelauftrag

Ein Warenausgangs-Auftrag (eigene Klasse in `order_class`) kann einzeln laufen oder zu einer **Sendung** zusammengefasst sein. Eine Sendung ist selbst wieder eine `order_head`-Zeile, aber mit der Auftragsklasse für Sendungen. Mehrere WA-Aufträge teilen sich dasselbe `shipment_number`.

Für Reports, die beides abbilden: zuerst prüfen, ob der Auftrag Teil einer Sendung ist — der angezeigte Status kommt dann von der passenden Ebene.

## L.3 Wellen (Waves)

Oberhalb der Sendung gibt es informell "Shipment Wave" und "Haupt-Welle", über die mehrere Sendungen gemeinsam gesteuert und stellenweise gemeinsam verladen werden.

Der sichtbare Status ist oft eine Prioritätskette **Auftrag → Sendung → Welle**; die am weitesten fortgeschrittene Ebene gewinnt. In Metabase steckt das in tief verschachtelten CASE-Ausdrücken.

Praxistipp: Bevor man eine bestehende Statuslogik ändert, klären für welche Fallkonstellation (Einzelauftrag, Sendung oder Welle) der CASE-Zweig gedacht ist.

## L.4 Praxisbeispiel: Liefertreue

```sql
SELECT
  (planned_processing_date + INTERVAL '1 hour')::date AS auftragstag,
  COUNT(*) AS gesamt_auftraege,
  COUNT(*) FILTER (
    WHERE confirmed_end_date_time
      <= (planned_processing_date + INTERVAL '1 hour')::date + INTERVAL '18 hour'
  ) AS termingerechte_auftraege
FROM order_head
WHERE task_status <> 'X0'
  AND created_date < planned_processing_date + INTERVAL '13 hour'
GROUP BY auftragstag;
```

Fachliche Entscheidungen darin:

- Termingerecht = `confirmed_end_date_time` vor Cutoff `planned_processing_date + 18 Stunden`.
- Last-Minute-Aufträge (angelegt nach 13 Uhr des geplanten Tages) werden ausgeschlossen, sonst verfälschen sie die KPI.

Dieses Muster — fachliche Cutoffs in der WHERE-Klausel dokumentieren — lohnt sich bei jeder Kennzahl.""",
    exercises=[
        EX(
            "l-ex1",
            why="Stornierte Aufträge dürfen in fast keinem Report auftauchen — sonst stimmen die Zahlen nicht.",
            task="Gib Auftragsnummer und Status aller nicht stornierten Aufträge aus.",
            look=[
                "Rechts „Auftrag“: order_number und task_status.",
                "Storniert ist der Code 'X0' (varchar, mit Anführungszeichen). FROM ist vorbereitet.",
            ],
            starter="-- Pflichtfilter in fast jedem Auftragsreport.\n-- Rechts: Auftrag → order_number, task_status.\n\nSELECT\n  -- Spalten rechts anklicken\nFROM instance_1.flowapp_demo_order_head\nWHERE\n",
            hints=[
                "SELECT order_number, task_status",
                "WHERE task_status <> 'X0'",
            ],
            solution="SELECT order_number, task_status FROM instance_1.flowapp_demo_order_head WHERE task_status <> 'X0';",
        ),
        EX(
            "l-ex2",
            why="loading_status kann '--' sein (Feld nicht relevant). Ein direkter Vergleich mit '80' würde diese Zeilen falsch behandeln.",
            task="Finde Aufträge mit fachlich abgeschlossenem Verladestatus. Gib order_number und loading_status aus.",
            look=[
                "Rechts „Auftrag“: loading_status.",
                "Muster aus dem Lerntext schon als Kommentar: COALESCE(NULLIF(...),'00') = '80'. FROM ist vorbereitet.",
            ],
            starter="-- '--' zuerst auf '00' normalisieren, dann auf Abschluss prüfen.\n-- Rechts: Auftrag → order_number, loading_status.\n\nSELECT\n  -- Spalten rechts anklicken\nFROM instance_1.flowapp_demo_order_head\nWHERE COALESCE(NULLIF(loading_status, '--'), '00') =\n",
            hints=[
                "SELECT order_number, loading_status",
                "Der Vergleich ist = '80'",
            ],
            solution="SELECT order_number, loading_status FROM instance_1.flowapp_demo_order_head WHERE COALESCE(NULLIF(loading_status, '--'), '00') = '80';",
        ),
        EX(
            "l-ex3",
            why="Zur Sendung SHP-01 gehören mehrere WA-Aufträge plus eine Kopfzeile der Klasse sendung. Die Kopfzeile soll nicht in der Liste stehen.",
            task="Gib order_number und loading_status der WA-Aufträge von SHP-01 aus, ohne die Sendungs-Kopfzeile.",
            look=[
                "Rechts „Auftrag“: shipment_number.",
                "Rechts „Klasse (Auftrag)“: alias (sendung vs. warenausgang). JOIN ist vorbereitet.",
            ],
            starter="-- Sendung SHP-01, aber nicht die Kopfzeile selbst.\n-- Rechts: Auftrag.shipment_number und Klasse (Auftrag).alias.\n\nSELECT\n  -- Spalten rechts anklicken\nFROM instance_1.flowapp_demo_order_head oh\nJOIN instance_1.flowapp_demo_order_class oc\n  ON oc.id = oh.order_class_id\nWHERE\n",
            hints=[
                "SELECT oh.order_number, oh.loading_status",
                "WHERE oh.shipment_number = 'SHP-01' AND oc.alias <> 'sendung'",
            ],
            solution="SELECT oh.order_number, oh.loading_status FROM instance_1.flowapp_demo_order_head oh JOIN instance_1.flowapp_demo_order_class oc ON oc.id = oh.order_class_id WHERE oh.shipment_number = 'SHP-01' AND oc.alias <> 'sendung';",
        ),
    ],
    quiz=[
        {"q": "Was bedeutet der Statuscode 'X0'?", "options": ["Abgeschlossen", "Nicht relevant", "Storniert", "In Bearbeitung"], "correct": 2, "explain": "'X0' = storniert. In Reports fast immer wegfiltern: task_status <> 'X0'."},
        {"q": "Warum normalisiert man '--' vor einem Vergleich mit '80'?", "options": ["Sonst ist der Index hin", "'--' als varchar verfälscht Größenvergleiche", "Metabase kann '--' nicht anzeigen", "Postgres verbietet den Wert"], "correct": 1, "explain": "COALESCE(NULLIF(spalte, '--'), '00') macht inaktive Felder zum Ausgangszustand, bevor man auf Abschluss prüft."},
        {"q": "Wie hängen mehrere WA-Aufträge an einer Sendung?", "options": ["Über dieselbe UUID", "Über dasselbe shipment_number-Feld", "Über task_state", "Über den Mandanten-Alias"], "correct": 1, "explain": "shipment_number ist der fachliche Gruppierungsschlüssel. Die Sendung selbst ist eine eigene order_head-Zeile mit Klasse sendung."},
    ],
    flashcards=[
        {"id": "l-fc1", "front": "Statuscode '80'?", "back": "Abgeschlossen (WE: putaway_status, WA: loading_status / task_status)."},
        {"id": "l-fc2", "front": "Statuscode '--'?", "back": "Feld für diesen Auftragstyp nicht relevant. Vor Vergleichen auf '00' normalisieren."},
        {"id": "l-fc3", "front": "Sendung vs. Auftrag", "back": "Sendung ist selbst order_head mit Klasse sendung. WA-Aufträge teilen sich shipment_number."},
    ],
)

L(
    id="m",
    letter="M",
    track="vertiefung",
    title="Alias-Filter statt UUIDs",
    minutes=8,
    goals=[
        "Stammdaten über alias statt hartkodierter UUID filtern",
        "Typische alias-Tabellen (order_class, HU-Class, Adresse) kennen",
        "Alte UUID-Filter in bestehenden Queries erkennen",
    ],
    content="""Ein sehr verbreitetes Muster: Stammdaten über eine sprechende `alias`-Spalte filtern statt über die technische UUID.

```sql
-- statt (Beispiel-UUID):
WHERE order_class_id = '00000000-0000-0000-0000-000000000000'::uuid
-- lieber:
WHERE oc.alias = 'warenausgang'
```

## M.1 Warum Alias statt UUID?

UUIDs unterscheiden sich zwischen Test und Prod (siehe K.2) — ein hartkodierter UUID-Wert funktioniert oft nur auf genau der Umgebung, von der er kopiert wurde. Aliase sind fachliche Bezeichner, die auf allen Umgebungen identisch sind. Die Abfrage wird portabel und lesbarer.

## M.2 Wo das Muster auftaucht

Typische Tabellen mit `alias`:

- `order_class` — Wareneingang, Warenausgang, Sendung
- `handling_unit_class` — Kategorien von Handling Units
- `handling_unit_identification_type` — Arten externer Kennungen
- `address_category` — Liefer-, Absender-, Rechnungsadresse
- `client` — Mandanten-Alias (in der Lern-DB identisch mit `code`)

Die konkreten Alias-Werte sind Konfigurationsdaten der Installation. Wer mit dem System arbeitet, liest sie aus der jeweiligen Stammdatabelle. In dieser Lern-DB z. B. `warenausgang`, `wareneingang`, `sendung`.

## M.3 Eingebettete Codes in Altfeldern

Manchmal kodiert ein einzelnes Textfeld mehrere Informationen an festen Zeichenpositionen — ein Implementierungsdetail gewachsener Systeme, keine Postgres-Konvention.

Praxistipp: Vermutetes Muster (z. B. "an Position X steht immer Code Y") erst gegen mehrere bekannte Datensätze prüfen.

## M.4 Wichtiger Hinweis

Nicht jede bestehende Abfrage folgt schon dem Alias-Prinzip. In älteren Queries stehen teils noch hartkodierte UUIDs für `client_id` oder `order_class_id`. Historisch gewachsen, kein Fehler per se — bei **neuen** Abfragen ist die Alias-Variante die robustere Wahl.""",
    exercises=[
        EX(
            "m-ex1",
            why="WA-Aufträge sollen nach Auftragsklasse gefiltert werden — nie über eine UUID, die zwischen Test und Prod wechselt.",
            task="Gib Auftragsnummer und Mandanten-Alias aller Warenausgangs-Aufträge aus.",
            look=[
                "Rechts „Klasse (Auftrag)“: alias = warenausgang.",
                "Rechts „Mandant“: alias. JOINs sind vorbereitet.",
            ],
            starter="-- Filter über alias, nicht über UUID.\n-- Rechts: Klasse (Auftrag), Mandant, Auftrag.\n\nSELECT\n  -- Spalten rechts anklicken\nFROM instance_1.flowapp_demo_order_head oh\nJOIN instance_1.flowapp_demo_order_class oc ON oc.id = oh.order_class_id\nJOIN instance_1.flowapp_demo_client c ON c.id = oh.client_id\nWHERE\n",
            hints=[
                "SELECT oh.order_number, c.alias",
                "WHERE oc.alias = 'warenausgang'",
            ],
            solution="SELECT oh.order_number, c.alias FROM instance_1.flowapp_demo_order_head oh JOIN instance_1.flowapp_demo_order_class oc ON oc.id = oh.order_class_id JOIN instance_1.flowapp_demo_client c ON c.id = oh.client_id WHERE oc.alias = 'warenausgang';",
        ),
        EX(
            "m-ex2",
            why="Bevor du Adressen filterst, schaust du nach, welche alias-Werte die Kategorien wirklich haben.",
            task="Liste alias und deutsche Bezeichnung aller Adresskategorien.",
            look=[
                "Rechts „Kategorie (Adresse)“: alias und name (jsonb).",
                "FROM ist vorbereitet. name->>'de' für den deutschen Text.",
            ],
            starter="-- Stammdaten erst lesen, dann in Filtern verwenden.\n-- Rechts: Kategorie (Adresse) → alias, name.\n\nSELECT\n  -- Spalten rechts anklicken\nFROM instance_1.flowapp_demo_address_category;\n",
            hints=[
                "Zwei Spalten aus einer Tabelle, kein JOIN.",
                "alias, name->>'de' AS bezeichnung",
            ],
            solution="SELECT alias, name->>'de' AS bezeichnung FROM instance_1.flowapp_demo_address_category;",
        ),
    ],
    quiz=[
        {"q": "Warum filtert man Stammdaten über alias statt UUID?", "options": ["Alias ist immer ein Integer", "Aliase sind umgebungsstabil und lesbar, UUIDs nicht", "Postgres kann UUIDs nicht vergleichen", "Field Filters brauchen alias"], "correct": 1, "explain": "UUIDs unterscheiden sich zwischen Test und Prod. alias ist der fachliche, portable Schlüssel."},
        {"q": "Welche Tabelle unterscheidet WE-, WA- und Sendungs-Aufträge per alias?", "options": ["task_booking_class", "order_class", "order_consolidation", "client"], "correct": 1, "explain": "order_class.alias — in der Lern-DB z. B. wareneingang, warenausgang, sendung."},
    ],
    flashcards=[
        {"id": "m-fc1", "front": "Filter auf Auftragsklasse — UUID oder alias?", "back": "alias, z. B. WHERE oc.alias = 'warenausgang'. UUIDs sind nicht portabel."},
        {"id": "m-fc2", "front": "Typische alias-Tabellen?", "back": "order_class, handling_unit_class, handling_unit_identification_type, address_category, client."},
    ],
)

L(
    id="n",
    letter="N",
    track="vertiefung",
    title="Verpackungsstruktur & Gebinde",
    minutes=8,
    goals=[
        "packaging_structure über parent_id am Artikel verankern",
        "packaging_level 0 vs. höhere Gebinde unterscheiden",
        "bundling_unit.alias per CASE in lesbare HU-Typen übersetzen",
    ],
    content="""Für Gewichts-, Volumen- und Palettentyp-Berechnungen (Zoll-Reports, Verladeplanung) ist die Verpackungsstruktur eines Artikels relevant.

## N.1 Aufbau

- `packaging_structure`: eine Verpackungsstruktur pro Artikel (`parent_id = item_master.id`).
- `packaging_structure_pos`: die Verpackungsebenen, unterschieden über `packaging_level` (0 = Basis-/Einzelverpackung, höhere Werte = Karton, Lage, Palette).
- Jede Positionszeile trägt Nettogewicht/Bruttogewicht (Gramm) sowie Länge/Breite/Höhe (mm).

## N.2 Gebindeeinheit / Palettentyp (`bundling_unit`)

Die Gebindeeinheit einer Ebene hängt über `bundling_unit_id`. `bundling_unit` hat einen technischen `alias`, der in Reports oft per CASE lesbar gemacht wird:

```sql
CASE bundling_unit.alias
  WHEN 'palette-typ-a' THEN 'Typ A'
  WHEN 'palette-typ-b' THEN 'Typ B'
  ELSE bundling_unit.alias
END AS "HU_Typ"
```

Unbekannte Alias-Werte fallen auf den Rohwert zurück (`ELSE`) — ein Hinweis, die Zuordnungstabelle bei neuen Palettentypen zu pflegen.""",
    exercises=[
        EX(
            "n-ex1",
            why="Für die Verladeplanung braucht ihr den Palettentyp je Artikel (Ebene 3), nicht den technischen Alias.",
            task="Gib die deutsche Artikelbezeichnung und den Palettentyp der Ebene 3 aus. palette-typ-a/b als Typ A/Typ B, sonst den Roh-Alias.",
            look=[
                "Rechts: Artikelstamm → Verpackungsstruktur (Eltern: Artikelstamm) → Verpackungsstrukturposition → Einheit (Gebinde).",
                "JOINs und WHERE packaging_level = 3 sind vorbereitet. SELECT mit CASE ergänzen.",
            ],
            starter="-- Ebene 3 = Palette. Rechts: Artikelstamm, Verpackungsstruktur, Verpackungsstrukturposition, Einheit (Gebinde).\n\nSELECT\n  -- Spalten rechts anklicken\nFROM instance_1.flowapp_demo_item_master im\nJOIN instance_1.flowapp_demo_packaging_structure ps ON ps.parent_id = im.id\nJOIN instance_1.flowapp_demo_packaging_structure_pos psp ON psp.packaging_structure_id = ps.id\nJOIN instance_1.flowapp_demo_bundling_unit bu ON bu.id = psp.bundling_unit_id\nWHERE psp.packaging_level = 3;\n",
            hints=[
                "Erste Spalte: im.designation_a->>'de' AS bezeichnung",
                "CASE bu.alias WHEN 'palette-typ-a' THEN 'Typ A' WHEN 'palette-typ-b' THEN 'Typ B' ELSE bu.alias END AS hu_typ",
            ],
            solution="SELECT im.designation_a->>'de' AS bezeichnung, CASE bu.alias WHEN 'palette-typ-a' THEN 'Typ A' WHEN 'palette-typ-b' THEN 'Typ B' ELSE bu.alias END AS hu_typ FROM instance_1.flowapp_demo_item_master im JOIN instance_1.flowapp_demo_packaging_structure ps ON ps.parent_id = im.id JOIN instance_1.flowapp_demo_packaging_structure_pos psp ON psp.packaging_structure_id = ps.id JOIN instance_1.flowapp_demo_bundling_unit bu ON bu.id = psp.bundling_unit_id WHERE psp.packaging_level = 3;",
        )
    ],
    quiz=[
        {"q": "Was bedeutet packaging_level = 0?", "options": ["Palette", "Basis-/Einzelverpackung", "Sendung", "Zollverfahren"], "correct": 1, "explain": "0 ist die kleinste Ebene. Höhere Werte sind größere Gebinde (Karton, Lage, Palette)."},
        {"q": "Wie hängt packaging_structure am Artikel?", "options": ["über client_id", "parent_id = item_master.id", "über order_head", "über TARIC"], "correct": 1, "explain": "Eine Struktur pro Artikel, parent_id zeigt auf item_master.id."},
    ],
    flashcards=[
        {"id": "n-fc1", "front": "packaging_level 0?", "back": "Basis-/Einzelverpackung. Höhere Werte = größere Gebinde."},
        {"id": "n-fc2", "front": "Gebindeeinheit / Palettentyp?", "back": "bundling_unit, referenziert über bundling_unit_id. Reports mappen alias per CASE."},
    ],
)

L(
    id="o",
    letter="O",
    track="vertiefung",
    title="Zoll & Compliance",
    minutes=10,
    goals=[
        "TARIC, Customs-Status und Incoterm den richtigen Tabellen zuordnen",
        "Adressen am Auftrag über address_category.alias unterscheiden",
        "Neue Abfragen alias-basiert statt über Übersetzungsnamen schreiben",
    ],
    content="""Für Kunden mit grenzüberschreitendem Warenverkehr gibt es ein eigenes Set Zoll-Tabellen.

| Tabelle / Feld | Bedeutung |
|---|---|
| `customs_status_profile` | Zollstatus eines Bestands (verzollt/unverzollt); über `stock_quant.customs_status_id` |
| `customs_procedure_profile` | Zollverfahren eines Auftrags (z. B. AES); über `order_head.customs_procedures_id` |
| `item_master.customs_tariff_number_taric` | TARIC-Code (EU-Zolltarifnummer) |
| `country_code` | ISO-3166-Alpha-2, Ursprungsland und Adressländer |
| `stock_quant.country_of_origin_id` | Ursprungsland eines Bestands → `country_code` |
| `incoterm` | Lieferbedingungen (EXW, FOB, DAP); über `order_head.incoterms_id` |

## O.1 Adresstypen an einem Auftrag

An einem Auftrag können mehrere Adressen hängen: `address_data.parent_id = order_head.id`, unterschieden über `address_category`.

Die drei wichtigsten Kategorien:

- Lieferadresse / Consignee
- Absenderadresse / Consignor
- Rechnungsadresse / Billing

In älteren Abfragen wird statt des Alias die übersetzte Bezeichnung verglichen (`address_categorytranslation.name = 'Consignee (Lieferadresse)'`). Für **neue** Abfragen die alias-Variante (Teil M).""",
    exercises=[
        EX(
            "o-ex1",
            why="Zoll will je Bestand TARIC, Ursprungsland und Zollstatus — immer die neueste Quant-Zeile.",
            task="Gib deutsche Artikelbezeichnung, TARIC, ISO-Ursprungsland und Zollstatus-Alias aus.",
            look=[
                "Rechts: Quant, Position (HU), Artikelstamm (customs_tariff_number_taric), Länderkennzeichen, Profil (Zollstatus).",
                "CTE und JOINs sind vorbereitet. SELECT-Liste und WHERE rn = 1 ergänzen.",
            ],
            starter="-- Neueste Quant-Zeile, dann Zollfelder dazuholen.\n-- Rechts: Quant, Position (HU), Artikelstamm, Länderkennzeichen, Profil (Zollstatus).\n\nWITH ranked AS (\n  SELECT sq.*,\n         ROW_NUMBER() OVER (\n           PARTITION BY sq.handling_unit_position_id\n           ORDER BY sq.updated_date DESC\n         ) AS rn\n  FROM instance_1.flowapp_demo_stock_quant sq\n)\nSELECT\n  -- Spalten rechts anklicken\nFROM ranked r\nJOIN instance_1.flowapp_demo_handling_unit_position hup ON hup.id = r.handling_unit_position_id\nJOIN instance_1.flowapp_demo_item_master im ON im.id = hup.item_master_id\nJOIN instance_1.flowapp_demo_country_code cc ON cc.id = r.country_of_origin_id\nJOIN instance_1.flowapp_demo_customs_status_profile csp ON csp.id = r.customs_status_id\nWHERE\n",
            hints=[
                "SELECT im.designation_a->>'de' AS bezeichnung, im.customs_tariff_number_taric AS taric, cc.iso_code AS ursprungsland, csp.alias AS zollstatus",
                "WHERE r.rn = 1",
            ],
            solution="WITH ranked AS (SELECT sq.*, ROW_NUMBER() OVER (PARTITION BY sq.handling_unit_position_id ORDER BY sq.updated_date DESC) AS rn FROM instance_1.flowapp_demo_stock_quant sq) SELECT im.designation_a->>'de' AS bezeichnung, im.customs_tariff_number_taric AS taric, cc.iso_code AS ursprungsland, csp.alias AS zollstatus FROM ranked r JOIN instance_1.flowapp_demo_handling_unit_position hup ON hup.id = r.handling_unit_position_id JOIN instance_1.flowapp_demo_item_master im ON im.id = hup.item_master_id JOIN instance_1.flowapp_demo_country_code cc ON cc.id = r.country_of_origin_id JOIN instance_1.flowapp_demo_customs_status_profile csp ON csp.id = r.customs_status_id WHERE r.rn = 1;",
        ),
        EX(
            "o-ex2",
            why="Für Auftrag 100504_A braucht der Zoll die Lieferadresse, nicht die Rechnungsadresse.",
            task="Gib Kategorie-Alias, Adressname und ISO-Ländercode der Lieferadresse aus.",
            look=[
                "Rechts „Adresse“ hängt am Auftrag (parent_id).",
                "Rechts „Kategorie (Adresse)“: alias = lieferadresse. JOINs sind vorbereitet.",
            ],
            starter="-- Nur die Lieferadresse dieses Auftrags.\n-- Rechts: Auftrag, Adresse, Kategorie (Adresse), Länderkennzeichen.\n\nSELECT\n  -- Spalten rechts anklicken\nFROM instance_1.flowapp_demo_order_head oh\nJOIN instance_1.flowapp_demo_address_data ad ON ad.parent_id = oh.id\nJOIN instance_1.flowapp_demo_address_category ac ON ac.id = ad.address_category_id\nJOIN instance_1.flowapp_demo_country_code cc ON cc.id = ad.country_id\nWHERE\n",
            hints=[
                "SELECT ac.alias AS kategorie, ad.name, cc.iso_code",
                "WHERE oh.order_number = '100504_A' AND ac.alias = 'lieferadresse'",
            ],
            solution="SELECT ac.alias AS kategorie, ad.name, cc.iso_code FROM instance_1.flowapp_demo_order_head oh JOIN instance_1.flowapp_demo_address_data ad ON ad.parent_id = oh.id JOIN instance_1.flowapp_demo_address_category ac ON ac.id = ad.address_category_id JOIN instance_1.flowapp_demo_country_code cc ON cc.id = ad.country_id WHERE oh.order_number = '100504_A' AND ac.alias = 'lieferadresse';",
        ),
    ],
    quiz=[
        {"q": "Wo liegt die EU-Zolltarifnummer (TARIC)?", "options": ["order_head.taric", "item_master.customs_tariff_number_taric", "stock_quant.taric", "country_code.taric"], "correct": 1, "explain": "TARIC hängt am Artikelstamm, nicht am Auftrag."},
        {"q": "Wie unterscheidet man Liefer- und Rechnungsadresse am Auftrag?", "options": ["Über die UUID der Sendung", "Über address_category.alias an address_data", "Über task_state", "Über incoterm"], "correct": 1, "explain": "address_data.parent_id = order_head.id, die Kategorie kommt von address_category (lieferadresse, absenderadresse, rechnungsadresse)."},
        {"q": "Wofür steht AES in unserem Kontext?", "options": ["Artikel-Ersatz-System", "Automated Export System (Ausfuhrverfahren)", "Alias-Export-Skript", "Address Event Service"], "correct": 1, "explain": "Zollverfahren am Auftrag: customs_procedure_profile, z. B. alias 'aes'."},
    ],
    flashcards=[
        {"id": "o-fc1", "front": "TARIC", "back": "EU-Zolltarifnummer. Spalte item_master.customs_tariff_number_taric."},
        {"id": "o-fc2", "front": "Zollstatus vs. Zollverfahren", "back": "Status hängt am Bestand (stock_quant.customs_status_id). Verfahren hängt am Auftrag (order_head.customs_procedures_id)."},
        {"id": "o-fc3", "front": "Lieferadresse joinen", "back": "address_data.parent_id = order_head.id AND address_category.alias = 'lieferadresse'."},
    ],
)

L(
    id="p",
    letter="P",
    track="vertiefung",
    title="Seriennummern & Tracking",
    minutes=10,
    goals=[
        "Seriennummern auf HU-Position aggregieren, ohne Summen zu verdoppeln",
        "TNR über identification_type.alias von der internen HU-Nummer unterscheiden",
        "STRING_AGG / COUNT DISTINCT als Muster für Fan-out kennen",
    ],
    content="""## P.1 Seriennummern

Seriennummern liegen auf Ebene einer `handling_unit_position`, nicht direkt auf HU- oder Artikelebene:

`hu_position_serial_number.parent_id = handling_unit_position.id`

Eine HU-Position kann mehrere Seriennummern-Zeilen haben (mehrere Einzelstücke auf einer Palette). Für Übersichten wie "Wie viele Seriennummern hat diese HU" deshalb **separat aggregieren** (`COUNT DISTINCT`, `STRING_AGG`) und das Ergebnis per LEFT JOIN an die Hauptabfrage hängen — nicht in der Hauptabfrage mitzählen, sonst verdoppelt der Zeilen-Fan-out die Summen.

In der Produktiv-DB hängt die Position oft über `hup.parent_id` an der HU. In **dieser Lern-DB** ist der FK `handling_unit_position.handling_unit_id` (gleiche Rolle):

```sql
SELECT
  hu.handling_unit_id,
  COUNT(DISTINCT psn.serial_number) AS anzahl_seriennummern,
  STRING_AGG(DISTINCT psn.serial_number, '; ' ORDER BY psn.serial_number) AS seriennummern_liste
FROM instance_1.flowapp_demo_handling_unit hu
JOIN instance_1.flowapp_demo_handling_unit_position hup ON hu.id = hup.handling_unit_id
LEFT JOIN instance_1.flowapp_demo_hu_position_serial_number psn ON hup.id = psn.parent_id
GROUP BY hu.handling_unit_id;
```

## P.2 Externe Tracking-Nummern (TNR)

Neben der internen `handling_unit_number` kann eine HU eine kundenseitige Kennung tragen — in `handling_unit_identification`, typisiert über `handling_unit_identification_type`. Ein bestimmter Type kennzeichnet die externe Tracking-Nummer (TNR). Reports zeigen meist TNR falls vorhanden, sonst die interne Nummer:

```sql
CASE
  WHEN identification_type.alias = 'externe-tracking-nummer'
  THEN ident.handling_unit_identification
  ELSE hu.handling_unit_number
END AS "TNR_oder_HU_Nummer"
```""",
    exercises=[
        EX(
            "p-ex1",
            why="Eine Übersicht soll je HU die Seriennummern zählen — HUs ohne SN dürfen nicht verschwinden.",
            task="Gib je Handling Unit die interne Nummer, die Anzahl distinkter Seriennummern und die Semikolon-Liste (sortiert) aus.",
            look=[
                "Rechts: Handling-Unit, Position (hängt an HU), Seriennummer (hängt an Position über parent_id).",
                "LEFT JOIN und GROUP BY sind vorbereitet. SELECT mit COUNT/STRING_AGG ergänzen.",
            ],
            starter="-- LEFT JOIN, damit HUs ohne Seriennummer bleiben.\n-- Rechts: Handling-Unit, Position, Seriennummer.\n\nSELECT\n  -- Spalten rechts anklicken\nFROM instance_1.flowapp_demo_handling_unit hu\nJOIN instance_1.flowapp_demo_handling_unit_position hup ON hu.id = hup.handling_unit_id\nLEFT JOIN instance_1.flowapp_demo_hu_position_serial_number psn ON hup.id = psn.parent_id\nGROUP BY hu.handling_unit_id;\n",
            hints=[
                "hu.handling_unit_id, COUNT(DISTINCT psn.serial_number) AS anzahl_seriennummern",
                "STRING_AGG(DISTINCT psn.serial_number, '; ' ORDER BY psn.serial_number) AS seriennummern_liste",
            ],
            solution="SELECT hu.handling_unit_id, COUNT(DISTINCT psn.serial_number) AS anzahl_seriennummern, STRING_AGG(DISTINCT psn.serial_number, '; ' ORDER BY psn.serial_number) AS seriennummern_liste FROM instance_1.flowapp_demo_handling_unit hu JOIN instance_1.flowapp_demo_handling_unit_position hup ON hu.id = hup.handling_unit_id LEFT JOIN instance_1.flowapp_demo_hu_position_serial_number psn ON hup.id = psn.parent_id GROUP BY hu.handling_unit_id;",
        ),
        EX(
            "p-ex2",
            why="Auf dem Label soll die externe Tracking-Nummer stehen, falls vorhanden — sonst die interne HU-Nummer.",
            task="Gib je HU handling_unit_number und die Anzeige-Kennung aus (TNR oder interne Nummer).",
            look=[
                "Rechts: Handling-Unit, Identifikation (hängt an HU), Typ (HU-Identifikation) mit alias.",
                "LEFT JOINs sind vorbereitet. SELECT mit CASE auf t.alias ergänzen.",
            ],
            starter="-- TNR wenn der Typ passt, sonst interne Nummer.\n-- Rechts: Handling-Unit, Identifikation, Typ (HU-Identifikation).\n\nSELECT\n  -- Spalten rechts anklicken\nFROM instance_1.flowapp_demo_handling_unit hu\nLEFT JOIN instance_1.flowapp_demo_handling_unit_identification i ON i.handling_unit_id = hu.id\nLEFT JOIN instance_1.flowapp_demo_handling_unit_identification_type t ON t.id = i.identification_type_id;\n",
            hints=[
                "Erste Spalte: hu.handling_unit_number",
                "CASE WHEN t.alias = 'externe-tracking-nummer' THEN i.handling_unit_identification ELSE hu.handling_unit_number END AS tnr_oder_hu_nummer",
            ],
            solution="SELECT hu.handling_unit_number, CASE WHEN t.alias = 'externe-tracking-nummer' THEN i.handling_unit_identification ELSE hu.handling_unit_number END AS tnr_oder_hu_nummer FROM instance_1.flowapp_demo_handling_unit hu LEFT JOIN instance_1.flowapp_demo_handling_unit_identification i ON i.handling_unit_id = hu.id LEFT JOIN instance_1.flowapp_demo_handling_unit_identification_type t ON t.id = i.identification_type_id;",
        ),
    ],
    quiz=[
        {"q": "Auf welcher Ebene liegen Seriennummern?", "options": ["handling_unit", "item_master", "handling_unit_position", "order_head"], "correct": 2, "explain": "hu_position_serial_number.parent_id = handling_unit_position.id. Eine Position kann mehrere SN haben."},
        {"q": "Warum aggregiert man Seriennummern separat statt in der Hauptquery mitzuzählen?", "options": ["STRING_AGG geht nur allein", "Der Join-Fan-out verdoppelt sonst Summen", "Metabase verbietet GROUP BY", "Serials sind JSONB"], "correct": 1, "explain": "Mehrere SN-Zeilen multiplizieren die Haupttabelle. COUNT/STRING_AGG erst gruppieren, dann LEFT JOINen."},
        {"q": "Was ist eine TNR?", "options": ["Task-Referenz-Nummer", "Externe Tracking-Nummer einer HU", "Tarifnummer", "Transaktions-Rollback-Nummer"], "correct": 1, "explain": "handling_unit_identification plus Type-Alias 'externe-tracking-nummer'."},
    ],
    flashcards=[
        {"id": "p-fc1", "front": "Wo hängen Seriennummern?", "back": "hu_position_serial_number.parent_id = handling_unit_position.id — nicht direkt an der HU."},
        {"id": "p-fc2", "front": "TNR vs. interne HU-Nummer", "back": "TNR in handling_unit_identification (Type externe-tracking-nummer). Sonst handling_unit_number."},
        {"id": "p-fc3", "front": "Fan-out bei SN vermeiden", "back": "COUNT DISTINCT / STRING_AGG gruppieren, Ergebnis per LEFT JOIN an die Hauptabfrage — nicht roh joinen und dann SUM."},
    ],
)


def main():
    out = Path(__file__).with_name("lessons.json")
    out.write_text(json.dumps(LESSONS, ensure_ascii=False, indent=2), encoding="utf-8")
    ex = sum(len(l.get("exercises") or []) for l in LESSONS)
    qz = sum(len(l.get("quiz") or []) for l in LESSONS)
    fc = sum(len(l.get("flashcards") or []) for l in LESSONS)
    print(f"Wrote {out} — {len(LESSONS)} lessons, {ex} exercises, {qz} quiz, {fc} flashcards")


if __name__ == "__main__":
    main()
