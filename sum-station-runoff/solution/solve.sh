#!/usr/bin/env bash
set -euo pipefail
python3 "$(dirname "$0")/water_balance.py" /app
