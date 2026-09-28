SELECT i.id, i.status, i.amount_cents
FROM invoices i
WHERE i.status = 'overdue' OR i.amount_cents > 400000
ORDER BY i.id
