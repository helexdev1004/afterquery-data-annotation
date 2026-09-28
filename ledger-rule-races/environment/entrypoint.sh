#!/usr/bin/env bash
# Container entrypoint: bring the stack up, then stay alive.
#
# Everything here is delegated to ledger-up so that the same code path works
# whether the harness runs this entrypoint or execs straight into a shell and
# the operator runs `ledger-up` by hand.
set -uo pipefail

/usr/local/bin/ledger-up.sh || true

exec sleep infinity
