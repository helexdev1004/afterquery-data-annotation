SELECT p.id, (p.paid_at - i.issued_on) AS days_to_pay
FROM payments p
JOIN invoices i ON i.id = p.invoice_id
ORDER BY p.id
