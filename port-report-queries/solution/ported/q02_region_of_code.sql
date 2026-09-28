SELECT c.id, c.name, c.region_code
FROM customers c
WHERE rtrim(c.region_code) = 'NW'
ORDER BY c.id
