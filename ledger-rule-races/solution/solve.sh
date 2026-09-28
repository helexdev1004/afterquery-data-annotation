#!/usr/bin/env bash
# Reference solution: install the four corrected modules.
#
# Three separate races, one per use case, and none of them is a lost update on
# an account balance - the shipped code already locks both account rows in
# ascending id order and the fix leaves that alone. NOTES.md alongside this
# file says what each defect is and why each fix is the fix.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET=/app/service/app

if [ ! -d "$HERE/fixed" ]; then
    echo "reference solution not found at $HERE/fixed" >&2
    exit 1
fi

install -m 644 "$HERE/fixed/repositories/pools.py" "$TARGET/repositories/pools.py"
install -m 644 "$HERE/fixed/services/transfers.py" "$TARGET/services/transfers.py"
install -m 644 "$HERE/fixed/services/reversals.py" "$TARGET/services/reversals.py"
install -m 644 "$HERE/fixed/services/accounts.py"  "$TARGET/services/accounts.py"

python -c "
import ast, pathlib
for p in pathlib.Path('$TARGET').rglob('*.py'):
    ast.parse(p.read_text())
"

echo "reference fix applied to $TARGET"
