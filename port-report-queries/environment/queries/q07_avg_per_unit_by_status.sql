SELECT i.status,
       SUM(i.amount_cents) / SUM(i.qty) AS per_unit
FROM invoices i
WHERE i.qty > 0
GROUP BY i.status
ORDER BY i.status
