SELECT i.id, i.amount_cents, i.qty, i.amount_cents / i.qty AS per_unit
FROM invoices i
WHERE i.qty > 0
ORDER BY i.id
