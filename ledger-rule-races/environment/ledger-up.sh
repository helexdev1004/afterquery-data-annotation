#!/usr/bin/env bash
# Bring the box up, or bring back whatever part of it is down. Idempotent:
# safe to run at any time, including when everything is already healthy.
#
#   ledger-up            start postgres, apply schema, seed, start the service
#   ledger-up --restart  restart the service only, picking up code changes
set -uo pipefail

RESTART=0
if [ "${1:-}" = "--restart" ]; then
  RESTART=1
fi

if curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1 && [ "$RESTART" -eq 0 ]; then
  echo "service already healthy on http://127.0.0.1:8000"
  exit 0
fi

/usr/local/bin/pgboot.sh || {
  echo "postgres failed to start; see /var/log/ledger/postgres.log" >&2
  exit 1
}

psql "${DATABASE_URL}" -v ON_ERROR_STOP=1 -f /app/service/schema.sql >/dev/null 2>&1
python /app/service/devseed.py >/dev/null 2>&1

pkill -f "uvicorn app.main:app" >/dev/null 2>&1
sleep 1

mkdir -p /var/log/ledger
cd /app/service
nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 3 --log-level warning \
  > /var/log/ledger/service.log 2>&1 &

for _ in $(seq 1 60); do
  if curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; then
    echo "service healthy on http://127.0.0.1:8000"
    exit 0
  fi
  sleep 1
done

echo "service did not become healthy; see /var/log/ledger/service.log" >&2
exit 1
