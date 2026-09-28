#!/usr/bin/env bash
# The reward is binary and is on disk before and after the tests run.
set -uo pipefail
mkdir -p /logs/verifier
chmod 700 /logs/verifier 2>/dev/null || true
printf '0' > /logs/verifier/reward.txt
cd /tests
if python -m pytest -q -p no:cacheprovider --ctrf /logs/verifier/ctrf.json test_areas.py
then
    printf '1' > /logs/verifier/reward.txt
else
    printf '0' > /logs/verifier/reward.txt
fi
exit 0
