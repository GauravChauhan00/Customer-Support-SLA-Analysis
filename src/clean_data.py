"""Clean support-ticket data and calculate SLA fields."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)


def normalize_title(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.title()


def main() -> None:
    df = pd.read_csv(RAW / "support_tickets_dirty.csv")
    targets = pd.read_csv(RAW / "priority_sla_targets.csv")
    raw_rows = len(df)
    exact_duplicates = int(df.duplicated().sum())

    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = df.drop_duplicates().copy()

    for col in ["priority", "category", "assigned_team", "status", "channel", "source_system"]:
        df[col] = normalize_title(df[col])

    # Fix acronyms changed by title-case.
    df["channel"] = df["channel"].replace({"Api Monitoring": "API Monitoring"})
    df["source_system"] = df["source_system"].replace({"Crm": "CRM"})
    df["category"] = df["category"].replace({"Api Error": "API Error", "Oauth Issue": "OAuth Issue"})

    for col in ["created_at", "resolved_at", "updated_at"]:
        df[col] = pd.to_datetime(df[col], errors="coerce", format="mixed", dayfirst=True)

    for col in ["first_response_minutes", "csat_score", "reopened_count"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["category"] = df["category"].fillna("Unknown")
    df["assigned_team"] = df["assigned_team"].fillna("Unknown")
    df.loc[~df["csat_score"].between(1, 5, inclusive="both"), "csat_score"] = pd.NA

    valid_priorities = set(targets["priority"])
    valid_statuses = {"Resolved", "Open", "Pending"}
    resolved_mask = df["status"].eq("Resolved")

    reasons = pd.Series("", index=df.index, dtype="string")
    reasons = reasons.mask(df["ticket_id"].isna(), reasons + "missing_ticket_id;")
    reasons = reasons.mask(df["created_at"].isna(), reasons + "invalid_created_at;")
    reasons = reasons.mask(~df["priority"].isin(valid_priorities), reasons + "invalid_priority;")
    reasons = reasons.mask(~df["status"].isin(valid_statuses), reasons + "invalid_status;")
    reasons = reasons.mask(df["first_response_minutes"].isna() | (df["first_response_minutes"] <= 0), reasons + "invalid_first_response;")
    reasons = reasons.mask(resolved_mask & df["resolved_at"].isna(), reasons + "missing_resolved_at;")
    reasons = reasons.mask(resolved_mask & (df["resolved_at"] < df["created_at"]), reasons + "resolved_before_created;")

    rejected = df[reasons.ne("")].copy()
    rejected["rejection_reason"] = reasons[reasons.ne("")]
    clean = df[reasons.eq("")].copy()

    # Keep latest record if duplicate ticket IDs appear with different updates.
    clean = clean.sort_values(["ticket_id", "updated_at"]).drop_duplicates("ticket_id", keep="last")
    clean = clean.merge(targets, on="priority", how="left", validate="many_to_one")

    clean["resolution_hours"] = (clean["resolved_at"] - clean["created_at"]).dt.total_seconds() / 3600
    clean["first_response_sla_met"] = (clean["first_response_minutes"] <= clean["first_response_target_min"]).astype(int)
    clean["resolution_sla_met"] = pd.NA
    resolved = clean["status"].eq("Resolved")
    clean.loc[resolved, "resolution_sla_met"] = (clean.loc[resolved, "resolution_hours"] <= clean.loc[resolved, "resolution_target_hours"]).astype(int)
    clean["overall_sla_met"] = pd.NA
    clean.loc[resolved, "overall_sla_met"] = (
        (clean.loc[resolved, "first_response_sla_met"] == 1)
        & (clean.loc[resolved, "resolution_sla_met"] == 1)
    ).astype(int)
    clean["is_reopened"] = (clean["reopened_count"].fillna(0) > 0).astype(int)
    clean["created_date"] = clean["created_at"].dt.date.astype(str)
    clean["created_month"] = clean["created_at"].dt.to_period("M").astype(str)
    clean["created_week"] = clean["created_at"].dt.to_period("W").astype(str)

    clean.to_csv(PROCESSED / "support_tickets_clean.csv", index=False)
    rejected.to_csv(PROCESSED / "rejected_support_rows.csv", index=False)

    quality = {
        "raw_rows": raw_rows,
        "exact_duplicates_removed": exact_duplicates,
        "valid_clean_rows": int(len(clean)),
        "rejected_rows": int(len(rejected)),
        "missing_values_after_cleaning": {k: int(v) for k, v in clean.isna().sum().to_dict().items()},
    }
    (PROCESSED / "data_quality_report.json").write_text(json.dumps(quality, indent=2), encoding="utf-8")
    print(json.dumps(quality, indent=2))


if __name__ == "__main__":
    main()
