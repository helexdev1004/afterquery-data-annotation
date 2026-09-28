SELECT c.id, c.name, c.external_ref
FROM customers c
WHERE c.external_ref = 12
ORDER BY c.id
