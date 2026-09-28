#!/usr/bin/env bash
# Marks the program at /app/activities.py.  The reward is written as 0 before anything is run,
# so a crash anywhere below leaves a 0 behind, and it is changed to 1 only when
# every test has passed.
set -uo pipefail

mkdir -p /logs/verifier
printf '0' > /logs/verifier/reward.txt

# the program under test is run as `nobody`; keep the marker's side to root
chmod 700 /tests /logs/verifier 2>/dev/null || true

cd /tests
if python -m pytest -q -p no:cacheprovider --ctrf /logs/verifier/ctrf.json test_activities.py; then
    printf '1' > /logs/verifier/reward.txt
fi
exit 0
