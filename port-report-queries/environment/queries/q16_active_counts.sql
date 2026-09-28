SELECT COUNT(*) AS customers, SUM(c.active) AS active_sum
FROM customers c
