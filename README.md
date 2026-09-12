# plx.learnSQL — PostgreSQL interaktiv lernen

Ein Lernpfad in der App: von der ersten Tabelle bis zu JOIN, Gruppen, Änderungen und den Konzepten hinter PostgreSQL.

- Interaktive Akademie (verstehen → vorhersagen → bauen → schreiben → anwenden)
- Zusatz-Kapitel zu Aggregaten, Positionen, CASE und Unterabfragen
- Kurz-Quiz nach jedem Kapitel
- SQL-Playground gegen Schema `learn`
- PostgreSQL-Bibel unter `/wissen` (eigene Artikel, nicht das alte Mini-Glossar)
- Karteikarten mit Leitner (Nochmal / Schwer / Sitzt) in localStorage
- Werkstatt für dynamische Übungen plus MCP für Claude Desktop, Claude Code und Cursor

Trainingsdaten setzt du bei Bedarf über **Datenbank zurücksetzen** zurück.

## Windows-Installer (für Kollegen)

Kein Docker, kein Python, keine Admin-Rechte. Setup bauen:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\build.ps1
```

Danach liegt `dist\plx.learnSQL-Setup.exe` bereit — diese Datei an den Kollegen schicken.
Installation: Doppelklick, Assistent durchklicken, Desktop-Verknüpfung **plx.learnSQL** starten.
Beim ersten Start wird die Lern-Datenbank einmalig eingerichtet, danach öffnet sich http://localhost:8080.
Wenn Claude Desktop installiert ist, trägt das Setup das MCP ein — Claude danach einmal komplett neu starten.
Kurzanleitung: `mcp/ANLEITUNG.md` oder in der App **Werkstatt**.

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
- **Werkstatt:** http://localhost:8080/werkstatt

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
├── mcp/learnsql_mcp.py              # MCP für Claude Code / Cursor
└── app/
    ├── app.py                       # Flask-Backend
    ├── sql_coach.py                 # Lernfeedback statt Roh-Postgres-Fehler
    ├── lessons/academy_data.py      # Offizieller Pfad
    ├── lessons/path_more.py         # Zusatz-Kapitel
    ├── lessons/knowledge/           # Bibel-Artikel und Karten
    └── templates/
```

### MCP (Claude Desktop, Claude Code, Cursor)

Die App ruft kein LLM auf. Claude hängt als Client am MCP und legt **zusätzliche Übungen** in die Werkstatt — der offizielle Pfad bleibt unverändert.

Was du sagen kannst: „Bau mir drei Werkstatt-Übungen zu offenen Aufträgen mit GROUP BY.“ Danach `/werkstatt` öffnen.

Schritt-für-Schritt: [mcp/ANLEITUNG.md](mcp/ANLEITUNG.md)

- Windows-Setup trägt Claude Desktop automatisch ein, wenn Claude gefunden wird.
- Claude Code: `claude mcp add --scope user --transport stdio learnsql -- python mcp/learnsql_mcp.py`
- Cursor / Repo: [mcp/cursor.mcp.example.json](mcp/cursor.mcp.example.json)

Docker hängt `data/workshop` nach `/data/workshop` (`WORKSHOP_DIR`). Die Windows-App nutzt `{app}\workshop` und liest den Datenbank-Port aus `runtime.json`.

## Hinweise

- Sandbox `learn`: SELECT, WITH, EXPLAIN, plus INSERT/UPDATE/DELETE und BEGIN/COMMIT/ROLLBACK. Schema-Änderungen sind gesperrt.
- SQL-Aufgaben werden über das **Abfrageergebnis** bewertet, nicht über einen exakten Musterstring.
- Tabellen: `orders`, `clients`, `stock`, `order_items`.
