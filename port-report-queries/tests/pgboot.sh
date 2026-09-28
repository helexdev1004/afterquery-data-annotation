#!/bin/bash
# Boot the cluster this image ships with, idempotently.
set -euo pipefail

PGBIN=$(ls -d /usr/lib/postgresql/*/bin | head -1)
PGDATA=/var/lib/postgresql/data

if [ ! -s "$PGDATA/PG_VERSION" ]; then
    mkdir -p "$PGDATA"
    chown -R postgres:postgres "$PGDATA"
    su postgres -c "$PGBIN/initdb -D $PGDATA -A trust -E UTF8 --locale=C" >/dev/null
fi

if ! su postgres -c "$PGBIN/pg_ctl -D $PGDATA status" >/dev/null 2>&1; then
    su postgres -c "$PGBIN/pg_ctl -D $PGDATA -o '-p 5432 -c listen_addresses=127.0.0.1' -w -l $PGDATA/server.log start" >/dev/null
fi
