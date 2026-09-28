SELECT c.id, c.name
FROM customers c
WHERE c.tier LIKE 'GOLD%'
ORDER BY c.id
