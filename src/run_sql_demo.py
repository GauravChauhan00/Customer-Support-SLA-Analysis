"""Load the clean CSV into SQLite and execute beginner SQL examples."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "support_tickets_clean.csv"
OUT = ROOT / "reports" / "sql_results"
OUT.mkdir(parents=True, exist_ok=True)

QUERIES = {
    "team_performance_sql": """
        SELECT assigned_team,
               COUNT(*) AS total_tickets,
               ROUND(100.0 * AVG(CASE WHEN status='Resolved' THEN overall_sla_met END), 2) AS sla_compliance_pct,
               ROUND(AVG(CASE WHEN status='Resolved' THEN resolution_hours END), 2) AS avg_resolution_hours
        FROM support_tickets
        GROUP BY assigned_team
        ORDER BY sla_compliance_pct ASC
    """,
    "top_categories_sql": """
        SELECT category, COUNT(*) AS ticket_count
        FROM support_tickets
        GROUP BY category
        ORDER BY ticket_count DESC
        LIMIT 10
    """,
    "priority_sla_sql": """
        SELECT priority, COUNT(*) AS tickets,
               ROUND(100.0 * AVG(CASE WHEN status='Resolved' THEN overall_sla_met END), 2) AS sla_compliance_pct
        FROM support_tickets
        GROUP BY priority
        ORDER BY tickets DESC
    """,
}


def main() -> None:
    df = pd.read_csv(DATA)
    with sqlite3.connect(ROOT / "support_analysis.db") as conn:
        df.to_sql("support_tickets", conn, if_exists="replace", index=False)
        for name, query in QUERIES.items():
            result = pd.read_sql_query(query, conn)
            result.to_csv(OUT / f"{name}.csv", index=False)
            print(f"\n{name}\n{result.to_string(index=False)}")


if __name__ == "__main__":
    main()
