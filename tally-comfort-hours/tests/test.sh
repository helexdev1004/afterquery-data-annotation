#!/usr/bin/env bash
# The reward file says 0 until pytest has passed; it is written either way.
set -uo pipefail
out=/logs/verifier
mkdir -p "$out"; chmod 700 "$out" 2>/dev/null || true
echo -n 0 > "$out/reward.txt"
cd /tests && python -m pytest -q -p no:cacheprovider --ctrf "$out/ctrf.json" test_out_of_band.py \
    && echo -n 1 > "$out/reward.txt"
exit 0
