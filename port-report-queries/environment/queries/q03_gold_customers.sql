SELECT c.id, c.name, c.tier
FROM customers c
WHERE c.tier = 'gold'
ORDER BY c.id
