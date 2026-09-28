SELECT l.invoice_id,
       string_agg(l.sku, ',' ORDER BY l.sku) AS skus
FROM line_items l
GROUP BY l.invoice_id
ORDER BY l.invoice_id
