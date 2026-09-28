#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 reckon.py /app
echo "drying_times.json written"
