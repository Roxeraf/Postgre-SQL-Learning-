# plx.learnSQL — PostgreSQL interaktiv lernen

Ein Lernpfad in der App: von der ersten Tabelle bis zu JOIN, Gruppen, Änderungen und den Konzepten hinter PostgreSQL.

- Interaktive Akademie (verstehen → vorhersagen → bauen → schreiben → anwenden)
- Zusatz-Kapitel zu Aggregaten, Positionen, CASE und Unterabfragen
- Kurz-Quiz nach jedem Kapitel
- SQL-Playground für Zusatzübungen von Claude (MCP)
- PostgreSQL-Bibel unter `/wissen` (eigene Artikel, nicht das alte Mini-Glossar)
- Karteikarten mit Leitner (Nochmal / Schwer / Sitzt) in localStorage
- **Claude-Buddy in der App** — fragen und direkt im Drawer antworten lassen, über Claude Code auf diesem Rechner (kein API-Key)
- MCP für Claude Desktop und Claude Code: dieselben Werkzeuge, wenn du lieber im Client arbeitest

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

## Starten (Entwicklung)

Der Claude-Buddy startet die `claude`-Kommandozeile auf **demselben Rechner** wie Flask.
Im Container gibt es sie nicht (und dein Claude-Login liegt in `~/.claude`), deshalb läuft
in der Entwicklung nur Postgres in Docker:

```bash
docker compose up db

python3 -m venv .venv && . .venv/bin/activate
pip install -r app/requirements.txt

DB_HOST=127.0.0.1 DB_PORT=5432 \
WORKSHOP_DIR="$PWD/data/workshop" \
APP_HOST=127.0.0.1 \
python app/app.py
```

Voraussetzung für den Buddy — einmalig:

```bash
npm install -g @anthropic-ai/claude-code
claude          # einmal starten und anmelden
```

`docker compose up --build` (alles im Container) funktioniert weiter, nur bleibt der
Buddy-Drawer dann leer und zeigt „Claude Code nicht gefunden".

Eine Installation = eine lernende Person: Lernstand und Claude-Login hängen am Rechner.

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
    ├── claude_cli.py                # startet Claude Code für den Buddy-Chat
    ├── learn_db.py                  # Postgres-Sandbox (auch MCP, ohne Flask)
    ├── sql_coach.py                 # Lernfeedback statt Roh-Postgres-Fehler
    ├── lessons/academy_data.py      # Offizieller Pfad
    ├── lessons/path_more.py         # Zusatz-Kapitel
    ├── lessons/knowledge/           # Bibel-Artikel und Karten
    └── templates/
```

### Claude-Buddy (in der App)

Die App bringt kein eigenes Modell mit und braucht keinen API-Key. Für den Buddy startet sie die
lokale `claude`-Kommandozeile (Claude Code) als Unterprozess und hängt ihr denselben
`learnsql`-MCP an — es zählt dein normales Claude-Abo. Ohne installierte Claude-Code-CLI zeigt
der Drawer nur einen Hinweis.

In der App: Knopf **Claude** oder in der Seitenleiste **Claude-Buddy**. Frage eintippen, die
Antwort läuft Wort für Wort ein. Claude liest über `buddy_context`, wo du stehst, prüft deine
Query mit `coach_sql` und legt auf Wunsch Übungen in den SQL-Playground.

Der Buddy darf ausschließlich die `learnsql`-Werkzeuge benutzen — keine Datei-, Shell- oder
Web-Zugriffe. **Stopp** bricht ab, **Neues Gespräch** vergisst den Verlauf.

Einstellbar über Umgebungsvariablen:

| Variable | Bedeutung |
| --- | --- |
| `CLAUDE_CLI` | Eigener Pfad zur `claude`-Kommandozeile |
| `BUDDY_TIMEOUT` | Sekunden pro Antwort (Standard 180) |
| `BUDDY_MAX_RUNS` | Gleichzeitige Läufe (Standard 2) |

### MCP (Claude Desktop, Claude Code)

Derselbe MCP-Server lässt sich in Claude Desktop oder Claude Code eintragen, wenn du lieber
direkt dort arbeitest: als **Lern-Buddy** auf dem offiziellen Pfad (Fragen erklären, SQL prüfen)
und als Autor **zusätzlicher Übungen** im SQL-Playground.

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
