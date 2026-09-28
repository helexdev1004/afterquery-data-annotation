SELECT i.issued_on, COUNT(*) AS invoices, SUM(i.amount_cents) AS total_cents
FROM invoices i
WHERE i.status = 'paid'
GROUP BY i.issued_on
ORDER BY i.issued_on
