"""Account lifecycle.

An account can be closed once it is empty. Closing is final as far as this
service is concerned: a closed account takes no further movement in either
direction, which the transfer path enforces when it reads the pair.

The emptiness check and the closure have to see the same row, so the account is
read under its own lock. A plain read lets a transfer land between the check
and the update, which closes an account that has just been paid into and leaves
money stranded on it.
"""

from __future__ import annotations

from .. import models
from ..errors import AccountNotEmpty, UnknownAccount
from ..repositories import accounts


async def close(conn, account_id: int) -> dict:
    row = await accounts.get_for_update(conn, account_id)
    if row is None:
        raise UnknownAccount()

    # Closing an already closed account is a no-op rather than an error, so a
    # client that retries after a dropped response gets the same answer.
    if row["status"] == "closed":
        return models.closure_view(account_id)

    if row["balance"] != 0:
        raise AccountNotEmpty()

    await accounts.mark_closed(conn, account_id)
    return models.closure_view(account_id)


async def read(conn, account_id: int) -> dict:
    row = await accounts.get(conn, account_id)
    if row is None:
        raise UnknownAccount()
    return models.account_view(row)
