#!/usr/bin/env bash
# One reward, 0 or 1, written before the tests and again after them.
set -uo pipefail
mkdir -p /logs/verifier
chmod 700 /logs/verifier 2>/dev/null || true
printf '0' > /logs/verifier/reward.txt
cd /tests
verdict=0
python -m pytest -q -p no:cacheprovider --ctrf /logs/verifier/ctrf.json \
    test_expected_protein.py && verdict=1
printf '%s' "$verdict" > /logs/verifier/reward.txt
exit 0
