SELECT i.id, i.amount_cents, i.qty,
       round(i.amount_cents::numeric / i.qty, 4) AS per_unit
FROM invoices i
WHERE i.qty > 0
ORDER BY i.id
