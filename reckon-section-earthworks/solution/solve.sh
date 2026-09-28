#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 take_off.py /app
echo "areas.csv written"
