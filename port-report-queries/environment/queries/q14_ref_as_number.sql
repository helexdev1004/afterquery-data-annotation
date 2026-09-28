SELECT c.id, CAST(c.external_ref AS INTEGER) AS ref_number
FROM customers c
WHERE c.external_ref IS NOT NULL
ORDER BY c.id
