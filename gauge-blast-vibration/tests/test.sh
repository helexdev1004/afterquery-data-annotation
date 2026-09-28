#!/usr/bin/env bash
# reward.txt is 0 until the whole of pytest has passed, then 1.
set -uo pipefail
mkdir -p /logs/verifier
chmod 700 /logs/verifier 2>/dev/null || true
echo -n 0 > /logs/verifier/reward.txt
cd /tests
python -m pytest -q -p no:cacheprovider --ctrf /logs/verifier/ctrf.json test_blast_pgv.py
verdict=$?
if [ "$verdict" -eq 0 ]; then echo -n 1 > /logs/verifier/reward.txt; fi
exit 0
