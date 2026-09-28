#!/usr/bin/env bash
# Boot the verifier's own PostgreSQL instance. Independent of anything the
# agent ran; the cluster is initialised fresh inside this container.
set -uo pipefail

PGBIN="${PGBIN:-/usr/lib/postgresql/15/bin}"
PGDATA="${PGDATA:-/var/lib/pgdata}"
LOGFILE=/logs/verifier/postgres.log

mkdir -p "$PGDATA" /logs/verifier
chown -R postgres:postgres "$PGDATA"
touch "$LOGFILE"
chown postgres:postgres "$LOGFILE"

if [ ! -s "$PGDATA/PG_VERSION" ]; then
  su postgres -c "$PGBIN/initdb -D $PGDATA -A trust -E UTF8" >/dev/null 2>&1 || exit 1
fi

if ! su postgres -c "$PGBIN/pg_ctl -D $PGDATA status" >/dev/null 2>&1; then
  su postgres -c "$PGBIN/pg_ctl -D $PGDATA -l $LOGFILE -w -t 60 \
      -o '-c listen_addresses=127.0.0.1 -p 5432 -c max_connections=200 -c fsync=off -c synchronous_commit=off' \
      start" >/dev/null 2>&1 || exit 1
fi

for _ in $(seq 1 60); do
  su postgres -c "$PGBIN/pg_isready -h 127.0.0.1 -p 5432" >/dev/null 2>&1 && break
  sleep 1
done

# Deliberately NOT a superuser. The submitted service connects with this role,
# so it must not be able to reach ALTER SYSTEM, COPY FROM PROGRAM, or anything
# else outside its own database. Ownership of the ledger database is enough for
# it to create and alter its own tables.
su postgres -c "psql -h 127.0.0.1 -tAc \"SELECT 1 FROM pg_roles WHERE rolname='ledger'\"" 2>/dev/null \
  | grep -q 1 || su postgres -c "psql -h 127.0.0.1 -c \"CREATE ROLE ledger LOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB\"" >/dev/null 2>&1

su postgres -c "psql -h 127.0.0.1 -tAc \"SELECT 1 FROM pg_database WHERE datname='ledger'\"" 2>/dev/null \
  | grep -q 1 || su postgres -c "createdb -h 127.0.0.1 -O ledger ledger" >/dev/null 2>&1

exit 0
