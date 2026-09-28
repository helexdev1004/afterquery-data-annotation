#!/usr/bin/env bash
# Verifier entry point. Writes the binary reward on every code path, including
# crashes: the default is 0 and it is only overwritten on a clean run.
set -uo pipefail

REWARD_DIR=/logs/verifier
mkdir -p "$REWARD_DIR"

# The submitted service runs as `runner`. Keep this directory owned by root and
# unwritable by anyone else, so nothing the service leaves behind can create or
# replace the reward file.
chown root:root "$REWARD_DIR" 2>/dev/null || true
chmod 755 "$REWARD_DIR" 2>/dev/null || true

printf '0' > "$REWARD_DIR/reward.txt"

cd /tests

python -m pytest test_ledger.py \
    -p no:cacheprovider \
    --ctrf "$REWARD_DIR/ctrf.json" \
    -q \
    > "$REWARD_DIR/pytest.log" 2>&1
STATUS=$?

cat "$REWARD_DIR/pytest.log"

# Sweep the service account before the verdict is written. The grader already
# does this, but a forged pass is worth guarding twice: nothing the submission
# started may be running when reward.txt is finalised.
pkill -TERM -u runner 2>/dev/null || true
sleep 1
pkill -KILL -u runner 2>/dev/null || true
sleep 1

if [ "$STATUS" -eq 0 ]; then
    printf '1' > "$REWARD_DIR/reward.txt"
else
    printf '0' > "$REWARD_DIR/reward.txt"
fi

chmod 644 "$REWARD_DIR/reward.txt" 2>/dev/null || true

exit 0
