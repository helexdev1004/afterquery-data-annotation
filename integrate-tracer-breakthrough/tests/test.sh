#!/usr/bin/env bash
# The reward is 0 from the first moment; passing checks alone make it 1.
set -uo pipefail
mkdir -p /logs/verifier
chmod 700 /logs/verifier 2>/dev/null || true
echo -n 0 > /logs/verifier/reward.txt
cd /tests
python -m pytest -q -p no:cacheprovider --ctrf /logs/verifier/ctrf.json test_breakthrough.py
status=$?
if [ "$status" -eq 0 ]; then echo -n 1 > /logs/verifier/reward.txt; fi
exit 0
