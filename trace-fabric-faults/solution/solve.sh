#!/usr/bin/env bash
set -euo pipefail
python3 "$(dirname "$0")/trace.py"
echo "wrote /app/recall.json"
