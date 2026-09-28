#!/usr/bin/env bash
set -euo pipefail
python3 "$(dirname "$0")/connect.py"
echo "wrote /app/connections.csv"
