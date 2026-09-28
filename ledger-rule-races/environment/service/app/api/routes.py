"""HTTP routes.

Thin on purpose. A route opens the right kind of database scope, calls one
service, and lets `errors.LedgerError` carry the status code back. No decision
about money is taken in this module.
"""

from __future__ import annotations

from fastapi import APIRouter

from .. import db, models
from ..services import accounts as account_service
from ..services import pools as pool_service
from ..services import reversals as reversal_service
from ..services import transfers as transfer_service

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    async with db.connection() as conn:
        await conn.fetchval("SELECT 1")
    return {"status": "ok"}


@router.get("/accounts/{account_id}")
async def get_account(account_id: int) -> dict:
    async with db.connection() as conn:
        return await account_service.read(conn, account_id)


@router.get("/pools/{pool_id}")
async def get_pool(pool_id: int) -> dict:
    async with db.connection() as conn:
        return await pool_service.read(conn, pool_id)


@router.post("/transfer")
async def post_transfer(body: models.TransferIn) -> dict:
    async with db.unit_of_work() as conn:
        return await transfer_service.execute(conn, body)


@router.post("/reversals")
async def post_reversal(body: models.ReversalIn) -> dict:
    async with db.unit_of_work() as conn:
        return await reversal_service.execute(conn, body)


@router.post("/accounts/{account_id}/close")
async def post_close(account_id: int) -> dict:
    async with db.unit_of_work() as conn:
        return await account_service.close(conn, account_id)
