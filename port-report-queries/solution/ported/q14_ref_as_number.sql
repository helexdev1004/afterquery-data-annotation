SELECT c.id,
       trunc(COALESCE(NULLIF(substring(c.external_ref FROM '^[+-]?[0-9]+'), '')::numeric, 0))::bigint AS ref_number
FROM customers c
WHERE c.external_ref IS NOT NULL
ORDER BY c.id
