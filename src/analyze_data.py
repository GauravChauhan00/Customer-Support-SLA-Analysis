"""Create support KPIs, summary tables, and charts."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "support_tickets_clean.csv"
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)


def pct(value: float) -> float:
    return round(float(value) * 100, 2)


def main() -> None:
    df = pd.read_csv(DATA, parse_dates=["created_at", "resolved_at", "updated_at"])
    resolved = df[df["status"] == "Resolved"].copy()

    kpis = pd.DataFrame([
        ["Total Tickets", len(df)],
        ["Resolved Tickets", len(resolved)],
        ["Open + Pending Tickets", int(df["status"].isin(["Open", "Pending"]).sum())],
        ["SLA Compliance %", pct(resolved["overall_sla_met"].mean())],
        ["Avg First Response Minutes", round(df["first_response_minutes"].mean(), 2)],
        ["Median Resolution Hours", round(resolved["resolution_hours"].median(), 2)],
        ["Average CSAT", round(resolved["csat_score"].mean(), 2)],
        ["Reopen Rate %", pct(resolved["is_reopened"].mean())],
    ], columns=["metric", "value"])
    kpis.to_csv(REPORTS / "kpi_summary.csv", index=False)

    team = df.groupby("assigned_team", as_index=False).agg(
        total_tickets=("ticket_id", "count"),
        resolved_tickets=("status", lambda s: int((s == "Resolved").sum())),
        avg_first_response_min=("first_response_minutes", "mean"),
    )
    sla = resolved.groupby("assigned_team", as_index=False).agg(
        sla_compliance=("overall_sla_met", "mean"),
        avg_resolution_hours=("resolution_hours", "mean"),
        avg_csat=("csat_score", "mean"),
        reopen_rate=("is_reopened", "mean"),
    )
    team = team.merge(sla, on="assigned_team", how="left")
    for col in ["avg_first_response_min", "avg_resolution_hours", "avg_csat"]:
        team[col] = team[col].round(2)
    for col in ["sla_compliance", "reopen_rate"]:
        team[col] = (team[col] * 100).round(2)
    team.to_csv(REPORTS / "team_performance.csv", index=False)

    category = df.groupby("category", as_index=False).agg(total_tickets=("ticket_id", "count"))
    category_sla = resolved.groupby("category", as_index=False).agg(
        sla_compliance=("overall_sla_met", "mean"),
        avg_resolution_hours=("resolution_hours", "mean"),
        avg_csat=("csat_score", "mean"),
    )
    category = category.merge(category_sla, on="category", how="left")
    category["sla_compliance"] = (category["sla_compliance"] * 100).round(2)
    category[["avg_resolution_hours", "avg_csat"]] = category[["avg_resolution_hours", "avg_csat"]].round(2)
    category = category.sort_values("total_tickets", ascending=False)
    category.to_csv(REPORTS / "category_performance.csv", index=False)

    weekly = df.groupby("created_week", as_index=False).agg(ticket_volume=("ticket_id", "count"))
    weekly.to_csv(REPORTS / "weekly_ticket_volume.csv", index=False)

    plt.figure(figsize=(9, 5))
    top = category.head(8).sort_values("total_tickets")
    plt.barh(top["category"], top["total_tickets"])
    plt.title("Top Support Categories by Ticket Volume")
    plt.xlabel("Tickets")
    plt.tight_layout()
    plt.savefig(FIGURES / "top_support_categories.png", dpi=160)
    plt.close()

    plt.figure(figsize=(8, 5))
    plot_team = team.sort_values("sla_compliance")
    plt.barh(plot_team["assigned_team"], plot_team["sla_compliance"])
    plt.title("SLA Compliance by Team")
    plt.xlabel("SLA Compliance (%)")
    plt.xlim(0, 100)
    plt.tight_layout()
    plt.savefig(FIGURES / "sla_compliance_by_team.png", dpi=160)
    plt.close()

    plt.figure(figsize=(10, 5))
    plt.plot(weekly["created_week"], weekly["ticket_volume"], marker="o")
    plt.title("Weekly Ticket Volume")
    plt.xlabel("Week")
    plt.ylabel("Tickets")
    plt.xticks(rotation=70)
    plt.tight_layout()
    plt.savefig(FIGURES / "weekly_ticket_volume.png", dpi=160)
    plt.close()

    print(kpis.to_string(index=False))


if __name__ == "__main__":
    main()
