#!/usr/bin/env bash
# The reward file holds 0 before any check runs and 1 only after all pass.
set -uo pipefail
mkdir -p /logs/verifier
chmod 700 /logs/verifier 2>/dev/null || true
echo -n 0 > /logs/verifier/reward.txt
cd /tests
python -m pytest -q -p no:cacheprovider --ctrf /logs/verifier/ctrf.json test_inbound_plan.py \
    && echo -n 1 > /logs/verifier/reward.txt
exit 0
