#!/usr/bin/env bash
set -euo pipefail
python3 "$(dirname "$0")/phase.py"
echo "wrote /app/contexts.csv"
