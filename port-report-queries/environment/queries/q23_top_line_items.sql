SELECT l.id, l.sku, l.units, l.unit_cents, l.units * l.unit_cents AS line_cents
FROM line_items l
WHERE l.units >= 10
ORDER BY line_cents DESC, l.id
