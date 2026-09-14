# plx.learnSQL — PostgreSQL interaktiv lernen

Ein Lernpfad in der App: von der ersten Tabelle bis zu JOIN, Gruppen, Änderungen und den Konzepten hinter PostgreSQL.

- Interaktive Akademie (verstehen → vorhersagen → bauen → schreiben → anwenden)
- Zusatz-Kapitel zu Aggregaten, Positionen, CASE und Unterabfragen
- Kurz-Quiz nach jedem Kapitel
- SQL-Playground für Zusatzübungen von Claude (MCP)
- PostgreSQL-Bibel unter `/wissen` (eigene Artikel, nicht das alte Mini-Glossar)
- Karteikarten mit Leitner (Nochmal / Schwer / Sitzt) in localStorage
- MCP für Claude Desktop und Claude Code, Übungen erscheinen im SQL-Playground

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

Die App ruft kein LLM auf. Claude hängt als Client am MCP und legt **zusätzliche Übungen** in den SQL-Playground — der offizielle Pfad bleibt unverändert.

Was du sagen kannst: „Bau mir drei Playground-Übungen zu offenen Aufträgen mit GROUP BY.“ Danach `/playground` öffnen. Alte Karten löschst du in der App oder sagst Claude `delete_practice`.

Claude soll zuerst `exercise_context` lesen, die Lösung mit `validate_exercise` prüfen und erst dann `save_practice` aufrufen. Extra-Tabellen in `learn` verschwinden beim Zurücksetzen (`DROP SCHEMA learn CASCADE`).

Schritt-für-Schritt: [mcp/ANLEITUNG.md](mcp/ANLEITUNG.md)

- Windows-Setup trägt Claude Desktop und Claude Code automatisch ein.
- Claude Code: `claude mcp add --scope user --transport stdio learnsql -- python mcp/learnsql_mcp.py`

Docker hängt `data/workshop` nach `/data/workshop` (`WORKSHOP_DIR`). Die Windows-App nutzt `{app}\workshop` und liest den Datenbank-Port aus `runtime.json`.

## Hinweise

- Sandbox `learn`: SELECT, WITH, EXPLAIN, plus INSERT/UPDATE/DELETE und BEGIN/COMMIT/ROLLBACK. Schema-Änderungen sind gesperrt.
- SQL-Aufgaben werden über das **Abfrageergebnis** bewertet, nicht über einen exakten Musterstring.
- Tabellen: `orders`, `clients`, `stock`, `order_items`.
