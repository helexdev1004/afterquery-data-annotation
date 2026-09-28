#!/usr/bin/env bash
# The reward is written as 0 first and becomes 1 only when every check passes.
set -uo pipefail
mkdir -p /logs/verifier
chmod 700 /logs/verifier 2>/dev/null || true
echo -n 0 > /logs/verifier/reward.txt
cd /tests
python -m pytest -q -p no:cacheprovider --ctrf /logs/verifier/ctrf.json test_service_due.py
rc=$?
if [ $rc -eq 0 ]; then echo -n 1 > /logs/verifier/reward.txt; fi
exit 0
