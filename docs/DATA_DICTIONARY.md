# Data Dictionary — Customer Support SLA

| Column | Meaning |
|---|---|
| ticket_id | Unique ticket identifier |
| created_at / resolved_at | Ticket creation and resolution timestamps |
| priority | Low, Medium, High or Critical |
| category | Business issue type |
| assigned_team | Team responsible for resolution |
| first_response_minutes | Minutes taken for first response |
| first_response_target_min | Priority-based response target |
| resolution_hours | Time from creation to resolution |
| resolution_target_hours | Priority-based resolution target |
| overall_sla_met | 1 when both response and resolution targets were met |
| csat_score | Customer satisfaction score from 1 to 5 |
| is_reopened | 1 when the resolved ticket was reopened |
| created_month / created_week | Reporting fields derived from created_at |
