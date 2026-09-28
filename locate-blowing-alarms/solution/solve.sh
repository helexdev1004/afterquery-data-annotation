#!/usr/bin/env bash
set -euo pipefail
python3 "$(dirname "$0")/place_alarms.py"
echo "wrote /app/dig_sheet.csv"
