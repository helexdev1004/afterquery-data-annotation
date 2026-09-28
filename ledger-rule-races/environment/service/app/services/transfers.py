"""Moving money between two accounts.

The shape of the operation: lock both accounts, check everything that has to be
true, write both journal rows and both balance updates, commit. One transaction
covers all of it, so a caller that gets a 200 knows the whole movement is on
disk and a caller that gets a 409 knows nothing moved.
"""

from __future__ import annotations

from .. import models
from ..errors import AccountClosed, InsufficientFunds, SameAccount, UnknownAccount
from ..policy import limits
from ..repositories import accounts, entries


async def execute(conn, body) -> dict:
    if body.source_account_id == body.destination_account_id:
        raise SameAccount()

    # Both accounts are locked in id order before anything is decided, so two
    # transfers touching the same pair queue rather than interleave, and a pair
    # moving money in opposite directions cannot deadlock.
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
