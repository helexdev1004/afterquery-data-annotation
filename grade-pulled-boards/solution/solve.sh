#!/usr/bin/env bash
set -euo pipefail
python3 "$(dirname "$0")/grade.py"
echo "wrote /app/grades.csv"
