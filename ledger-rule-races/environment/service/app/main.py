"""Ledger service.

Double-entry ledger. Every movement of money writes two rows into `entries`
(a negative row on the source account, a positive row on the destination) and
keeps a cached running balance on the `accounts` row so that balance reads do
not have to aggregate the whole entry history.

Accounts belong to a pool, and a pool has a daily outbound limit: the total
debited across all of that pool's accounts in a day may not exceed it.

An account can be closed once it is empty, and a closed account takes no
further movement. A transfer can be reversed at most once.

Layout:

    api/            HTTP routes; no decisions taken here
    services/       one module per use case, the decisions live here
    policy/         rules that are about the business and not about storage
    repositories/   every statement that touches the database
    jobs/           out-of-band work, not on the request path
    db.py           connection pool and the transaction scope
    errors.py       domain errors and the status codes they map to

Deployed behind the process manager as three worker processes; see run.sh.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from . import db
from .api.routes import router
from .errors import LedgerError

app = FastAPI(title="ledger", version="4.0.0")
app.include_router(router)


@app.exception_handler(LedgerError)
async def _domain_error(_request, exc: LedgerError) -> JSONResponse:
    return JSONResponse(status_code=exc.status, content={"detail": exc.detail})


@app.on_event("shutdown")
async def _shutdown() -> None:
    await db.close_pool()
