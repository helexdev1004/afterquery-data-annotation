#!/usr/bin/env bash
# Boot a local PostgreSQL instance and create the ledger role + database.
# Idempotent: safe to run again if the cluster is already up.
set -uo pipefail

PGBIN="${PGBIN:-/usr/lib/postgresql/15/bin}"
PGDATA="${PGDATA:-/var/lib/pgdata}"
LOGFILE="${PGLOG:-/var/log/ledger/postgres.log}"

mkdir -p "$(dirname "$LOGFILE")" "$PGDATA"
chown -R postgres:postgres "$PGDATA" "$(dirname "$LOGFILE")"

if [ ! -s "$PGDATA/PG_VERSION" ]; then
  su postgres -c "$PGBIN/initdb -D $PGDATA -A trust -E UTF8" >/dev/null 2>&1 || exit 1
fi

if ! su postgres -c "$PGBIN/pg_ctl -D $PGDATA status" >/dev/null 2>&1; then
  su postgres -c "$PGBIN/pg_ctl -D $PGDATA -l $LOGFILE -w -t 60 \
      -o '-c listen_addresses=127.0.0.1 -p 5432 -c max_connections=200 -c fsync=off -c synchronous_commit=off' \
      start" >/dev/null 2>&1 || exit 1
fi

for _ in $(seq 1 60); do
  if su postgres -c "$PGBIN/pg_isready -h 127.0.0.1 -p 5432" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

su postgres -c "psql -h 127.0.0.1 -tAc \"SELECT 1 FROM pg_roles WHERE rolname='ledger'\"" 2>/dev/null \
  | grep -q 1 || su postgres -c "psql -h 127.0.0.1 -c \"CREATE ROLE ledger LOGIN SUPERUSER\"" >/dev/null 2>&1

su postgres -c "psql -h 127.0.0.1 -tAc \"SELECT 1 FROM pg_database WHERE datname='ledger'\"" 2>/dev/null \
  | grep -q 1 || su postgres -c "createdb -h 127.0.0.1 -O ledger ledger" >/dev/null 2>&1

exit 0
