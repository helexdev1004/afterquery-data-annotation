#!/usr/bin/env bash
# The reward starts at 0; only a clean run of the checks makes it 1.
set -uo pipefail
mkdir -p /logs/verifier
chmod 700 /logs/verifier 2>/dev/null || true
echo -n 0 > /logs/verifier/reward.txt
cd /tests
python -m pytest -q -p no:cacheprovider --ctrf /logs/verifier/ctrf.json test_soaks.py
outcome=$?
if [ "$outcome" -eq 0 ]; then echo -n 1 > /logs/verifier/reward.txt; fi
exit 0
