#!/bin/bash
# Reference solution: install the corrected query set.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p /app/ported
cp "$HERE"/ported/*.sql /app/ported/

echo "installed $(ls -1 /app/ported/*.sql | wc -l) ported queries"
