SELECT p.id, p.note, p.amount_cents
FROM payments p
ORDER BY p.note NULLS FIRST, p.id
