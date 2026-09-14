# MCP für Claude — Buddy auf dem Pfad, Übungen daneben

Claude kennt das Lager (`orders`, `clients`, `stock`, `order_items`), den **offiziellen Lernpfad** und die Bibel.

Zwei Rollen:

1. **Lern-Buddy** überall in der App (Kapitel, Bibel, Karten, Playground). In der App **Claude** antippen und direkt fragen — die App startet dafür im Hintergrund die `claude`-Kommandozeile mit genau diesem MCP. Claude liest `buddy_context` (Kapitel, Schritt, letzte Query). Dieselben Werkzeuge hast du auch in Claude Desktop, wenn du lieber dort arbeitest.
2. **Zusatzübungen** in den SQL-Playground schreiben. Der offizielle Lernpfad bleibt unverändert. Übungen brauchen jetzt eine richtige Erklärung: `explain` mit Alltagssprache (`plain`) und antippenbaren SQL-Teilen (`parts`), plus `teach` an den Schreib-Schritten.

Die App enthält kein Modell und keinen API-Key. Sie startet die lokale Claude-Code-Kommandozeile
(dein normales Abo) und reicht ihr denselben MCP-Server durch. Claude Desktop bleibt daneben der
zweite Weg — beide sehen dieselben Daten.

## Der Buddy in der App

- Nur `learnsql`-Werkzeuge: keine Datei-, Shell- oder Web-Zugriffe.
- Ein Lauf gleichzeitig. **Stopp** bricht ab, **Neues Gespräch** vergisst den Verlauf.
- Steht dort „Claude Code nicht gefunden": `npm install -g @anthropic-ai/claude-code`, einmal
  `claude` starten und anmelden, App neu starten. Eigener Pfad über `CLAUDE_CLI`.

**Voraussetzung:** plx.learnSQL (oder Docker) muss laufen, bevor Claude SQL-Werkzeuge nutzt.
Bibel lesen, Standort (`buddy_context`) und Übungen speichern geht auch ohne Datenbank.

## Was du Claude sagst

Kopieren und anpassen:

- Ich bin im Lernpfad. Lies `buddy_context` und erklär mir den aktuellen Schritt, ohne die Lösung zu verraten.
- Meine Query gibt das Falsche zurück. `coach_sql` — was übersehe ich?
- Welche Bibel-Stelle passt zu JOIN?
- Bau mir drei Playground-Übungen zu offenen Aufträgen mit GROUP BY — mit explain-Schritt und teach.
- Eine LEFT-JOIN-Übung, bei der 4730 ohne Kunde sichtbar bleibt.
- Prüf die Musterlösung mit run_sql, dann speichern.
- Lösch die vier alten Übungen zu GROUP BY.

Danach in der App **SQL-Playground** öffnen und die neue Karte anklicken. Überflüssige Karten löschst du am Knopf auf der Karte oder lässt Claude `delete_practice` nutzen.

Als Buddy: zuerst `buddy_context`, Fragen mit `help_with` / `search_path`, SQL mit `coach_sql`.
(Der Buddy in der App bekommt das schon über seinen Systemprompt mit.)

Als Übungsautor: zuerst `exercise_context` (Übungsdesign, Live-Sandbox, Beispiel, Ziel-URL).
Tabellenzeilen kommen über `table_rows`, IDs über `run_sql` mit `as_ids`.
Vor dem Speichern prüft `validate_exercise` — ohne `explain` (plain + parts) und ohne `teach` am Schreib-Schritt wird nicht gespeichert.
`save_practice` legt die Karte unter `/playground/{id}` ab und bestätigt, dass die laufende App sie sieht. `draft_exercise` ist nur ein Gerüst.

Beim Zurücksetzen baut die App das Schema `learn` per `DROP SCHEMA learn CASCADE` neu auf.
Zusätzliche Tabellen in `learn` sind danach weg.

## Windows-Installer

Setup und der erste App-Start tragen `learnsql` automatisch ein — in Claude Desktop
(`%APPDATA%\Claude\claude_desktop_config.json`) und in Claude Code
(`%USERPROFILE%\.claude.json`). Andere MCP-Server bleiben unverändert.

**Claude einmal komplett beenden** (auch das Symbol unten rechts) und neu starten.
In Claude Desktop unter Einstellungen → Developer sollte `learnsql` stehen.

## Manuell: Claude Desktop

1. Claude → Settings → Developer → Edit Config
2. Im JSON unter `mcpServers` den Block `learnsql` einfügen (andere Server nicht löschen)
3. Claude komplett beenden und neu starten

Windows (Installer, feste Pfade — `{app}` durch dein Installationsverzeichnis ersetzen, meist `%LOCALAPPDATA%\plx.learnSQL`):

```json
{
  "mcpServers": {
    "learnsql": {
      "command": "C:/Users/DU/AppData/Local/plx.learnSQL/python/python.exe",
      "args": ["-u", "C:/Users/DU/AppData/Local/plx.learnSQL/mcp/learnsql_mcp.py"],
      "env": {
        "DB_HOST": "127.0.0.1",
        "DB_NAME": "learnsql",
        "DB_USER": "lernuser",
        "DB_PASSWORD": "lernuser",
        "LEARN_SQL_HOME": "C:/Users/DU/AppData/Local/plx.learnSQL",
        "WORKSHOP_DIR": "C:/Users/DU/AppData/Local/plx.learnSQL/workshop"
      }
    }
  }
}
```

Wenn der Server danach nicht erscheint: dieselbe Datei zusätzlich nach
`%LOCALAPPDATA%\Packages\Claude_*\LocalCache\Roaming\Claude\claude_desktop_config.json`
legen. Die Schaltfläche „Edit Config“ öffnet manchmal die falsche Datei.

## Manuell: Claude Code

Im Terminal (einmal, Benutzer-weit):

```bash
claude mcp add --scope user --transport stdio learnsql -- python mcp/learnsql_mcp.py
```

Im installierten Windows-Paket `python` und das Skript durch die festen Pfade oben ersetzen.
Zusätzlich die `env`-Werte setzen (gleiche wie im JSON).

Oder in `%USERPROFILE%\.claude.json` denselben `mcpServers.learnsql`-Block eintragen.

Docker: App mit `docker compose up` starten. Übungen liegen in `data/workshop/`.
