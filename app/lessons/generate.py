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
    title="SQL auf den Lager-Tabellen",
    minutes=16,
    goals=[
        "Dieselben SELECT/WHERE/JOIN-Befehle voll qualifiziert auf order_head schreiben",
        "INNER JOIN vs. LEFT JOIN an echten Lücken in den Übungsdaten sehen",
        "UUID-Naht (oh.id) nicht mit der lesbaren order_id verwechseln",
    ],
    content="""## Transfer: dieselbe SQL-Sprache, andere Tabellen

SELECT, WHERE, INNER/LEFT JOIN kennst du aus der Akademie. Hier heißen die Dinge **Auftrag**, **Position**, **Mandant** — und jede Tabelle braucht den vollen Namen:

```sql
instance_1.flowapp_demo_<tabellenname>
```

Rechts im Übungsteil steht der deutsche Name (**Auftrag**) und darunter der technische (`order_head`). Ohne `instance_1.` sucht Postgres im falschen Schema.

```sql
SELECT order_number, task_status
FROM instance_1.flowapp_demo_order_head
WHERE order_number = '100504_A';
```

## Die Naht ist eine UUID

Die Position hängt am Auftrag über `order_position.order_head_id = order_head.id`.

`order_head.order_id` ist die **lesbare Nummer** (integer, z. B. 100504). `order_head.id` ist der **UUID-Primärschlüssel**. `integer = uuid` knallt zur Laufzeit — deshalb joinst du nicht über `order_id`.

## INNER JOIN Auftrag → Position

Nur Paare. Auftrag ohne Position fliegt raus.

```sql
SELECT oh.order_number, op.quantity
FROM instance_1.flowapp_demo_order_head oh
INNER JOIN instance_1.flowapp_demo_order_position op
  ON op.order_head_id = oh.id;
```

In der Übungs-DB haben **drei** von acht Aufträgen Positionen — INNER JOIN liefert drei Zeilen. `JOIN` ohne Wort davor ist INNER JOIN.

## LEFT JOIN — Lücken sichtbar

LEFT JOIN behält alle Aufträge. Ohne Position ist `quantity` **NULL** (kein Treffer, nicht 0).

Acht Aufträge, fünf ohne Position. Ein Auftrag hat **keinen Mandanten** (`100508_A`) — LEFT JOIN Auftrag → Mandant zeigt `c.code` dort leer.

```sql
SELECT oh.order_number, c.code
FROM instance_1.flowapp_demo_order_head oh
LEFT JOIN instance_1.flowapp_demo_client c
  ON c.id = oh.client_id;
```

Im Lageralltag fast immer LEFT JOIN, Auftrag links: die Auftragsliste darf nicht verschwinden.

## Welchen JOIN wann?

| Ziel | JOIN |
|---|---|
| Nur Aufträge, die wirklich Positionen haben | **INNER JOIN** |
| Alle Aufträge, Lücken sichtbar lassen | **LEFT JOIN** Auftrag → Position |
| Auftrag plus Mandant, Auftrag darf nicht verschwinden | **LEFT JOIN** Auftrag → Mandant |

Mandant `DEMO` hat keinen Auftrag. Ein FULL JOIN Auftrag/Mandant würde ihn trotzdem zeigen — im Shop selten.

Teil A nimmt Postgres-Eigenheiten: Schema, UUID vs. Integer, CTE und Window Functions.""",
    exercises=[
        EX(
            "sql-ex1",
            why="Dieselben drei Satzteile wie in der Akademie — jetzt mit vollem Tabellennamen.",
            task="Gib Auftragsnummer und Status für den Auftrag 100504_A aus.",
            look=[
                "Rechts „Auftrag“ öffnen. Die Tabelle im FROM steht schon voll qualifiziert.",
                "Zwei Spalten: order_number und task_status. Filter: genau diese Auftragsnummer.",
            ],
            starter="-- Eine Zeile: Auftrag 100504_A.\n\nSELECT\n  \nFROM instance_1.flowapp_demo_order_head\nWHERE\n",
            hints=[
                "Spalten heißen order_number und task_status.",
                "Textfilter in einfachen Anführungszeichen: order_number = '100504_A'.",
            ],
            solution="SELECT order_number, task_status FROM instance_1.flowapp_demo_order_head WHERE order_number = '100504_A';",
        ),
        EX(
            "sql-ex2",
            why="Nur Aufträge, die wirklich Positionen haben — der Rest soll nicht in der Liste stehen.",
            task="Verknüpfe Auftrag und Position per INNER JOIN. Gib Auftragsnummer und Menge aus.",
            look=[
                "Die Position hängt am Auftrag: op.order_head_id = oh.id (UUID, nicht order_id).",
                "SELECT: oh.order_number und op.quantity.",
            ],
            starter="-- Nur Treffer in beiden Tabellen.\n\nSELECT\n  \nFROM instance_1.flowapp_demo_order_head oh\nINNER JOIN instance_1.flowapp_demo_order_position op\n  ON \n",
            hints=[
                "Alias oh und op stehen schon im FROM.",
                "ON op.order_head_id = oh.id — nicht die lesbare order_id.",
            ],
            solution="SELECT oh.order_number, op.quantity FROM instance_1.flowapp_demo_order_head oh INNER JOIN instance_1.flowapp_demo_order_position op ON op.order_head_id = oh.id;",
        ),
        EX(
            "sql-ex3",
            why="Dieselbe Liste, aber Aufträge ohne Position sollen bleiben — Menge dann leer (NULL).",
            task="Verknüpfe Auftrag und Position per LEFT JOIN. Gib Auftragsnummer und Menge aus.",
            look=[
                "Gleicher JOIN-Schlüssel wie eben. LEFT statt INNER hält die fünf Aufträge ohne Position.",
                "Erwartet: mehr Zeilen als bei der INNER-JOIN-Aufgabe.",
            ],
            starter="-- Alle Aufträge, auch ohne Position.\n\nSELECT\n  \nFROM instance_1.flowapp_demo_order_head oh\nLEFT JOIN instance_1.flowapp_demo_order_position op\n  ON \n",
            hints=[
                "SELECT oh.order_number, op.quantity.",
                "ON bleibt op.order_head_id = oh.id. Wer INNER nimmt, verliert Aufträge ohne Position.",
            ],
            solution="SELECT oh.order_number, op.quantity FROM instance_1.flowapp_demo_order_head oh LEFT JOIN instance_1.flowapp_demo_order_position op ON op.order_head_id = oh.id;",
        ),
        EX(
            "sql-ex4",
            why="Ein Auftrag hat keinen Mandanten. Die Auftragsliste darf trotzdem vollständig sein.",
            task="Zeig zu jedem Auftrag die Nummer und den Mandanten-Code. Aufträge ohne Mandant sollen bleiben.",
            look=[
                "Mandant = Tabelle client, Naht c.id = oh.client_id.",
                "LEFT JOIN, Auftrag links. 100508_A hat dann einen leeren Code.",
            ],
            starter="-- Auftragsliste inkl. Lücke beim Mandanten.\n\n",
            hints=[
                "FROM order_head, LEFT JOIN client. Was nicht verschwinden darf, gehört nach links.",
                "ON c.id = oh.client_id — der Code ist c.code, nicht die UUID.",
            ],
            solution="SELECT oh.order_number, c.code FROM instance_1.flowapp_demo_order_head oh LEFT JOIN instance_1.flowapp_demo_client c ON c.id = oh.client_id;",
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

Auftrag mit Mandant — LEFT JOIN, damit der Auftrag bleibt, falls `client_id` fehlt. In der Übungs-DB hat **100508_A keinen Mandanten**: INNER JOIN würde ihn verlieren, LEFT JOIN zeigt `c.code` als NULL.

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
            why="Ohne Schema-Präfix sucht Postgres im search_path und findet die Tabelle nicht.",
            task="Zeig Auftragsnummer und Status aller Aufträge. Tabelle voll qualifiziert ansprechen.",
            look=[
                "Muster: instance_1.flowapp_demo_order_head — Schema, Präfix, Name.",
                "Rechts „Auftrag“ — der technische Name steht unter der deutschen Bezeichnung.",
            ],
            starter="-- Vollständiger Name: instance_1.flowapp_demo_…\n\nSELECT\n  \nFROM \n",
            hints=[
                "SELECT order_number, task_status.",
                "FROM instance_1.flowapp_demo_order_head — ohne instance_1. findet Postgres nichts.",
            ],
            require=["instance_1.flowapp_demo_order_head"],
            solution="SELECT order_number, task_status FROM instance_1.flowapp_demo_order_head;",
        ),
        EX(
            "a-ex2",
            why="order_id ist die lesbare Nummer (integer). Joins laufen über id (UUID). Mischen knallt.",
            task="Zeig die Zonentypen von Auftrag 100501. Die Zonierung hängt am UUID-Schlüssel des Auftrags.",
            look=[
                "Tabelle Zonierung (order_consolidation): parent_id = order_head.id, nicht order_id.",
                "Filter auf die lesbare Nummer 100501 darfst du in WHERE nutzen — der JOIN nicht.",
            ],
            starter="SELECT oc.consolidation_type\nFROM instance_1.flowapp_demo_order_head oh\nJOIN instance_1.flowapp_demo_order_consolidation oc\n  ON oc.parent_id = oh.\nWHERE oh.order_id = 100501;\n",
            hints=[
                "Nach oh. kommt id (UUID). order_id wäre der falsche Typ.",
                "ON oc.parent_id = oh.id",
            ],
            solution="SELECT oc.consolidation_type FROM instance_1.flowapp_demo_order_head oh JOIN instance_1.flowapp_demo_order_consolidation oc ON oc.parent_id = oh.id WHERE oh.order_id = 100501;",
        ),
        EX(
            "a-ex3",
            why="Im Bestand stehen oft mehrere Zeilen pro Palettenfach. Der Report soll nur die aktuelle zeigen.",
            task="Behalt pro Lagerplatz-Position nur die neueste Bestandszeile. Gib Positions-ID, Charge und Änderungsdatum aus.",
            look=[
                "Tabelle stock_quant. Mehrere Zeilen je handling_unit_position_id — die mit dem neuesten updated_date behalten.",
                "Muster: ROW_NUMBER() OVER (PARTITION BY … ORDER BY updated_date DESC), danach WHERE rn = 1.",
                "Eine CTE (WITH … AS) hält die Nummerierung lesbar.",
            ],
            starter="-- Pro handling_unit_position_id nur die neueste Zeile (updated_date DESC).\n-- Ausgabe: handling_unit_position_id, batch_a, updated_date\n\n",
            hints=[
                "WITH ranked AS ( SELECT …, ROW_NUMBER() OVER (PARTITION BY handling_unit_position_id ORDER BY updated_date DESC) AS rn FROM … )",
                "Außen nur noch WHERE rn = 1 und die drei Ausgabespalten. Tabelle: instance_1.flowapp_demo_stock_quant.",
            ],
            require=["ROW_NUMBER", "PARTITION BY"],
            solution="WITH ranked AS (SELECT handling_unit_position_id, batch_a, updated_date, ROW_NUMBER() OVER (PARTITION BY handling_unit_position_id ORDER BY updated_date DESC) AS rn FROM instance_1.flowapp_demo_stock_quant) SELECT handling_unit_position_id, batch_a, updated_date FROM ranked WHERE rn = 1;",
        ),
    ],
    quiz=[
        {
            "q": "Wie lautet die voll qualifizierte Ansprache von order_head bei uns?",
            "options": [
                "order_head",
                "flowapp_demo_order_head",
                "instance_1.flowapp_demo_order_head",
                "instance_1.order_head",
            ],
            "correct": 2,
            "explain": "Immer Schema + Präfix + Tabellenname. Ohne instance_1 sucht Postgres im search_path.",
        },
        {
            "q": "Worüber joinst du eine Kindtabelle an den Auftrag?",
            "options": [
                "order_head.order_id (integer, lesbare Nummer)",
                "order_head.id (UUID-Primärschlüssel)",
                "order_number als Text",
                "Immer über den Mandanten",
            ],
            "correct": 1,
            "explain": "order_id ist die lesbare Nummer. Die Naht ist id. integer = uuid wirft einen Laufzeitfehler.",
        },
        {
            "q": "Was macht ROW_NUMBER() … WHERE rn = 1?",
            "options": [
                "Es löscht alle alten Zeilen in der Tabelle.",
                "Pro Partition bleibt die erste Zeile der Sortierung — z. B. die neueste Qualifikation.",
                "Es zählt die Aufträge.",
                "Es ist dasselbe wie LIMIT 1 auf die ganze Tabelle.",
            ],
            "correct": 1,
            "explain": "Window Function nummeriert innerhalb der Gruppe. rn = 1 nach ORDER BY datum DESC = neueste Zeile je Schlüssel.",
        },
        {
            "q": "Wozu eine CTE (WITH … AS)?",
            "options": [
                "Sie ersetzt JOIN.",
                "Ein benanntes Zwischenergebnis, auf das die äußere Query zugreift — z. B. die nummerierten Zeilen.",
                "Sie schreibt in die Tabelle.",
                "Sie ist in Postgres verboten.",
            ],
            "correct": 1,
            "explain": "WITH ranked AS (…) SELECT … FROM ranked WHERE rn = 1. Lesbarer als verschachtelte Subselects.",
        },
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
    exercises=[
        EX(
            "b-ex1",
            why="Multi-Tenant: früh auf den Mandanten filtern, sonst mischst du Daten und nutzt den Index nicht.",
            task="Zeig Auftragsnummer und Status aller Aufträge des Mandanten WEST.",
            look=[
                "Auftrag joinen mit Mandant (client). Filter auf c.code = 'WEST' — nicht auf eine UUID.",
                "LEFT JOIN, damit die Idee aus Teil SQL bleibt; WEST hat Aufträge, INNER ginge hier auch.",
            ],
            starter="SELECT oh.order_number, oh.task_status\nFROM instance_1.flowapp_demo_order_head oh\nJOIN instance_1.flowapp_demo_client c\n  ON c.id = oh.client_id\nWHERE \n",
            hints=[
                "Der Mandanten-Code steht in client.code.",
                "WHERE c.code = 'WEST'",
            ],
            solution="SELECT oh.order_number, oh.task_status FROM instance_1.flowapp_demo_order_head oh JOIN instance_1.flowapp_demo_client c ON c.id = oh.client_id WHERE c.code = 'WEST';",
        ),
    ],
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
            why="Support fragt, welche Artikel zu welchem Mandanten gehören. Am Artikel selbst gibt es keine Mandanten-Spalte.",
            task="Zeig die deutsche Artikelbezeichnung und den Mandanten-Code.",
            look=[
                "Rechts Artikelstamm aufklappen → designation_a klicken (wird zu im.designation_a). Dahinter tippen: ->>'de'",
                "Dann Mandant → code klicken (wird zu c.code).",
                "Der JOIN steht schon — über parent_id, nicht über eine client_id.",
            ],
            starter="SELECT\n  \nFROM instance_1.flowapp_demo_item_master im\nJOIN instance_1.flowapp_demo_client c\n  ON im.parent_id = c.accounting_area_item_master_id;\n",
            hints=[
                "Deutscher Text: im.designation_a->>'de' — die Spalte heißt designation_a, nicht designation.",
                "Mandant: c.code. Ein Alias wie AS bezeichnung ist optional.",
            ],
            solution="SELECT im.designation_a->>'de' AS bezeichnung, c.code AS mandant FROM instance_1.flowapp_demo_item_master im JOIN instance_1.flowapp_demo_client c ON im.parent_id = c.accounting_area_item_master_id;",
        ),
        EX(
            "d-ex2",
            why="Die Halle will wissen, in welchen Zonen Auftrag 100501 geplant ist.",
            task="Zeig die Zonentypen von Auftrag 100501.",
            look=[
                "Nach oh. die Spalte id eintragen — das ist der interne Schlüssel, nicht die lesbare Nummer order_id.",
                "Rechts Zonierung aufklappen, falls du consolidation_type nachschauen willst. Die SELECT-Liste steht schon.",
            ],
            starter="SELECT oc.consolidation_type\nFROM instance_1.flowapp_demo_order_head oh\nJOIN instance_1.flowapp_demo_order_consolidation oc\n  ON oc.parent_id = oh.\nWHERE oh.order_id = 100501;\n",
            hints=[
                "Die Zonierung hängt am Auftrag über oh.id (UUID). order_id wäre die falsche Spalte und der falsche Typ.",
                "ON oc.parent_id = oh.id",
            ],
            solution="SELECT oc.consolidation_type FROM instance_1.flowapp_demo_order_head oh JOIN instance_1.flowapp_demo_order_consolidation oc ON oc.parent_id = oh.id WHERE oh.order_id = 100501;",
        ),
        EX(
            "d-ex3",
            why="Beim Abgleich stört das Suffix _A (100501_A gegen 100501).",
            task="Kürze jede Auftragsnummer vor dem Unterstrich und zeig sie zusammen mit der lesbaren ID.",
            look=[
                "In die Klammern von split_part klicken.",
                "Rechts Auftrag → order_number klicken — sie landet in der Funktion.",
                "order_id steht schon in der zweiten Spalte.",
            ],
            starter="SELECT\n  split_part(, '_', 1) AS order_number_norm,\n  order_id\nFROM instance_1.flowapp_demo_order_head;\n",
            hints=[
                "split_part zerteilt am Unterstrich und nimmt das erste Stück: split_part(order_number, '_', 1).",
                "Erstes Argument ist die Textspalte, nicht die lesbare ID. Zweites Argument ist der Trenner.",
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
    quiz=[
        {"q": "Wie liest man den deutschen Text aus designation_a?", "options": ["designation_a.de", "designation_a->>'de'", "designation", "designation_a->de ohne Quotes"], "correct": 1, "explain": "JSONB: ->> liefert Text. Die Spalte heißt designation_a, nicht designation."},
        {"q": "Wie kommt item_master zum Mandanten?", "options": ["item_master.client_id", "item_master.parent_id = client.accounting_area_item_master_id", "Über order_head", "Gar nicht"], "correct": 1, "explain": "Keine client_id am Artikel. Join über den Buchungskreis Artikelstamm."},
        {"q": "Was speichert order_consolidation?", "options": ["Den Auftragskopf", "Zonen-Einträge (eine Zeile pro Auftrag + Zonentyp)", "Den Mandanten", "Die Sendungsnummer"], "correct": 1, "explain": "parent_id = order_head.id. consolidation_type ist der Zonencode."},
        {"q": "Worüber hängt die Zonierung am Auftrag?", "options": ["order_id (integer)", "order_head.id (UUID)", "order_number", "client_id"], "correct": 1, "explain": "parent_id ist UUID. Filter auf 100501 darfst du in WHERE über order_id machen — der JOIN nicht."},
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
            why="Das Dashboard zeigt die letzte Änderung am Vorgang zwei Stunden falsch — die Uhr wurde doppelt umgerechnet.",
            task="Zeig Vorgangs-ID und letzte Änderung, einmal nach Berlin-Zeit.",
            look=[
                "Rechts Vorgang aufklappen → updated_date klicken (id steht schon).",
                "Direkt dahinter schreiben: AT TIME ZONE 'Europe/Berlin'",
                "Genau einmal — kein zweites AT TIME ZONE.",
            ],
            starter="SELECT\n  id,\n  \nFROM instance_1.flowapp_demo_task_head;\n",
            hints=[
                "Eine Umrechnung: updated_date AT TIME ZONE 'Europe/Berlin'. Ein Spaltenname danach ist optional.",
                "Genau einmal Berlin, kein UTC davor. id steht schon in der ersten Spalte.",
            ],
            solution="SELECT id, updated_date AT TIME ZONE 'Europe/Berlin' AS updated_berlin FROM instance_1.flowapp_demo_task_head;",
            require=["AT TIME ZONE", "Europe/Berlin"],
            forbid=["AT TIME ZONE 'UTC'"],
        ),
        EX(
            "e-ex2",
            why="Für den Einlagerungstag braucht ihr nur das Kalenderdatum — keine Uhrzeit und keine Zeitzonen-Rechnung.",
            task="Zeig Positions-ID und das Datum der Einlagerung, ohne Zeitzone.",
            look=[
                "Rechts „Position“ unter Vorgang aufklappen → storage_date klicken.",
                "Direkt dahinter ::date schreiben — kein AT TIME ZONE, die Spalte ist schon Ortszeit.",
            ],
            starter="SELECT\n  id,\n  \nFROM instance_1.flowapp_demo_task_position;\n",
            hints=[
                "storage_date::date macht aus der Uhr ein Datum. Ein Spaltenname danach ist optional.",
                "Kein AT TIME ZONE — die Spalte ist schon Ortszeit.",
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
    quiz=[
        {"q": "Wie wandelt man timestamptz nach Berlin?", "options": ["AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Berlin'", "Genau einmal: spalte AT TIME ZONE 'Europe/Berlin'", "Nur ::date", "EXTRACT(TIMEZONE FROM …)"], "correct": 1, "explain": "Eine Konvertierung. Doppelt verschiebt um zwei Stunden — nie in WHERE-Filtern."},
        {"q": "Was gilt für storage_date (timestamp ohne TZ)?", "options": ["Auch AT TIME ZONE 'Europe/Berlin'", "Bereits lokale Zeit, nur ::date", "Immer UTC", "Die Spalte ist JSONB"], "correct": 1, "explain": "Ohne Zeitzone gespeichert als Ortszeit. Kein AT TIME ZONE."},
        {"q": "Warum keine doppelte Konvertierung in WHERE?", "options": ["Postgres verbietet das", "Die Uhr verschiebt sich um zwei Stunden, der Filter trifft die falschen Zeilen", "Metabase kann kein AT TIME ZONE", "Nur in SELECT verboten"], "correct": 1, "explain": "Filter auf die verschobene Uhr finden andere Zeilen als gedacht."},
        {"q": "Wo darf doppelte Konvertierung vorkommen?", "options": ["In jedem WHERE", "Gelegentlich nur zur Anzeige in SELECT, wenn das Dashboard das so vorsieht — nie im Filter", "In JOIN-ON", "Nirgends, auch nicht in SELECT"], "correct": 1, "explain": "Anzeige vs. Filter trennen. Rechnen und filtern immer mit der einfachen Form."},
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
            why="Du sollst alle Vorgänge einer Buchungsart finden — über den lesbaren Namen, nicht über eine UUID.",
            task="Zeig die IDs aller Vorgänge mit der Buchungsart goods-receipt-single-hu-movement.",
            look=[
                "Nach tbc.alias = den Namen in einfache Anführungszeichen setzen.",
                "Rechts „Klasse (Vorgangsbuchung)“ aufklappen, wenn du den alias nachschlagen willst.",
            ],
            starter="SELECT th.id\nFROM instance_1.flowapp_demo_task_head th\nJOIN instance_1.flowapp_demo_task_booking_class tbc\n  ON tbc.id = th.task_booking_class_id\nWHERE tbc.alias = \n",
            hints=[
                "Der Filter ist ein Text: 'goods-receipt-single-hu-movement' — mit Anführungszeichen.",
                "WHERE tbc.alias = 'goods-receipt-single-hu-movement'",
            ],
            solution="SELECT th.id FROM instance_1.flowapp_demo_task_head th JOIN instance_1.flowapp_demo_task_booking_class tbc ON tbc.id = th.task_booking_class_id WHERE tbc.alias = 'goods-receipt-single-hu-movement';",
        ),
        EX(
            "f-ex2",
            why="Im WE-Abschlussbericht zählen nur Vorgänge, die fertig sind und wirklich im Fach stehen — nicht der bloße Auftragsstatus.",
            task="Finde abgeschlossene Wareneingänge, die schon eingelagert sind. Jede Vorgangs-ID nur einmal.",
            look=[
                "Die drei Tabellen und DISTINCT stehen schon. Es fehlt der Filter nach WHERE.",
                "Wareneingang: tbc.alias beginnt mit goods-receipt.",
                "Fertig: th.task_state = '90'. Eingelagert: tp.storage_date IS NOT NULL. Die drei mit AND verbinden.",
            ],
            starter="SELECT DISTINCT th.id\nFROM instance_1.flowapp_demo_task_head th\nJOIN instance_1.flowapp_demo_task_position tp\n  ON tp.task_head_id = th.id\nJOIN instance_1.flowapp_demo_task_booking_class tbc\n  ON tbc.id = th.task_booking_class_id\nWHERE\n  \n",
            hints=[
                "Drei Bedingungen: Buchungsart, Status 90, Einlagerungsdatum gesetzt.",
                "WHERE tbc.alias LIKE 'goods-receipt%' AND th.task_state = '90' AND tp.storage_date IS NOT NULL",
            ],
            solution="SELECT DISTINCT th.id FROM instance_1.flowapp_demo_task_head th JOIN instance_1.flowapp_demo_task_position tp ON tp.task_head_id = th.id JOIN instance_1.flowapp_demo_task_booking_class tbc ON tbc.id = th.task_booking_class_id WHERE tbc.alias LIKE 'goods-receipt%' AND th.task_state = '90' AND tp.storage_date IS NOT NULL;",
        ),
    ],
    quiz=[
        {"q": "Wo liegt task_status wirklich?", "options": ["task_head", "order_head", "task_position", "client"], "correct": 1, "explain": "Am Auftrag. Am Vorgang heißt das Pendant task_state."},
        {"q": "Was bedeutet task_state = '90'?", "options": ["Auftrag storniert", "Task abgeschlossen", "WE auf Auftragsebene", "Nur geplant"], "correct": 1, "explain": "90 = Task fertig. Storno des Auftrags ist X0 auf order_head.task_status."},
        {"q": "Präziser WE-Abschluss auf HU-Ebene?", "options": ["Nur putaway_status = '80'", "task_state = '90' UND storage_date IS NOT NULL", "Nur updated_date am Task", "loading_status = '80'"], "correct": 1, "explain": "storage_date ist der physische Einlagerungszeitpunkt, nicht die letzte Datensatz-Änderung."},
        {"q": "Wie unterscheidest du WE- und WA-Vorgänge in SQL?", "options": ["Über UUID der booking_class", "Über tbc.alias (z. B. goods-receipt-… vs. outgoing-goods-…)", "Über den Mandanten", "Über TARIC"], "correct": 1, "explain": "Alias ist portabel zwischen Test und Prod. UUIDs nicht."},
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
            why="Auftrag 100507_A soll als abgeschlossen gelten. Ohne vorheriges Nachschauen und ohne Transaktion ändert man hier nichts.",
            task="Setze den Status von Auftrag 100507_A auf abgeschlossen (80).",
            look=[
                "Das Skript ist schon in der richtigen Reihenfolge: nachschauen, BEGIN, ändern, nochmal nachschauen, COMMIT.",
                "Nach SET task_status = den neuen Wert '80' eintragen (mit Anführungszeichen).",
                "Ausführen, dann Stimmt das?. Wenn die Daten schon geändert sind: Datenbank zurücksetzen.",
            ],
            starter="SELECT order_number, task_status\nFROM instance_1.flowapp_demo_order_head\nWHERE order_number = '100507_A';\n\nBEGIN;\nUPDATE instance_1.flowapp_demo_order_head\nSET task_status =\nWHERE order_number = '100507_A';\n\nSELECT order_number, task_status\nFROM instance_1.flowapp_demo_order_head\nWHERE order_number = '100507_A';\n\nCOMMIT;\n",
            hints=[
                "Abgeschlossen ist der Text '80', nicht die Zahl 80 ohne Anführungszeichen.",
                "SET task_status = '80' WHERE order_number = '100507_A'; — COMMIT steht schon am Ende.",
            ],
            solution="SELECT order_number, task_status FROM instance_1.flowapp_demo_order_head WHERE order_number = '100507_A';\nBEGIN;\nUPDATE instance_1.flowapp_demo_order_head SET task_status = '80' WHERE order_number = '100507_A';\nSELECT order_number, task_status FROM instance_1.flowapp_demo_order_head WHERE order_number = '100507_A';\nCOMMIT;",
            kind="write",
            verify="SELECT order_number, task_status FROM instance_1.flowapp_demo_order_head WHERE order_number = '100507_A'",
            expected=[{"order_number": "100507_A", "task_status": "80"}],
        ),
        EX(
            "g-ex2",
            why="Eine Vorgangsposition soll weg. Daran hängen noch Verweise — die zuerst löschen, sonst bleiben Reste.",
            task="Lösche die Position aaaaaaab-0000-0000-0000-000000000002. Zuerst den Verweis, dann die Position.",
            look=[
                "Kind zuerst: das erste DELETE (Referenz) ist fertig.",
                "Im zweiten DELETE nach WHERE id = dieselbe UUID in Anführungszeichen eintragen, dann ein Semikolon.",
                "Danach Kontroll-SELECT und COMMIT — beides steht schon.",
            ],
            starter="SELECT id, task_position_id\nFROM instance_1.flowapp_demo_task_position_reference\nWHERE task_position_id = 'aaaaaaab-0000-0000-0000-000000000002';\n\nBEGIN;\nDELETE FROM instance_1.flowapp_demo_task_position_reference\nWHERE task_position_id = 'aaaaaaab-0000-0000-0000-000000000002';\n\nDELETE FROM instance_1.flowapp_demo_task_position\nWHERE id =\n\nSELECT id\nFROM instance_1.flowapp_demo_task_position\nWHERE id = 'aaaaaaab-0000-0000-0000-000000000002';\n\nCOMMIT;\n",
            hints=[
                "Die Eltern-Zeile hat dieselbe UUID in der Spalte id: 'aaaaaaab-0000-0000-0000-000000000002'.",
                "DELETE FROM instance_1.flowapp_demo_task_position WHERE id = 'aaaaaaab-0000-0000-0000-000000000002';",
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
            why="Bevor eine große Abfrage gebaut wird, schaust du eine Zeile an — so prüfst du den Spaltennamen, ohne die ganze Tabelle zu laden.",
            task="Zeig den Lagerort einer Handling Unit, aber nur eine Zeile.",
            look=[
                "Rechts Handling-Unit aufklappen.",
                "storage_location_id klicken — nicht location_id, die Spalte heißt länger.",
                "LIMIT 1 steht schon.",
            ],
            starter="SELECT\n  \nFROM instance_1.flowapp_demo_handling_unit\nLIMIT 1;\n",
            hints=[
                "Die Lagerort-Spalte heißt storage_location_id — nicht location_id.",
                "LIMIT 1 steht schon; du brauchst nur die Spalte nach SELECT.",
            ],
            solution="SELECT storage_location_id FROM instance_1.flowapp_demo_handling_unit LIMIT 1;",
        ),
        EX(
            "i-ex2",
            why="Vor Metabase testest du mit LIMIT, damit eine Tippfehler-Query nicht die Replica killt.",
            task="Zeig interne HU-Nummer und Lagerort der Handling Units, höchstens zwei Zeilen.",
            look=[
                "Spalten: handling_unit_number und storage_location_id.",
                "LIMIT 2 selbst setzen — nicht die ganze Tabelle ziehen.",
            ],
            starter="-- Erst eine Mini-Stichprobe, dann die große Query.\n\n",
            hints=[
                "Zwei Spalten, dann LIMIT 2.",
                "Tabelle instance_1.flowapp_demo_handling_unit.",
            ],
            require=["LIMIT"],
            solution="SELECT handling_unit_number, storage_location_id FROM instance_1.flowapp_demo_handling_unit LIMIT 2;",
        ),
    ],
    quiz=[
        {"q": "Was prüfst du, bevor du einen JOIN schreibst?", "options": ["Nur den Tabellennamen", "Spaltennamen und Datentypen der Naht (UUID vs. integer)", "Ob Metabase online ist", "Die Farbe des Dashboards"], "correct": 1, "explain": "integer = uuid knallt. Erst Schema, dann JOIN."},
        {"q": "Warum zuerst LIMIT im Playground?", "options": ["LIMIT ist Pflicht in Postgres", "Kleine Stichprobe, bevor eine teure Query die Replica belastet", "Ohne LIMIT kommt immer 0 Zeilen", "Metabase ignoriert LIMIT"], "correct": 1, "explain": "Punkt 5 im Ablauf: erst klein testen."},
        {"q": "Wo prüfst du echte FK-Constraints?", "options": ["Nur Schema-CSV", "pg_constraint / Systemkataloge", "Im Auftragstext", "Gar nicht, FKs sind immer erzwungen"], "correct": 1, "explain": "Die CSV ist unvollständig. Viele Beziehungen sind fachlich, nicht technisch."},
        {"q": "Daten ändern: welches Muster?", "options": ["Direkt DELETE ohne SELECT", "SELECT → BEGIN → Änderung → Verifikation → COMMIT (Teil G)", "Nur ROLLBACK", "DROP TABLE"], "correct": 1, "explain": "Ohne Ausnahme, auch in der Lern-App."},
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
            why="Ein Drucker-Job ist fehlgeschlagen. Die Events liegen nicht bei den Aufträgen, sondern im Print-Schema.",
            task="Zeig Ereignistyp und Inhalt der Druck-Events.",
            look=[
                "Rechts „Druck-Event“ aufklappen — die Tabelle liegt in subscription, nicht in instance_1.",
                "event_type klicken, dann payload klicken.",
            ],
            starter="SELECT\n  \nFROM subscription.processevents_printer;\n",
            hints=[
                "Zwei Spalten: event_type, payload. Kein instance_1 und kein flowapp_demo_ davor.",
                "FROM steht schon. Nur die beiden Spaltennamen nach SELECT.",
            ],
            solution="SELECT event_type, payload FROM subscription.processevents_printer;",
        ),
        EX(
            "k-ex2",
            why="Bestand und Artikelstamm haben unterschiedliche Mengeneinheiten — Reports zeigen dann falsche Stückzahlen.",
            task="Zeig Position, Bestandseinheit und Artikeleinheit, nur wo die beiden Einheiten nicht zusammenpassen. Nur die neueste Bestandszeile je Position.",
            look=[
                "Neueste Qualifikation: ROW_NUMBER je handling_unit_position_id, ORDER BY updated_date DESC, rn = 1.",
                "Einheit am Bestand: stock_quant.quantity_unit_id → quantity_unit.alias.",
                "Einheit am Stamm: handling_unit_position → item_master.quantity_unit_id → quantity_unit.alias. Vergleich mit <> .",
            ],
            starter="-- Pro Position nur die neueste stock_quant-Zeile, dann Einheiten vergleichen.\n-- Tabellen: stock_quant, handling_unit_position, item_master, quantity_unit (zweimal).\n\n",
            hints=[
                "CTE mit ROW_NUMBER() OVER (PARTITION BY handling_unit_position_id ORDER BY updated_date DESC).",
                "Zwei Joins auf quantity_unit: eine über den Bestand, eine über den Artikelstamm. WHERE rn = 1 AND die alias-Werte ungleich.",
            ],
            require=["ROW_NUMBER"],
            solution="WITH ranked AS (SELECT sq.*, ROW_NUMBER() OVER (PARTITION BY sq.handling_unit_position_id ORDER BY sq.updated_date DESC) AS rn FROM instance_1.flowapp_demo_stock_quant sq) SELECT r.handling_unit_position_id, qu_stock.alias AS bestand_einheit, qu_item.alias AS artikel_einheit FROM ranked r JOIN instance_1.flowapp_demo_handling_unit_position hup ON hup.id = r.handling_unit_position_id JOIN instance_1.flowapp_demo_item_master im ON im.id = hup.item_master_id JOIN instance_1.flowapp_demo_quantity_unit qu_stock ON qu_stock.id = r.quantity_unit_id JOIN instance_1.flowapp_demo_quantity_unit qu_item ON qu_item.id = im.quantity_unit_id WHERE r.rn = 1 AND qu_stock.alias <> qu_item.alias;",
        ),
        EX(
            "k-ex3",
            why="Test und Prod haben verschiedene interne IDs. Zum Abgleich braucht ihr den Mandanten-Code plus einen Hash der ganzen Zeile.",
            task="Zeig Mandanten-Code und Fingerprint jeder Mandantenzeile.",
            look=[
                "code steht schon. In der zweiten Spalte den Hash eintragen.",
                "Muster: MD5(to_jsonb(c)::text) — c ist der Tabellenname im FROM.",
            ],
            starter="SELECT\n  code,\n  \nFROM instance_1.flowapp_demo_client c;\n",
            hints=[
                "Zweite Spalte: MD5(to_jsonb(c)::text) AS fingerprint",
                "c ist der Alias im FROM. to_jsonb macht die ganze Zeile zum JSON, MD5 daraus ist der Fingerprint.",
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
            task="Zeig Nummer und Status aller Aufträge, die nicht storniert sind.",
            look=[
                "Nummer und Status stehen schon. Es fehlt der Filter nach WHERE.",
                "Storniert ist der Text 'X0'. Alles außer diesem Status: task_status <> 'X0'",
            ],
            starter="SELECT order_number, task_status\nFROM instance_1.flowapp_demo_order_head\nWHERE\n  \n",
            hints=[
                "Ungleich schreibt man <>. Der Status ist Text, also mit Anführungszeichen.",
                "WHERE task_status <> 'X0'",
            ],
            solution="SELECT order_number, task_status FROM instance_1.flowapp_demo_order_head WHERE task_status <> 'X0';",
        ),
        EX(
            "l-ex2",
            why="Verladestatus kann '--' heißen (Feld gilt für diesen Auftrag nicht). Ein direkter Vergleich mit 80 würde das falsch werten.",
            task="Zeig Nummer und Verladestatus der Aufträge, die fachlich fertig verladen sind.",
            look=[
                "Die Umwandlung von '--' nach '00' steht schon in der WHERE-Zeile.",
                "Nach dem Gleichheitszeichen '80' eintragen — das ist abgeschlossen.",
            ],
            starter="SELECT order_number, loading_status\nFROM instance_1.flowapp_demo_order_head\nWHERE COALESCE(NULLIF(loading_status, '--'), '00') =\n",
            hints=[
                "Abgeschlossen ist der Text '80'.",
                "WHERE COALESCE(NULLIF(loading_status, '--'), '00') = '80'",
            ],
            solution="SELECT order_number, loading_status FROM instance_1.flowapp_demo_order_head WHERE COALESCE(NULLIF(loading_status, '--'), '00') = '80';",
        ),
        EX(
            "l-ex3",
            why="Zu Sendung SHP-01 gehören mehrere Warenausgänge plus eine Kopfzeile. Die Kopfzeile soll nicht in der Liste stehen.",
            task="Zeig Nummer und Verladestatus der Warenausgänge von SHP-01, ohne die Sendungs-Kopfzeile.",
            look=[
                "Sendungsnummer und JOINs stehen schon.",
                "Nach oc.alias <> den Typ der Kopfzeile ausschließen: 'sendung'",
            ],
            starter="SELECT oh.order_number, oh.loading_status\nFROM instance_1.flowapp_demo_order_head oh\nJOIN instance_1.flowapp_demo_order_class oc\n  ON oc.id = oh.order_class_id\nWHERE oh.shipment_number = 'SHP-01'\n  AND oc.alias <> \n",
            hints=[
                "Die Kopfzeile hat oc.alias = 'sendung'. Die willst du nicht: <> 'sendung'.",
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
            why="Warenausgänge sollen über den lesbaren Klassennamen gefiltert werden — nie über eine interne ID, die zwischen Test und Prod wechselt.",
            task="Zeig Auftragsnummer und Mandanten-Kürzel aller Warenausgänge.",
            look=[
                "JOINs und SELECT stehen schon. Es fehlt der Filter.",
                "Nach oc.alias = den Text 'warenausgang' eintragen.",
                "Rechts „Klasse (Auftrag)“ aufklappen, wenn du den alias nachschlagen willst.",
            ],
            starter="SELECT oh.order_number, c.alias\nFROM instance_1.flowapp_demo_order_head oh\nJOIN instance_1.flowapp_demo_order_class oc ON oc.id = oh.order_class_id\nJOIN instance_1.flowapp_demo_client c ON c.id = oh.client_id\nWHERE oc.alias =\n",
            hints=[
                "Warenausgang heißt in den Stammdaten 'warenausgang'.",
                "WHERE oc.alias = 'warenausgang'",
            ],
            solution="SELECT oh.order_number, c.alias FROM instance_1.flowapp_demo_order_head oh JOIN instance_1.flowapp_demo_order_class oc ON oc.id = oh.order_class_id JOIN instance_1.flowapp_demo_client c ON c.id = oh.client_id WHERE oc.alias = 'warenausgang';",
        ),
        EX(
            "m-ex2",
            why="Bevor du Adressen filterst, schaust du nach, welche Kurznamen die Kategorien wirklich haben.",
            task="List die Kurznamen und die deutsche Bezeichnung aller Adresskategorien.",
            look=[
                "alias steht schon. Rechts Kategorie (Adresse) aufklappen → name klicken.",
                "Dahinter tippen: ->>'de' — so kommt der deutsche Text aus dem JSON.",
            ],
            starter="SELECT\n  alias,\n  \nFROM instance_1.flowapp_demo_address_category;\n",
            hints=[
                "Zweite Spalte: name->>'de' AS bezeichnung — kein JOIN nötig.",
                "name ist JSONB. ->>'de' holt den deutschen Text, ohne zweite Tabelle.",
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
            why="Für die Verladeplanung braucht ihr den Palettentyp je Artikel, lesbar — nicht den technischen Kurznamen.",
            task="Zeig deutsche Artikelbezeichnung und Palettentyp der Ebene 3. palette-typ-a/b als Typ A/Typ B, sonst den Rohwert.",
            look=[
                "Die JOINs und Ebene 3 stehen schon. Die Bezeichnung auch.",
                "In der zweiten Spalte das CASE aus dem Lerntext eintragen: palette-typ-a → Typ A, palette-typ-b → Typ B, sonst bu.alias.",
            ],
            starter="SELECT\n  im.designation_a->>'de' AS bezeichnung,\n  \nFROM instance_1.flowapp_demo_item_master im\nJOIN instance_1.flowapp_demo_packaging_structure ps ON ps.parent_id = im.id\nJOIN instance_1.flowapp_demo_packaging_structure_pos psp ON psp.packaging_structure_id = ps.id\nJOIN instance_1.flowapp_demo_bundling_unit bu ON bu.id = psp.bundling_unit_id\nWHERE psp.packaging_level = 3;\n",
            hints=[
                "Der Palettentyp kommt aus bu.alias und wird mit CASE übersetzt.",
                "CASE bu.alias WHEN 'palette-typ-a' THEN 'Typ A' WHEN 'palette-typ-b' THEN 'Typ B' ELSE bu.alias END AS hu_typ",
            ],
            solution="SELECT im.designation_a->>'de' AS bezeichnung, CASE bu.alias WHEN 'palette-typ-a' THEN 'Typ A' WHEN 'palette-typ-b' THEN 'Typ B' ELSE bu.alias END AS hu_typ FROM instance_1.flowapp_demo_item_master im JOIN instance_1.flowapp_demo_packaging_structure ps ON ps.parent_id = im.id JOIN instance_1.flowapp_demo_packaging_structure_pos psp ON psp.packaging_structure_id = ps.id JOIN instance_1.flowapp_demo_bundling_unit bu ON bu.id = psp.bundling_unit_id WHERE psp.packaging_level = 3;",
        ),
        EX(
            "n-ex2",
            why="Die Basisverpackung (Ebene 0) hat Nettogewicht — ohne CASE, nur die Zahl.",
            task="Zeig deutsche Artikelbezeichnung und Nettogewicht in Gramm der Verpackungsebene 0.",
            look=[
                "packaging_level = 0 ist die kleinste Ebene. Nettogewicht: net_weight_g.",
                "Struktur hängt am Artikel: packaging_structure.parent_id = item_master.id.",
            ],
            starter="-- Ebene 0, Nettogewicht.\n\n",
            hints=[
                "Joins: item_master → packaging_structure → packaging_structure_pos.",
                "WHERE psp.packaging_level = 0. Spalte net_weight_g.",
            ],
            solution="SELECT im.designation_a->>'de' AS bezeichnung, psp.net_weight_g FROM instance_1.flowapp_demo_item_master im JOIN instance_1.flowapp_demo_packaging_structure ps ON ps.parent_id = im.id JOIN instance_1.flowapp_demo_packaging_structure_pos psp ON psp.packaging_structure_id = ps.id WHERE psp.packaging_level = 0;",
        ),
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
            why="Zoll will je Bestand Tarifnummer, Ursprungsland und Zollstatus — immer die aktuelle Bestandszeile.",
            task="Zeig deutsche Bezeichnung, TARIC, ISO-Ursprungsland und Zollstatus. Nur die neueste Zeile je Position.",
            look=[
                "Bezeichnung: item_master.designation_a->>'de'. TARIC am Stamm.",
                "Ursprung: stock_quant.country_of_origin_id → country_code.iso_code. Zollstatus: customs_status_profile.alias.",
                "Wie in Teil A: ROW_NUMBER je handling_unit_position_id, rn = 1.",
            ],
            starter="-- Neueste stock_quant-Zeile je Position, dann Artikel, Land, Zollstatus joinen.\n\n",
            hints=[
                "CTE mit ROW_NUMBER wie in Teil A, außen WHERE rn = 1.",
                "Joins: handling_unit_position, item_master, country_code, customs_status_profile.",
            ],
            require=["ROW_NUMBER"],
            solution="WITH ranked AS (SELECT sq.*, ROW_NUMBER() OVER (PARTITION BY sq.handling_unit_position_id ORDER BY sq.updated_date DESC) AS rn FROM instance_1.flowapp_demo_stock_quant sq) SELECT im.designation_a->>'de' AS bezeichnung, im.customs_tariff_number_taric AS taric, cc.iso_code AS ursprungsland, csp.alias AS zollstatus FROM ranked r JOIN instance_1.flowapp_demo_handling_unit_position hup ON hup.id = r.handling_unit_position_id JOIN instance_1.flowapp_demo_item_master im ON im.id = hup.item_master_id JOIN instance_1.flowapp_demo_country_code cc ON cc.id = r.country_of_origin_id JOIN instance_1.flowapp_demo_customs_status_profile csp ON csp.id = r.customs_status_id WHERE r.rn = 1;",
        ),
        EX(
            "o-ex2",
            why="Für Auftrag 100504_A braucht der Zoll die Lieferadresse, nicht die Rechnungsadresse.",
            task="Zeig Kategorie, Name und Ländercode der Lieferadresse von Auftrag 100504_A.",
            look=[
                "Auftrag, JOINs und SELECT stehen. Der Auftrag ist schon gefiltert.",
                "Nach ac.alias = den Kurznamen der Lieferadresse eintragen: 'lieferadresse'",
            ],
            starter="SELECT ac.alias AS kategorie, ad.name, cc.iso_code\nFROM instance_1.flowapp_demo_order_head oh\nJOIN instance_1.flowapp_demo_address_data ad ON ad.parent_id = oh.id\nJOIN instance_1.flowapp_demo_address_category ac ON ac.id = ad.address_category_id\nJOIN instance_1.flowapp_demo_country_code cc ON cc.id = ad.country_id\nWHERE oh.order_number = '100504_A'\n  AND ac.alias =\n",
            hints=[
                "Die Kategorie heißt in den Stammdaten 'lieferadresse'.",
                "AND ac.alias = 'lieferadresse'",
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
            why="Eine Übersicht soll je Palette die Seriennummern zählen — Paletten ohne Nummer dürfen nicht verschwinden.",
            task="Zeig je Handling Unit die interne Nummer, die Anzahl verschiedener Seriennummern und die sortierte Liste mit Semikolon.",
            look=[
                "LEFT JOIN und GROUP BY stehen schon, damit leere Paletten bleiben.",
                "handling_unit_id und die Anzahl stehen. In der dritten Spalte die Liste bauen: STRING_AGG(DISTINCT psn.serial_number, '; ' ORDER BY psn.serial_number)",
            ],
            starter="SELECT\n  hu.handling_unit_id,\n  COUNT(DISTINCT psn.serial_number) AS anzahl_seriennummern,\n  \nFROM instance_1.flowapp_demo_handling_unit hu\nJOIN instance_1.flowapp_demo_handling_unit_position hup ON hu.id = hup.handling_unit_id\nLEFT JOIN instance_1.flowapp_demo_hu_position_serial_number psn ON hup.id = psn.parent_id\nGROUP BY hu.handling_unit_id;\n",
            hints=[
                "STRING_AGG klebt die Nummern aneinander. DISTINCT und ORDER BY gehören hinein.",
                "STRING_AGG(DISTINCT psn.serial_number, '; ' ORDER BY psn.serial_number) AS seriennummern_liste",
            ],
            solution="SELECT hu.handling_unit_id, COUNT(DISTINCT psn.serial_number) AS anzahl_seriennummern, STRING_AGG(DISTINCT psn.serial_number, '; ' ORDER BY psn.serial_number) AS seriennummern_liste FROM instance_1.flowapp_demo_handling_unit hu JOIN instance_1.flowapp_demo_handling_unit_position hup ON hu.id = hup.handling_unit_id LEFT JOIN instance_1.flowapp_demo_hu_position_serial_number psn ON hup.id = psn.parent_id GROUP BY hu.handling_unit_id;",
        ),
        EX(
            "p-ex2",
            why="Auf dem Label soll die externe Tracking-Nummer stehen, falls vorhanden — sonst die interne HU-Nummer.",
            task="Zeig je Handling Unit die interne Nummer und die Anzeige-Kennung (externe Tracking-Nummer oder interne Nummer).",
            look=[
                "Die JOINs und die interne Nummer stehen schon.",
                "Zweite Spalte: CASE WHEN t.alias = 'externe-tracking-nummer' THEN i.handling_unit_identification ELSE hu.handling_unit_number END",
            ],
            starter="SELECT\n  hu.handling_unit_number,\n  \nFROM instance_1.flowapp_demo_handling_unit hu\nLEFT JOIN instance_1.flowapp_demo_handling_unit_identification i ON i.handling_unit_id = hu.id\nLEFT JOIN instance_1.flowapp_demo_handling_unit_identification_type t ON t.id = i.identification_type_id;\n",
            hints=[
                "Wenn der Typ externe-tracking-nummer ist, nimm i.handling_unit_identification, sonst die interne Nummer.",
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
