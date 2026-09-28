#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 expected.py /app
echo "expected_protein.csv written"
