# PostgreSQL & FlowApp/WMX — Interaktive Einarbeitung

Lern-App aus der Einarbeitungs-Dokumentation `PostgreSQL_FlowApp_Einarbeitung.docx`.
Die Datei ist die **Wissensbasis** für alle Inhalte (Teile A–P plus Glossar).

- **16 Lektionen:** Einstieg A–J, Vertiefung K–P (Eigenheiten, Status/Sendung, Alias-Filter, Verpackung, Zoll, Tracking)
- **SQL-Übungen im Browser** (SELECT, UPDATE, DELETE) mit Prüfung gegen eine Musterlösung
- **Kurz-Quiz und Karteikarten**
- **Durchsuchbare Wissensbasis** (`/wissen`) über alle Abschnitte, Tabellen und Begriffe
- **Übungs-PostgreSQL**, die die FlowApp/WMX-Struktur nachbildet (Schema `instance_1`, Präfix `flowapp_demo_`, Schema `subscription`)

Alles läuft in der App. Die Beispieldaten setzt du bei Bedarf über **Datenbank zurücksetzen** zurück.

## Windows-Installer (für Kollegen)

Kein Docker, kein Python, keine Admin-Rechte. Setup bauen:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\build.ps1
```

Danach liegt `dist\plx.learnSQL-Setup.exe` bereit — diese Datei an den Kollegen schicken.
Installation: Doppelklick, Assistent durchklicken, Desktop-Verknüpfung **plx.learnSQL** starten.
Beim ersten Start wird die Lern-Datenbank einmalig eingerichtet, danach öffnet sich http://localhost:8080.

SmartScreen kann bei einer unsignierten EXE warnen: „Weitere Informationen“ → „Trotzdem ausführen“.

## Starten (Entwicklung mit Docker)

Voraussetzung: Docker + Docker Compose.

```bash
docker compose up --build
```

Danach:

- **Lern-App:** http://localhost:8080
- **Wissensbasis:** http://localhost:8080/wissen

Zum Stoppen: `Ctrl+C`, danach `docker compose down` (mit `-v` werden auch die DB-Daten gelöscht,
damit die Datenbank beim nächsten Start wieder mit den Ausgangsdaten neu initialisiert wird).

Nach Schema-Änderungen immer mit frischem Volume starten:

```bash
docker compose down -v
docker compose up --build
```

## Projektstruktur

```
flowapp-learn/
├── docker-compose.yml
├── db/
│   └── init/01_schema_and_data.sql   # Schema + Beispieldaten + Lern-User "lernuser"
└── app/
    ├── Dockerfile
    ├── requirements.txt
    ├── app.py                        # Flask-Backend (Lektionen, SQL-Sandbox, Suche)
    ├── lessons/lessons.json          # Wissensbasis: Lerninhalte, Übungen, Quiz
    ├── lessons/generate.py           # regeneriert lessons.json aus der Doku-Struktur
    ├── templates/
    └── static/
```

## Hinweise

- Die SQL-Sandbox erlaubt SELECT, INSERT, UPDATE und DELETE (plus BEGIN/COMMIT).
  Schema-Änderungen (DROP/ALTER/CREATE) sind gesperrt.
- Diese Datenbank ist eine **didaktisch vereinfachte Nachbildung** der echten Struktur.
- Inhalte kommen aus der Einarbeitungs-Dokumentation. Anpassungen an den Texten
  in `app/lessons/generate.py` vornehmen und das Skript ausführen, oder direkt
  `lessons.json` editieren.
