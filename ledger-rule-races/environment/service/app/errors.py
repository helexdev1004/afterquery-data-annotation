"""Domain errors, and how they become HTTP responses.

Services raise these; the API layer turns them into responses. Keeping the
mapping in one place is what stops a handler inventing its own status code for
a condition another handler already has a name for.
"""

from __future__ import annotations


class LedgerError(Exception):
    """Base class. `status` is the HTTP code the API layer will use."""

    status = 500
    detail = "ledger error"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.detail)
        if detail:
            self.detail = detail


class UnknownAccount(LedgerError):
    status = 404
    detail = "unknown account"


class UnknownPool(LedgerError):
    status = 404
    detail = "unknown pool"


class UnknownTransfer(LedgerError):
    status = 404
    detail = "unknown transfer"


class SameAccount(LedgerError):
    status = 400
    detail = "source and destination are the same"


class AccountClosed(LedgerError):
    status = 409
    detail = "account is closed"


class InsufficientFunds(LedgerError):
    status = 409
    detail = "insufficient funds"


class DailyLimitExceeded(LedgerError):
    status = 409
    detail = "daily pool limit exceeded"


class AlreadyReversed(LedgerError):
    status = 409
    detail = "transfer already reversed"


class AccountNotEmpty(LedgerError):
    status = 409
    detail = "account is not empty"
