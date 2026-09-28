#!/usr/bin/env bash
# reward.txt is 0 from the start; a clean pytest run is the only thing that makes it 1.
set -uo pipefail
mkdir -p /logs/verifier
chmod 700 /logs/verifier 2>/dev/null || true
echo -n 0 > /logs/verifier/reward.txt
cd /tests
python -m pytest -q -p no:cacheprovider --ctrf /logs/verifier/ctrf.json test_commission.py
if [ "$?" -eq 0 ]; then echo -n 1 > /logs/verifier/reward.txt; fi
exit 0
