SELECT p.method, COUNT(*) AS payments, SUM(p.amount_cents) AS total_cents
FROM payments p
GROUP BY p.method
ORDER BY p.method
