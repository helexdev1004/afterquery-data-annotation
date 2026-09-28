#!/usr/bin/env bash
# reward.txt is 0 until the checks have passed, and is written on every path.
set -uo pipefail
mkdir -p /logs/verifier
chmod 700 /logs/verifier 2>/dev/null || true
echo -n 0 > /logs/verifier/reward.txt
cd /tests
if python -m pytest -q -p no:cacheprovider --ctrf /logs/verifier/ctrf.json test_error_budget.py; then
    echo -n 1 > /logs/verifier/reward.txt
fi
exit 0
