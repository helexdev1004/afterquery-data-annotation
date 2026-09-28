#!/usr/bin/env bash
# The reward file is written as 0 at once and raised to 1 only by passing checks.
set -uo pipefail
mkdir -p /logs/verifier
chmod 700 /logs/verifier 2>/dev/null || true
echo -n 0 > /logs/verifier/reward.txt
cd /tests
python -m pytest -q -p no:cacheprovider --ctrf /logs/verifier/ctrf.json test_cost_to_target.py
if [ $? = 0 ]; then echo -n 1 > /logs/verifier/reward.txt; fi
exit 0
