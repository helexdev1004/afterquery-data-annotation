#!/usr/bin/env bash
set -euo pipefail
python3 "$(dirname "$0")/place.py"
echo "wrote /app/beds_for_paper.md"
