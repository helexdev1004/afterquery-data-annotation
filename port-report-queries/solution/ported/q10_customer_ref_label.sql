SELECT c.id, c.name || ' [' || c.external_ref || ']' AS label
FROM customers c
ORDER BY c.id
