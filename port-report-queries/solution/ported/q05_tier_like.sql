SELECT c.id, c.name
FROM customers c
WHERE c.tier ILIKE 'GOLD%'
ORDER BY c.id
