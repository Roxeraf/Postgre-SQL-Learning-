# plx.learnSQL — PostgreSQL interaktiv lernen

Ein Lernpfad in der App: von der ersten Tabelle bis zu JOIN, Gruppen, Änderungen und den Konzepten hinter PostgreSQL.

- Interaktive Akademie (verstehen → vorhersagen → bauen → schreiben → anwenden)
- Zusatz-Kapitel zu Aggregaten, Positionen, CASE und Unterabfragen
- Kurz-Quiz nach jedem Kapitel
- SQL-Playground für Zusatzübungen von Claude (MCP)
- PostgreSQL-Bibel unter `/wissen` (eigene Artikel, nicht das alte Mini-Glossar)
- Karteikarten mit Leitner (Nochmal / Schwer / Sitzt) in localStorage
- MCP für Claude Desktop und Claude Code: Lern-Buddy auf dem Pfad, Zusatzübungen im SQL-Playground

Trainingsdaten setzt du bei Bedarf über **Datenbank zurücksetzen** zurück.

## Windows-Installer (für Kollegen)

Kein Docker, kein Python, keine Admin-Rechte. Setup bauen:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\build.ps1
```

Danach liegt `dist\plx.learnSQL-Setup.exe` bereit — diese Datei an den Kollegen schicken.
Installation: Doppelklick, Assistent durchklicken, Desktop-Verknüpfung **plx.learnSQL** starten.
Beim ersten Start wird die Lern-Datenbank einmalig eingerichtet, danach öffnet sich http://localhost:8080.
Das Setup trägt das MCP in Claude Desktop und Claude Code ein — Claude danach einmal komplett neu starten.
Kurzanleitung: `mcp/ANLEITUNG.md` oder in der App **SQL-Playground**.

SmartScreen kann bei einer unsignierten EXE warnen: „Weitere Informationen“ → „Trotzdem ausführen“.

## Starten (Entwicklung mit Docker)

Voraussetzung: Docker + Docker Compose.

```bash
docker compose up --build
```

Danach:

- **Lern-App:** http://localhost:8080
- **Pfad:** http://localhost:8080/learn/ch0
- **Wissensbasis:** http://localhost:8080/wissen
- **Karten:** http://localhost:8080/cards
- **SQL-Playground:** http://localhost:8080/playground

Zum Stoppen: `Ctrl+C`, danach `docker compose down` (mit `-v` werden auch die DB-Daten gelöscht,
damit die Datenbank beim nächsten Start wieder mit den Ausgangsdaten neu initialisiert wird).

Nach Schema-Änderungen immer mit frischem Volume starten:

```bash
docker compose down -v
docker compose up --build
```

## Projektstruktur

```
├── docker-compose.yml
├── db/init/01_schema_and_data.sql   # Schema learn
├── data/workshop/                   # Dynamische Übungen (MCP), nicht der offizielle Pfad
├── mcp/learnsql_mcp.py              # MCP für Claude Desktop / Claude Code
└── app/
    ├── app.py                       # Flask-Backend
    ├── sql_coach.py                 # Lernfeedback statt Roh-Postgres-Fehler
    ├── lessons/academy_data.py      # Offizieller Pfad
    ├── lessons/path_more.py         # Zusatz-Kapitel
    ├── lessons/knowledge/           # Bibel-Artikel und Karten
    └── templates/
```

### MCP (Claude Desktop, Claude Code)

Die App ruft kein LLM auf. Claude hängt als Client am MCP: als **Lern-Buddy** auf dem offiziellen Pfad (Fragen erklären, SQL prüfen) und als Autor **zusätzlicher Übungen** im SQL-Playground.

In der App: Knopf **Claude** oder in der Seitenleiste **Claude-Buddy**. Der Prompt wird kopiert; Claude Code / Desktop liest über `buddy_context`, wo du gerade bist.

Was du sagen kannst: „Erklär mir diesen Schritt, ohne die Lösung zu verraten.“ oder „Bau mir drei Playground-Übungen zu offenen Aufträgen mit GROUP BY — mit explain-Schritt und teach.“ Alte Karten löschst du in der App oder sagst Claude `delete_practice`.

Claude soll zuerst `buddy_context` (Lernen) oder `exercise_context` (Playground-Übungen) lesen. Übungen brauchen einen **explain**-Schritt (Alltagssprache + antippenbare SQL-Teile) und `teach` an den Schreib-Schritten. Vor dem Speichern `validate_exercise`. Extra-Tabellen in `learn` verschwinden beim Zurücksetzen (`DROP SCHEMA learn CASCADE`).

Schritt-für-Schritt: [mcp/ANLEITUNG.md](mcp/ANLEITUNG.md)

- Windows-Setup trägt Claude Desktop und Claude Code automatisch ein.
- Claude Code: `claude mcp add --scope user --transport stdio learnsql -- python mcp/learnsql_mcp.py`

Docker hängt `data/workshop` nach `/data/workshop` (`WORKSHOP_DIR`). Die Windows-App nutzt `{app}\workshop` und liest den Datenbank-Port aus `runtime.json`.

## Hinweise

- Sandbox `learn`: SELECT, WITH, EXPLAIN, plus INSERT/UPDATE/DELETE und BEGIN/COMMIT/ROLLBACK. Schema-Änderungen sind gesperrt.
- SQL-Aufgaben werden über das **Abfrageergebnis** bewertet, nicht über einen exakten Musterstring.
- Tabellen: `orders`, `clients`, `stock`, `order_items`.
