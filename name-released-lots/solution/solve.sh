#!/usr/bin/env bash
set -euo pipefail
install -m 644 "$(dirname "$0")/releases.py" /app/releases.py
