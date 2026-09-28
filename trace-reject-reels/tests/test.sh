#!/usr/bin/env bash
# Reward starts at 0 and becomes 1 only if every check passes.
set -uo pipefail
mkdir -p /logs/verifier && chmod 700 /logs/verifier 2>/dev/null
echo -n 0 > /logs/verifier/reward.txt
cd /tests
if python -m pytest -q -p no:cacheprovider --ctrf /logs/verifier/ctrf.json test_reject_reels.py
then
    echo -n 1 > /logs/verifier/reward.txt
fi
exit 0
