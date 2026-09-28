SELECT c.id, c.name, c.active
FROM customers c
WHERE c.active = 1
ORDER BY c.id
