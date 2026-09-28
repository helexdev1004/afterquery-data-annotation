SELECT c.id, c.name, c.external_ref
FROM customers c
WHERE COALESCE(NULLIF(substring(c.external_ref FROM '^[+-]?[0-9]+'), '')::numeric, 0) = 12
ORDER BY c.id
