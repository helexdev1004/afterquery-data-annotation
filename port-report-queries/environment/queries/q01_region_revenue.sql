SELECT r.code, r.name, SUM(i.amount_cents) AS revenue_cents
FROM regions r
JOIN customers c ON c.region_code = r.code
JOIN invoices i ON i.customer_id = c.id
WHERE i.status <> 'void'
GROUP BY r.code, r.name
ORDER BY r.code
