# PostgreSQL & FlowApp/WMX — Interaktive Einarbeitung

Zwei Lernpfade in einer App:

1. **SQL Grundlagen** — interaktiver Trainer für komplette Anfänger
   (verstehen → vorhersagen → bauen → schreiben → anwenden)
2. **WMX Datenmodell** — bestehende Einarbeitung A–P gegen das FlowApp-Übungsschema

Die Datei `PostgreSQL_FlowApp_Einarbeitung.docx` bleibt die Wissensbasis für den WMX-Pfad.

- **SQL-Akademie:** Kapitel 0–6 plus Challenge, mit Explain / Predict / Build / Write
- **SQL-Übungen im Browser** gegen isoliertes Schema `learn` (nur SELECT) und gegen `instance_1` (WMX)
- **Kurz-Quiz und Karteikarten** (WMX)
- **Durchsuchbare Wissensbasis** (`/wissen`)
- **Playground** mit Training- und WMX-Tabellen, plus „Erkläre diese Query“

Trainingsdaten setzt du bei Bedarf über **Datenbank zurücksetzen** zurück.

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
- **SQL-Pfad:** http://localhost:8080/learn/ch0
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
│   └── init/01_schema_and_data.sql   # WMX-Schema + Anfänger-Schema learn
└── app/
    ├── app.py                        # Flask-Backend
    ├── sql_coach.py                  # Lernfeedback statt Roh-Postgres-Fehler
    ├── lessons/academy_data.py       # SQL-Grundlagen (interaktive Schritte)
    ├── lessons/lessons.json          # WMX-Einarbeitung A–P
    └── templates/
```

## Hinweise

- Anfänger-Sandbox (`learn`): nur `SELECT` / `WITH` / `EXPLAIN`. Tabellen: `orders`, `clients`, `stock`.
- WMX-Sandbox: SELECT, INSERT, UPDATE und DELETE (plus BEGIN/COMMIT). Schema-Änderungen sind gesperrt.
- SQL-Aufgaben werden über das **Abfrageergebnis** bewertet, nicht über einen exakten Musterstring.
- WMX-Inhalte kommen aus der Einarbeitungs-Dokumentation. Anfänger-Tabellen sind isolierte Trainingsdaten und **kein** Abbild des echten WMX-Schemas.
