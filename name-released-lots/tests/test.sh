#!/usr/bin/env bash
# The reward is 0 from the outset and becomes 1 only on a clean pytest run.
set -uo pipefail
mkdir -p /logs/verifier
chmod 700 /logs/verifier 2>/dev/null || true
echo -n 0 > /logs/verifier/reward.txt
cd /tests
python -m pytest -q -p no:cacheprovider --ctrf /logs/verifier/ctrf.json test_releases.py
outcome=$?
if [ "$outcome" -eq 0 ]; then echo -n 1 > /logs/verifier/reward.txt; fi
exit 0
