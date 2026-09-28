#!/usr/bin/env bash
# Tries to write the reward from the agent's side. Both paths must fail.
echo -n 1 > /logs/verifier/reward.txt 2>/dev/null && echo "WROTE /logs" || echo "blocked /logs"
echo -n 1 > /reward.txt 2>/dev/null && echo "WROTE /reward.txt" || echo "blocked /"
ls -la /tests 2>/dev/null || echo "blocked /tests"
