SELECT i.status,
       round(SUM(i.amount_cents)::numeric / SUM(i.qty), 4) AS per_unit
FROM invoices i
WHERE i.qty > 0
GROUP BY i.status
ORDER BY i.status
