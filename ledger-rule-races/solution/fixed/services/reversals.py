"""Undoing a transfer.

A reversal writes the mirror image of every leg the original transfer wrote and
puts the money back where it came from. A transfer may be reversed once; a
second attempt is refused.

"Reversed at most once" is decided by whether a row exists in `reversals`, and
a row that does not exist yet cannot be locked. So the accounts the reversal is
about are locked first: two reversals of the same transfer are about the same
accounts, so the second one waits, and by the time it looks the first has
committed its row. Locking in ascending id order keeps this path inside the
same lock order the transfer path uses.
"""

from __future__ import annotations

from .. import models
from ..errors import AlreadyReversed, UnknownTransfer
from ..repositories import accounts, entries, reversals


async def execute(conn, body) -> dict:
    legs = await entries.legs_of(conn, body.transfer_id)
    if not legs:
        raise UnknownTransfer()

    for account_id in sorted({leg["account_id"] for leg in legs}):
        await accounts.get_for_update(conn, account_id)

    if await reversals.exists_for(conn, body.transfer_id):
        raise AlreadyReversed()

    for leg in legs:
        await entries.write_leg(
            conn, f"rev:{body.reversal_id}", leg["account_id"], -leg["amount"]
        )
        await accounts.adjust_balance(conn, leg["account_id"], -leg["amount"])

    await reversals.record(conn, body.reversal_id, body.transfer_id)

    return models.reversal_view(body.reversal_id, body.transfer_id)
