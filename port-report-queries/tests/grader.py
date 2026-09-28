"""Score the submitted query set against ground truth, on both datasets."""

from __future__ import annotations

import decimal
import os
import pathlib
import subprocess
import time

PORTED = pathlib.Path("/app/ported")
TESTS = pathlib.Path("/tests")
PASS_MARK = 22
DATASETS = ("visible", "hidden")
QUERY_NAMES = ['q01_region_revenue', 'q02_region_of_code', 'q03_gold_customers', 'q04_tier_membership', 'q05_tier_like', 'q06_unit_amount', 'q07_avg_per_unit_by_status', 'q08_per_unit_all', 'q09_payment_labels', 'q10_customer_ref_label', 'q11_payments_by_note', 'q12_items_by_category', 'q13_ref_equals_number', 'q14_ref_as_number', 'q15_active_customers', 'q16_active_counts', 'q17_weekday_mix', 'q18_skus_per_invoice', 'q19_settlement_days', 'q20_discount_share', 'q21_flagged_invoices', 'q22_monthly_totals', 'q23_top_line_items', 'q24_payment_methods']
STATEMENT_TIMEOUT_MS = 30000


def pg(sql: str, db: str = "postgres", tuples: bool = True) -> str:
    args = ["psql", "-h", "127.0.0.1", "-U", "postgres", "-d", db,
            "-v", "ON_ERROR_STOP=1", "-A", "-F", "\t", "-P", "null=NULL", "-q"]
    if tuples:
        args.append("-t")
    done = subprocess.run(args, input=sql, capture_output=True, text=True)
    if done.returncode != 0:
        raise RuntimeError(done.stderr.strip()[:300])
    return done.stdout


def boot() -> None:
    subprocess.run(["/tests/pgboot.sh"], check=True, timeout=180)
    for _ in range(60):
        try:
            pg("SELECT 1")
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError("PostgreSQL did not come up in the verifier")


def load(dataset: str) -> None:
    pg(f"DROP DATABASE IF EXISTS grading", db="postgres")
    pg(f"CREATE DATABASE grading", db="postgres")
    sql = (TESTS / "data" / f"{dataset}.sql").read_text(encoding="utf-8")
    pg(sql, db="grading")


def cell(value: str):
    value = value.strip()
    if value in ("NULL", ""):
        return None
    try:
        return decimal.Decimal(value).normalize()
    except (decimal.InvalidOperation, ValueError):
        return value


def grid(text: str, drop_header: bool):
    lines = [ln for ln in text.replace("\r\n", "\n").split("\n") if ln.strip() != ""]
    if drop_header and lines:
        lines = lines[1:]
    return [[cell(c) for c in ln.split("\t")] for ln in lines]


def compare(expected, actual):
    if len(expected) != len(actual):
        return f"returned {len(actual)} rows, expected {len(expected)}"
    for i, (e, a) in enumerate(zip(expected, actual)):
        if len(e) != len(a):
            return f"row {i + 1}: {len(a)} columns, expected {len(e)}"
        if e != a:
            return f"row {i + 1}: {a!r} != {e!r}"
    return None


def score_dataset(dataset: str) -> dict:
    load(dataset)
    results = {}
    for name in QUERY_NAMES:
        path = PORTED / f"{name}.sql"
        if not path.is_file():
            results[name] = "missing from /app/ported"
            continue
        try:
            sql = path.read_text(encoding="utf-8")
        except OSError as exc:
            results[name] = f"unreadable: {exc}"
            continue
        truth = (TESTS / "truth" / dataset / f"{name}.tsv").read_text(encoding="utf-8")
        expected = grid(truth, True)
        try:
            guard = f"SET statement_timeout = {STATEMENT_TIMEOUT_MS};\n"
            actual = grid(pg(guard + sql, db="grading"), False)
        except RuntimeError as exc:
            results[name] = f"failed to run: {exc.args[0][:160]}"
            continue
        results[name] = compare(expected, actual)
    return results


def run_all() -> dict:
    boot()
    return {dataset: score_dataset(dataset) for dataset in DATASETS}
