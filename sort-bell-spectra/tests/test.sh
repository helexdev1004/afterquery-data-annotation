#!/bin/bash
set -uo pipefail

mkdir -p /logs/verifier
echo -n 0 > /logs/verifier/reward.txt

cd /tests
python -m pytest test_tuning.py -q \
    --ctrf /logs/verifier/ctrf.json \
    >> /logs/verifier/pytest.log 2>&1
status=$?

if [ "$status" -eq 0 ]; then
    echo -n 1 > /logs/verifier/reward.txt
else
    echo -n 0 > /logs/verifier/reward.txt
fi
exit 0
