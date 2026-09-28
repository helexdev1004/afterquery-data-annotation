SELECT EXTRACT(DOW FROM i.issued_on) AS dow, COUNT(*) AS invoices
FROM invoices i
GROUP BY EXTRACT(DOW FROM i.issued_on)
ORDER BY dow
