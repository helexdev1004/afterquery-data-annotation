SELECT c.id, c.name, c.active::int AS active
FROM customers c
WHERE c.active
ORDER BY c.id
