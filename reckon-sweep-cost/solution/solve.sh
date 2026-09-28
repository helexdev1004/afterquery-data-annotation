#!/usr/bin/env bash
set -euo pipefail
python3 "$(dirname "$0")/sweep_cost.py" /app
