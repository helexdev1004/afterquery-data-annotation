-- Ledger schema.
--
-- `entries` is the authoritative double-entry journal. `accounts.balance` is a
-- cached running balance in minor units (cents) maintained by the service, and
-- must always equal the sum of that account's rows in `entries`. Each account is
-- opened with a genesis entry carrying its opening balance.
--
-- Accounts belong to a pool. A pool is one customer's set of accounts and it
-- carries a daily outbound limit: the total debited from every account in the
-- pool on a given day may not exceed `daily_limit_cents`. Genesis entries are
-- not spending and do not count toward it.
--
-- An account can be closed once it is empty. A closed account takes no further
-- movement in either direction.
--
-- `reversals` records that a transfer has been reversed. A transfer may be
-- reversed at most once; the reversal writes mirrored journal rows under its own
-- transfer id of the form 'rev:<reversal_id>'.

CREATE TABLE IF NOT EXISTS pools (
    id                BIGINT PRIMARY KEY,
    daily_limit_cents BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS accounts (
    id      BIGINT PRIMARY KEY,
    pool_id BIGINT NOT NULL REFERENCES pools (id),
    balance BIGINT NOT NULL,
    status  TEXT   NOT NULL DEFAULT 'open'
);

CREATE TABLE IF NOT EXISTS entries (
    id          BIGSERIAL PRIMARY KEY,
    transfer_id TEXT        NOT NULL,
    account_id  BIGINT      NOT NULL REFERENCES accounts (id),
    amount      BIGINT      NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reversals (
    id           BIGSERIAL PRIMARY KEY,
    reversal_id  TEXT        NOT NULL,
    transfer_id  TEXT        NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS entries_account_id_idx ON entries (account_id);
-- The daily total is looked up per account and bounded by date, so it is served
-- from here rather than by walking the whole journal.
CREATE INDEX IF NOT EXISTS entries_account_day_idx ON entries (account_id, created_at);
CREATE INDEX IF NOT EXISTS entries_transfer_id_idx ON entries (transfer_id);
CREATE INDEX IF NOT EXISTS accounts_pool_id_idx ON accounts (pool_id);
CREATE INDEX IF NOT EXISTS reversals_transfer_id_idx ON reversals (transfer_id);
