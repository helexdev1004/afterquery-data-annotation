#!/usr/bin/env bash
# 0 is written before anything runs; 1 replaces it only on a clean pass.
set -uo pipefail
where=/logs/verifier
mkdir -p "$where"
chmod 700 "$where" 2>/dev/null || true
echo -n 0 > "$where/reward.txt"
cd /tests
python -m pytest -q -p no:cacheprovider --ctrf "$where/ctrf.json" test_load_batches.py
code=$?
if [ "$code" = "0" ]; then echo -n 1 > "$where/reward.txt"; fi
exit 0
