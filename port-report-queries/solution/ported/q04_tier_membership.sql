SELECT c.id, c.name, c.tier
FROM customers c
WHERE lower(c.tier) IN ('gold', 'silver')
ORDER BY c.id
