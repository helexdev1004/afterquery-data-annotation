"""Moving money between two accounts.

The shape of the operation: take the pool, then lock both accounts, check
everything that has to be true, write both journal rows and both balance
updates, commit. One transaction covers all of it, so a caller that gets a 200
knows the whole movement is on disk and a caller that gets a 409 knows nothing
moved.

Lock order is pool first, then the two account rows in ascending id order. A
transaction takes at most one pool lock and always takes it before any account
lock, so no cycle can form between any two of the paths in this service and the
server's deadlock counter never moves.
"""

from __future__ import annotations

from .. import models
from ..errors import AccountClosed, InsufficientFunds, SameAccount, UnknownAccount
from ..policy import limits
from ..repositories import accounts, entries, pools


async def execute(conn, body) -> dict:
    if body.source_account_id == body.destination_account_id:
        raise SameAccount()

    # Which pool the limit belongs to is a property of the source account, so
    # it has to be read before the pool can be locked. This read takes no lock
    # on purpose: taking the account first and the pool second would invert the
    # lock order that the rest of this module depends on. An account never
    # moves between pools - nothing in the API changes `pool_id` - so the
    # answer cannot go stale underneath the lock taken on the next line.
    preview = await accounts.get(conn, body.source_account_id)
    if preview is None:
        raise UnknownAccount()

    await pools.lock(conn, preview["pool_id"])

    rows = await accounts.lock_pair(
        conn, body.source_account_id, body.destination_account_id
    )
    if len(rows) != 2:
        raise UnknownAccount()

    source = rows[body.source_account_id]
    destination = rows[body.destination_account_id]

    if source["status"] == "closed" or destination["status"] == "closed":
        raise AccountClosed()

    if source["balance"] < body.amount_cents:
        raise InsufficientFunds()

    # Safe to read the day's total now: everything that could add to it for
    # this pool is queued behind the pool lock this transaction is holding.
    await limits.check_outbound(conn, source["pool_id"], body.amount_cents)

    await entries.write_pair(
        conn,
        body.transfer_id,
        body.source_account_id,
        body.destination_account_id,
        body.amount_cents,
    )
    await accounts.adjust_balance(conn, body.source_account_id, -body.amount_cents)
    await accounts.adjust_balance(conn, body.destination_account_id, body.amount_cents)

    return models.transfer_view(
        body.transfer_id, source["balance"] - body.amount_cents
    )
