#!/usr/bin/env bash
set -euo pipefail
python3 /app/trials.py > /app/trials.csv
echo "wrote /app/trials.csv"
