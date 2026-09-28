#!/usr/bin/env bash
# Reward starts at 0; only a clean pytest run raises it to 1.
set -uo pipefail
mkdir -p /logs/verifier
chmod 700 /logs/verifier 2>/dev/null || true
echo -n 0 > /logs/verifier/reward.txt
cd /tests
if python -m pytest -q -p no:cacheprovider --ctrf /logs/verifier/ctrf.json test_rail_power.py; then
  echo -n 1 > /logs/verifier/reward.txt
fi
exit 0
