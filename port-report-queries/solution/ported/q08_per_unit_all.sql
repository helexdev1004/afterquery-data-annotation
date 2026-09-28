SELECT i.id,
       round(i.amount_cents::numeric / NULLIF(i.qty, 0), 4) AS per_unit
FROM invoices i
ORDER BY i.id
