#!/usr/bin/env bash
# Development launcher. This mirrors how the service is deployed: three worker
# processes, bound to 127.0.0.1:8000, module path app.main:app.
#
# The deployment shape is fixed. The grader starts the service with exactly the
# command below and ignores this file.
set -uo pipefail

cd /app/service
exec uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 3 --log-level warning
