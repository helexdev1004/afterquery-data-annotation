#!/usr/bin/env bash
# The reward starts at 0 and is raised to 1 only by a fully passing pytest run.
set -uo pipefail
mkdir -p /logs/verifier
chmod 700 /logs/verifier 2>/dev/null || true
echo -n 0 > /logs/verifier/reward.txt
cd /tests
python -m pytest -q -p no:cacheprovider --ctrf /logs/verifier/ctrf.json test_no2_report.py
result=$?
if [ "$result" = "0" ]; then echo -n 1 > /logs/verifier/reward.txt; fi
exit 0
