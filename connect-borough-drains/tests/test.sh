#!/usr/bin/env bash
# Writes a binary reward to /logs/verifier/reward.txt on every path.
set -uo pipefail

mkdir -p /logs/verifier
chmod 700 /logs/verifier 2>/dev/null || true

# Default to a zero reward before anything runs, so a crash anywhere below
# cannot leave the reward unwritten.
printf '0' > /logs/verifier/reward.txt

cd /tests

python -m pytest -q -p no:cacheprovider \
    --ctrf /logs/verifier/ctrf.json \
    test_connections.py
status=$?

if [ "$status" -eq 0 ]; then
    printf '1' > /logs/verifier/reward.txt
else
    printf '0' > /logs/verifier/reward.txt
fi

exit 0
