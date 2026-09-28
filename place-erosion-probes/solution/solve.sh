#!/usr/bin/env bash
set -euo pipefail
python3 "$(dirname "$0")/level_probes.py"
echo "wrote /app/probe_altitudes.jsonl"
