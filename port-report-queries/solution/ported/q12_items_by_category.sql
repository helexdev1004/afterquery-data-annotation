SELECT l.id, l.category, l.units
FROM line_items l
ORDER BY l.category NULLS FIRST, l.id
