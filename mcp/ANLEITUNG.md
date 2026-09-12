# MCP für Claude — Übungen neben dem Pfad

Claude kennt das Lager (`orders`, `clients`, `stock`, `order_items`) und die Bibel.
Er schreibt **zusätzliche Übungen** in die Werkstatt. Der offizielle Lernpfad bleibt unverändert.
Du öffnest sie in der App unter **Werkstatt** und löst sie wie ein normales Kapitel.

Die App ruft kein Sprachmodell auf. Claude hängt nur als Client am MCP.

**Voraussetzung:** plx.learnSQL (oder Docker) muss laufen, bevor Claude SQL-Werkzeuge nutzt.
Bibel lesen und Übungen speichern geht auch ohne Datenbank.

## Was du Claude sagst

Kopieren und anpassen:

- Bau mir drei Werkstatt-Übungen zu offenen Aufträgen mit GROUP BY.
- Eine LEFT-JOIN-Übung, bei der 4730 ohne Kunde sichtbar bleibt.
- Prüf die Musterlösung mit run_sql, dann speichern.

Danach in der App **Werkstatt** öffnen und die neue Karte anklicken.

## Windows-Installer

Wenn das Setup Claude Desktop gefunden hat, ist das MCP schon eingetragen.
**Claude einmal komplett beenden** (auch das Symbol unten rechts) und neu starten.
In Claude unter Einstellungen → Developer sollte `learnsql` stehen.

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
      "args": ["C:/Users/DU/AppData/Local/plx.learnSQL/mcp/learnsql_mcp.py"],
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

## Manuell: Cursor / Repo

Arbeitsverzeichnis = Projektordner. Vorlage: `mcp/cursor.mcp.example.json`.

```bash
python3 mcp/learnsql_mcp.py
```

Docker: App mit `docker compose up` starten. Übungen liegen in `data/workshop/`.
