#!/usr/bin/env bash
set -euo pipefail
python3 "$(dirname "$0")/number.py"
echo "wrote /app/rings.tsv"
