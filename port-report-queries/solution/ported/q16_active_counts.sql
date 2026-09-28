SELECT COUNT(*) AS customers,
       SUM(CASE WHEN c.active THEN 1 ELSE 0 END) AS active_sum
FROM customers c
