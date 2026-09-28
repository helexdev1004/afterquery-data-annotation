#!/usr/bin/env bash
set -euo pipefail
python3 "$(dirname "$(readlink -f "$0")")/blast_pgv.py" /app
