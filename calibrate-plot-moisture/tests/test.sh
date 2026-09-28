#!/usr/bin/env bash
# 0 is written before any check runs; 1 replaces it only if pytest exits clean.
set -uo pipefail
mkdir -p /logs/verifier
chmod 700 /logs/verifier 2>/dev/null || true
echo -n 0 > /logs/verifier/reward.txt
cd /tests
python -m pytest -q -p no:cacheprovider --ctrf /logs/verifier/ctrf.json test_plot_moisture.py
code=$?
if [ "$code" -eq 0 ]; then
  echo -n 1 > /logs/verifier/reward.txt
fi
exit 0
