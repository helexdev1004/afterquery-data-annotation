SELECT p.id, p.method || ' / ' || p.note AS label
FROM payments p
ORDER BY p.id
