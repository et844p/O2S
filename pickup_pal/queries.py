"""BigQuery-backed pickup queries and Slack-ready formatters."""

from __future__ import annotations

from pathlib import Path

from gbq import query_df

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "sql" / "large_parcel"

QUERIES = {
    "extra_pickup": {
        "file": "extra_pickup_volume_check.sql",
        "description": "Check if a supplier has enough open volume for an extra pickup",
    },
    "pickups_this_week": {
        "file": "supplier_pickups_this_week.sql",
        "description": "Planned and executed pickups for the current week",
    },
    "typical_days": {
        "file": "typical_pickup_days.sql",
        "description": "Typical pickup days from FM planned trucks (12-week lookback)",
    },
}


def load_sql(name: str, supplier: str) -> str:
    sql_path = SQL_DIR / QUERIES[name]["file"]
    template = sql_path.read_text()
    return template.replace("{supplier_name}", supplier.replace("'", "''"))


def format_extra_pickup(df) -> str:
    if df.empty:
        return "No supplier match found."

    row = df.iloc[0]
    lines = [
        f"*{row['supplier_name']}* — Extra Pickup Volume Check",
        "",
        f"• *Recommendation:* {row['extra_pickup_recommendation']}",
        f"• *Open POs:* {int(row['open_po_count'])} "
        f"({int(row['open_not_late_yet'])} not late yet, {int(row['open_already_late'])} already late)",
        f"• *PO/PU target:* {int(row['po_pu'])}",
        f"• *Pickups needed (by volume):* {row['pickups_needed_by_open_volume']:.2f} "
        f"(~{int(row['pickups_needed_rounded'])} trailers)",
        f"• *Planned this week:* {int(row['planned_pickups_this_week'])} "
        f"({row['planned_pickup_days'] or 'none'})",
        f"• *Executed this week:* {int(row['executed_pickups_this_week'])}",
        f"• *Lane:* {row['lane_name']}",
    ]
    return "\n".join(lines)


def format_pickups_this_week(df) -> str:
    if df.empty:
        return "No supplier match found."

    row = df.iloc[0]
    lines = [
        f"*{row['supplier_name']}* — Pickups This Week",
        "",
        f"• *Week starting:* {row['week_start']}",
        f"• *Planned pickups:* {int(row['planned_pickups_this_week'])}",
        f"• *Executed pickups:* {int(row['executed_pickups_this_week'])}",
        f"• *Pickup days:* {row['pickup_days'] or 'none scheduled'}",
    ]

    breakdown = row.get("daily_breakdown")
    if breakdown is not None and len(breakdown):
        lines.append("")
        lines.append("*Daily breakdown:*")
        for day in breakdown:
            if day["planned_pickups"] > 0 or day["executed_pickups"] > 0:
                lines.append(
                    f"• {day['day_name']} ({day['day']}): "
                    f"{int(day['planned_pickups'])} planned, {int(day['executed_pickups'])} executed"
                )
    return "\n".join(lines)


def format_typical_days(df) -> str:
    if df.empty:
        return "No supplier match found."

    supplier = df.iloc[0]["supplier_name"]
    typical = df[df["pickup_frequency"] == "Typical"]["day_name"].tolist()
    occasional = df[df["pickup_frequency"] == "Occasional"]["day_name"].tolist()

    lines = [
        f"*{supplier}* — Typical Pickup Days (12-week lookback)",
        "",
        f"• *Typical days:* {', '.join(typical) if typical else 'none'}",
        f"• *Occasional days:* {', '.join(occasional) if occasional else 'none'}",
        "",
        "*By day of week:*",
    ]
    for _, row in df.iterrows():
        avg = row["avg_trucks_when_scheduled"]
        avg_display = avg if avg == avg else 0
        lines.append(
            f"• {row['day_name']}: {int(row['weeks_with_pickup'])} weeks with pickup, "
            f"avg {avg_display} trucks ({row['pickup_frequency'].lower()})"
        )
    return "\n".join(lines)


FORMATTERS = {
    "extra_pickup": format_extra_pickup,
    "pickups_this_week": format_pickups_this_week,
    "typical_days": format_typical_days,
}


def run_query(query_name: str, supplier: str, *, raw: bool = False) -> str:
    """Run a named query and return formatted text (or raw table string)."""
    if query_name not in QUERIES:
        raise ValueError(f"Unknown query: {query_name}")

    sql = load_sql(query_name, supplier)
    df = query_df(sql)

    if raw:
        return df.to_string(index=False)
    return FORMATTERS[query_name](df)
