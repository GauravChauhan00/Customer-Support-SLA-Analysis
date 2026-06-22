-- Customer Support SLA Analysis (MySQL 8+ and SQLite-friendly)
-- Import data/processed/support_tickets_clean.csv as table: support_tickets

-- 1. Overall KPI summary
SELECT
    COUNT(*) AS total_tickets,
    SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) AS resolved_tickets,
    ROUND(100.0 * AVG(CASE WHEN status = 'Resolved' THEN overall_sla_met END), 2) AS sla_compliance_pct,
    ROUND(AVG(first_response_minutes), 2) AS avg_first_response_minutes,
    ROUND(AVG(CASE WHEN status = 'Resolved' THEN resolution_hours END), 2) AS avg_resolution_hours
FROM support_tickets;

-- 2. Team performance
SELECT
    assigned_team,
    COUNT(*) AS total_tickets,
    ROUND(100.0 * AVG(CASE WHEN status = 'Resolved' THEN overall_sla_met END), 2) AS sla_compliance_pct,
    ROUND(AVG(CASE WHEN status = 'Resolved' THEN resolution_hours END), 2) AS avg_resolution_hours,
    ROUND(AVG(csat_score), 2) AS avg_csat
FROM support_tickets
GROUP BY assigned_team
ORDER BY sla_compliance_pct ASC;

-- 3. Most common issue categories
SELECT category, COUNT(*) AS ticket_count
FROM support_tickets
GROUP BY category
ORDER BY ticket_count DESC
LIMIT 10;

-- 4. Priority-wise SLA compliance
SELECT
    priority,
    COUNT(*) AS tickets,
    ROUND(100.0 * AVG(CASE WHEN status = 'Resolved' THEN overall_sla_met END), 2) AS sla_compliance_pct
FROM support_tickets
GROUP BY priority
ORDER BY CASE priority
    WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END;

-- 5. Monthly ticket trend
SELECT created_month, COUNT(*) AS ticket_volume
FROM support_tickets
GROUP BY created_month
ORDER BY created_month;

-- 6. Reopen rate by category
SELECT
    category,
    COUNT(*) AS resolved_tickets,
    ROUND(100.0 * AVG(is_reopened), 2) AS reopen_rate_pct
FROM support_tickets
WHERE status = 'Resolved'
GROUP BY category
HAVING COUNT(*) >= 10
ORDER BY reopen_rate_pct DESC;
