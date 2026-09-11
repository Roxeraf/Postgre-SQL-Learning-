#!/bin/sh
# Läuft als Healthcheck im Postgres-Container.
# Legt learnsql auch dann an, wenn das Volume schon existiert
# (Init-Skripte in /docker-entrypoint-initdb.d laufen sonst nicht erneut).
set -eu
pg_isready -U postgres -d postgres >/dev/null
exists=$(psql -U postgres -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='learnsql'")
if [ "$exists" != "1" ]; then
  psql -U postgres -d postgres -c "CREATE DATABASE learnsql"
fi
