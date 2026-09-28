#!/bin/bash
# Verifier entry point. A reward is written on every path, including a crash.
set -uo pipefail

mkdir -p /logs/verifier
echo -n 0 > /logs/verifier/reward.txt

# The submitted module is executed by an unprivileged account, so it has to be
# readable by one. /logs stays root-only, so nothing the submission does can
# reach the reward file.
chmod -R a+rX /app/solution 2>/dev/null || true
chmod 700 /logs/verifier 2>/dev/null || true

cd /tests
python -m pytest test_adjustment.py -q \
    --ctrf /logs/verifier/ctrf.json \
    >> /logs/verifier/pytest.log 2>&1
status=$?

if [ "$status" -eq 0 ]; then
    echo -n 1 > /logs/verifier/reward.txt
else
    echo -n 0 > /logs/verifier/reward.txt
fi
exit 0
