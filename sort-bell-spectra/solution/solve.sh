#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python "$HERE/write_book.py" /app /app/attribution.json /app/tuning.json
echo "wrote /app/attribution.json and /app/tuning.json"
