#!/usr/bin/env bash
# Reference solution: install the correct adjustment.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p /app/solution
install -m 644 "$HERE/adjust.py" /app/solution/adjust.py
python -c "import ast, pathlib; ast.parse(pathlib.Path('/app/solution/adjust.py').read_text())"
echo "reference adjustment installed at /app/solution/adjust.py"
