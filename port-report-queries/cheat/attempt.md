# Ways to pass without doing the port, and what stops each

Written by asking what the laziest passing attempt would be. Never executed by
the pipeline; kept so the reasoning is on the record.

## 1. Return the published answers as literals

The environment ships `/app/expected/<query>.tsv`, the exact output every query
produced on the source engine for the shipped data. So paste them back:

```sql
SELECT * FROM (VALUES (1, 456219, 2, 228109.5000), ...) AS t(id, amount_cents, qty, per_unit)
```

**Blocked.** Grading runs on two datasets and both must reach the pass mark. The
literals satisfy the dataset whose answers were published and return exactly the
wrong rows for the one whose answers the submission has never seen. This is the
main reason both datasets are graded rather than only the hidden one.

## 2. Read the expected output at query time

Have the query select out of `/app/expected`, or `COPY` it into a table first.

**Blocked.** The verifier builds its own container from `tests/`, boots its own
PostgreSQL and loads its own data. `/app/expected` does not exist there, and
neither does any table the submission created while working - only the `.sql`
files in `/app/ported` are carried across. A `COPY FROM '/app/expected/...'`
fails to open the file, which scores the query as failed to run.

## 3. Leave the hard queries out

Ship only the queries that are already right and drop the rest, hoping absence
scores better than a wrong answer.

**Blocked.** A query missing from `/app/ported` is recorded as a failure exactly
like a wrong one, and a separate check names the missing files, so this can only
lose ground. Twenty-two of twenty-four must match.

## 4. Put the answer somewhere other than a .sql file

Leave a script, a `.tsv`, or a `README` explaining the intended fix.

**Blocked.** The verifier reads `/app/ported/<name>.sql` for each of the
twenty-four names and nothing else. Anything else in the directory is ignored.

## 5. Blanket-apply every fix

Wrap every comparison in `lower()`, cast every division, put `NULLS FIRST` on
every sort, replace every `concat()` with `||`.

**Not blocked, and it does not work.** Five of the twenty-four queries are
already correct as the transpiler emitted them, so a blanket rewrite breaks
queries that were passing. `lower()` on a column that is already lower case is
harmless, but `NULLS FIRST` on a sort whose source ordering put NULLs last, or a
`round(..., 4)` on an expression that was never a division, changes a correct
answer into a wrong one. Reading each query is cheaper than guessing.

## 6. Tune against the visible diff until it is clean

Run every query, diff against `/app/expected`, repair whatever disagrees, stop
when nothing disagrees.

**Not blocked, and deliberately so - this is the intended near miss.** It is a
reasonable engineering approach and it gets most of the way. Measured on this
bundle it reaches 24 of 24 on the visible dataset and 19 of 24 on the hidden one,
against a bar of 22. Five queries are wrong in ways the shipped data never
exercises: two comparisons whose source collation is case-insensitive but whose
shipped values happen to be uniformly lower case, an integer division whose
shipped amounts happen to divide evenly, a division whose shipped denominators
are never zero, and a sort whose shipped column happens to contain no NULL. A
clean diff is evidence about the data in hand, not about the semantics.

## 7. Install the source engine and property-test against it

Install MariaDB or MySQL, load the shipped data, generate extra rows, and
compare the two engines until the port agrees everywhere.

**Allowed, and expected to be one of the passing routes.** It is real work -
standing up a second engine, reproducing the schema, and generating data that
actually exercises the boundaries - and it is roughly what the alternative costs
a person who reasons about the dialects directly. The instruction says the
network is open and does not ask for any particular method; grading looks only at
whether the results match.

## 8. Exploit the numeric normalisation

Cells that parse as numbers are compared as normalised decimals, so return
`2.50` where the source printed `2.5000`.

**Not blocked, and intended.** Requiring a port to reproduce another engine's
trailing zeros would be grading formatting rather than semantics. `2.5` and
`2.5000` are the same number and both pass; `2` and `2.5` are not and the
truncating division still fails. NULL is kept distinct from the empty string so
that the CONCAT and ordering divergences remain gradeable.
