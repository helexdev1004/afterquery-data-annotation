#!/usr/bin/env bash
# Binary reward, written whatever happens.
set -uo pipefail
mkdir -p /logs/verifier
chmod 700 /logs/verifier 2>/dev/null || true
printf '0' > /logs/verifier/reward.txt
reward=0
cd /tests
python -m pytest -q -p no:cacheprovider --ctrf /logs/verifier/ctrf.json \
    test_drying_times.py && reward=1
printf '%s' "$reward" > /logs/verifier/reward.txt
exit 0
