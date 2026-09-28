#!/usr/bin/env bash
# Reference solution: produce the inspection report.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python "$HERE/inspect_plates.py" /app/plates /app/inspection.json
echo "wrote /app/inspection.json"
