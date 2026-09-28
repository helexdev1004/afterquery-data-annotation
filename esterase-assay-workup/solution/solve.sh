#!/usr/bin/env bash
# Puts the reference work-up where the task asks for the program.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
install -m 644 "$here/activities.py" /app/activities.py
