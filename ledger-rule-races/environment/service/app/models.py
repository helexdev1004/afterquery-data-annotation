"""Request and response shapes.

The response bodies are part of the published API and callers depend on the
field names, so they are built here rather than assembled ad hoc in each route.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TransferIn(BaseModel):
    transfer_id: str = Field(min_length=1, max_length=64)
    source_account_id: int
    destination_account_id: int
    amount_cents: int = Field(gt=0)


class ReversalIn(BaseModel):
    reversal_id: str = Field(min_length=1, max_length=64)
    transfer_id: str = Field(min_length=1, max_length=64)


def account_view(row) -> dict:
    return {
        "account_id": row["id"],
        "pool_id": row["pool_id"],
        "balance_cents": row["balance"],
        "status": row["status"],
    }


def pool_view(row, spent_today: int) -> dict:
    return {
        "pool_id": row["id"],
        "daily_limit_cents": row["daily_limit_cents"],
        "spent_today_cents": spent_today,
    }


def transfer_view(transfer_id: str, source_balance_cents: int) -> dict:
    return {
        "transfer_id": transfer_id,
        "status": "committed",
        "source_balance_cents": source_balance_cents,
    }


def reversal_view(reversal_id: str, transfer_id: str) -> dict:
    return {
        "reversal_id": reversal_id,
        "transfer_id": transfer_id,
        "status": "reversed",
    }


def closure_view(account_id: int) -> dict:
    return {"account_id": account_id, "status": "closed"}
