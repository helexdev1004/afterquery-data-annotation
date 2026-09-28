SELECT i.id, i.amount_cents / i.qty AS per_unit
FROM invoices i
ORDER BY i.id
