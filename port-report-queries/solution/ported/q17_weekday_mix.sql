SELECT EXTRACT(DOW FROM i.issued_on) + 1 AS dow, COUNT(*) AS invoices
FROM invoices i
GROUP BY EXTRACT(DOW FROM i.issued_on)
ORDER BY dow
