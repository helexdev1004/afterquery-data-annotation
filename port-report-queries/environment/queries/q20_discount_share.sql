SELECT i.id,
       ROUND(i.amount_cents * i.discount_pct / 100.0, 2) AS discount_cents
FROM invoices i
ORDER BY i.id
