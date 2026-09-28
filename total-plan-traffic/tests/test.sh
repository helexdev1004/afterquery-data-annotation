#!/usr/bin/env bash
# reward.txt holds 0 from the first moment; only a clean pytest run makes it 1.
set -uo pipefail
mkdir -p /logs/verifier
chmod 700 /logs/verifier 2>/dev/null || true
echo -n 0 > /logs/verifier/reward.txt
cd /tests
python -m pytest -q -p no:cacheprovider --ctrf /logs/verifier/ctrf.json \
    test_plan_volumes.py
status=$?
[ "$status" -eq 0 ] && echo -n 1 > /logs/verifier/reward.txt
exit 0
