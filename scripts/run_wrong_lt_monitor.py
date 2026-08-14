#!/usr/bin/env python3
"""Daily wrong lead-time (LT) monitor with open/resolved/reopened tracking.

Runs sql/wrong_lt_monitor.sql for yesterday's DS US/CA orders, diffs against
the prior open-issue state, and writes:
  - CSV of today's mismatches
  - JSON state for the next run
  - Slack-ready markdown summary (stdout + file)

Issue key grain:
  supplierid | Supplierpartid | ship_class_group | su_lt_type
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_default_creds = ROOT / ".gcp" / "credentials.json"
if _default_creds.exists():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(_default_creds)

from gbq import query_df

SQL_PATH = ROOT / "sql" / "wrong_lt_monitor.sql"
OUTPUT_DIR = ROOT / "output" / "wrong_lt_monitor"
STATE_PATH = OUTPUT_DIR / "state.json"

ISSUE_KEY_COLS = ["supplierid", "Supplierpartid", "ship_class_group", "su_lt_type"]


def _norm_key_part(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def issue_key(row: pd.Series | dict[str, Any]) -> str:
    parts = [_norm_key_part(row.get(c) if isinstance(row, dict) else row[c]) for c in ISSUE_KEY_COLS]
    return "|".join(parts)


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "version": 1,
            "last_run_date": None,
            "open_issues": {},
            "resolved_history": {},
        }
    return json.loads(path.read_text())


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def aggregate_issues(df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """Collapse OPID rows into issue keys with representative metadata."""
    if df.empty:
        return {}

    working = df.copy()
    working["_issue_key"] = working.apply(issue_key, axis=1)

    issues: dict[str, dict[str, Any]] = {}
    for key, group in working.groupby("_issue_key", dropna=False):
        first = group.iloc[0]
        issues[str(key)] = {
            "supplierid": _norm_key_part(first.get("supplierid")),
            "suname": _norm_key_part(first.get("suname")),
            "SupplierPartNumber": _norm_key_part(first.get("SupplierPartNumber")),
            "Supplierpartid": _norm_key_part(first.get("Supplierpartid")),
            "ship_class_group": _norm_key_part(first.get("ship_class_group")),
            "su_lt_type": _norm_key_part(first.get("su_lt_type")),
            "expected_lt": _norm_key_part(first.get("expected_lt")),
            "actual_lt": _norm_key_part(first.get("actual_lt")),
            "opid_count": int(group["opid"].nunique()) if "opid" in group.columns else len(group),
            "sample_opids": [
                _norm_key_part(v) for v in group["opid"].dropna().astype(str).unique()[:5]
            ]
            if "opid" in group.columns
            else [],
        }
    return issues


def classify(
    current: dict[str, dict[str, Any]],
    previous_open: dict[str, dict[str, Any]],
    resolved_history: dict[str, dict[str, Any]],
) -> dict[str, list[str]]:
    current_keys = set(current)
    previous_keys = set(previous_open)
    previously_resolved = set(resolved_history)

    new = sorted(current_keys - previous_keys - previously_resolved)
    reopened = sorted((current_keys - previous_keys) & previously_resolved)
    ongoing = sorted(current_keys & previous_keys)
    resolved = sorted(previous_keys - current_keys)
    return {
        "new": new,
        "reopened": reopened,
        "ongoing": ongoing,
        "resolved": resolved,
    }


def _fmt_issue(issue: dict[str, Any]) -> str:
    name = issue.get("suname") or "unknown"
    sid = issue.get("supplierid") or "?"
    part = issue.get("SupplierPartNumber") or issue.get("Supplierpartid") or "?"
    ship = issue.get("ship_class_group") or "?"
    lt_type = issue.get("su_lt_type") or "?"
    expected = issue.get("expected_lt") or "?"
    actual = issue.get("actual_lt") or "?"
    n = issue.get("opid_count", 0)
    return (
        f"• `{sid}` {name} | part `{part}` | {ship} | {lt_type} | "
        f"expected {expected}h vs actual {actual}h | {n} opid(s)"
    )


def _top_suppliers(issues: dict[str, dict[str, Any]], limit: int = 10) -> list[str]:
    """Roll open issues up to supplier for a compact Slack summary."""
    if not issues:
        return []
    rows: dict[str, dict[str, Any]] = {}
    for issue in issues.values():
        sid = issue.get("supplierid") or "?"
        entry = rows.setdefault(
            sid,
            {"suname": issue.get("suname") or "unknown", "issues": 0, "opids": 0},
        )
        entry["issues"] += 1
        entry["opids"] += int(issue.get("opid_count") or 0)
    ranked = sorted(rows.items(), key=lambda kv: (-kv[1]["opids"], -kv[1]["issues"], kv[0]))
    lines = []
    for sid, meta in ranked[:limit]:
        lines.append(
            f"• `{sid}` {meta['suname']} — {meta['issues']} issue(s), {meta['opids']} opid(s)"
        )
    if len(ranked) > limit:
        lines.append(f"_…and {len(ranked) - limit} more suppliers_")
    return lines


def build_slack_message(
    run_date: str,
    as_of_order_date: str,
    buckets: dict[str, list[str]],
    issues: dict[str, dict[str, Any]],
    previous_open: dict[str, dict[str, Any]],
    max_rows: int = 15,
) -> str:
    n_new = len(buckets["new"])
    n_reopened = len(buckets["reopened"])
    n_ongoing = len(buckets["ongoing"])
    n_resolved = len(buckets["resolved"])
    n_open = n_new + n_reopened + n_ongoing

    if n_open == 0 and n_resolved == 0:
        status = "ALL CLEAR"
        headline = f":white_check_mark: *Wrong LT monitor — {status}*"
        body = (
            f"No incorrect lead-time assignments for order date `{as_of_order_date}` "
            f"(run `{run_date}`)."
        )
        return f"{headline}\n{body}\n"

    if n_open == 0 and n_resolved > 0:
        status = "RESOLVED"
        headline = f":tada: *Wrong LT monitor — {status}*"
    elif n_reopened > 0:
        status = "REOPENED ISSUES"
        headline = f":rotating_light: *Wrong LT monitor — {status}*"
    elif n_new > 0:
        status = "NEW ISSUES"
        headline = f":warning: *Wrong LT monitor — {status}*"
    else:
        status = "ONGOING"
        headline = f":large_orange_circle: *Wrong LT monitor — {status}*"

    total_opids = sum(int(i.get("opid_count") or 0) for i in issues.values())
    lines = [
        headline,
        f"Order date: `{as_of_order_date}` · Run: `{run_date}`",
        (
            f"Open: *{n_open}* issue keys / *{total_opids}* opids "
            f"(new {n_new} · reopened {n_reopened} · ongoing {n_ongoing}) · "
            f"Resolved today: *{n_resolved}*"
        ),
        "",
    ]

    top = _top_suppliers(issues)
    if top:
        lines.append("*Top suppliers (open)*")
        lines.extend(top)
        lines.append("")

    def _section(title: str, keys: list[str], source: dict[str, dict[str, Any]]) -> None:
        if not keys:
            return
        lines.append(f"*{title}* ({len(keys)})")
        for key in keys[:max_rows]:
            lines.append(_fmt_issue(source[key]))
        if len(keys) > max_rows:
            lines.append(f"_…and {len(keys) - max_rows} more_")
        lines.append("")

    _section("Reopened", buckets["reopened"], issues)
    _section("New", buckets["new"], issues)
    _section("Resolved", buckets["resolved"], previous_open)
    if buckets["ongoing"] and (n_new or n_reopened or n_resolved):
        _section("Still open", buckets["ongoing"], issues)
    elif buckets["ongoing"] and not (n_new or n_reopened or n_resolved):
        _section("Ongoing (unchanged)", buckets["ongoing"], issues)

    return "\n".join(lines).rstrip() + "\n"


def update_state(
    state: dict[str, Any],
    run_date: str,
    as_of_order_date: str,
    current: dict[str, dict[str, Any]],
    buckets: dict[str, list[str]],
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    previous_open = state.get("open_issues", {})
    resolved_history = dict(state.get("resolved_history", {}))

    # Newly resolved → history
    for key in buckets["resolved"]:
        payload = dict(previous_open.get(key, {}))
        payload["resolved_on"] = as_of_order_date
        payload["last_seen_run"] = run_date
        resolved_history[key] = payload

    # Reopened → leave history (so future reopen detection still works) but mark
    for key in buckets["reopened"]:
        if key in resolved_history:
            resolved_history[key]["reopened_on"] = as_of_order_date
            resolved_history[key]["last_reopened_run"] = run_date

    # Open set becomes today's current issues (with first_seen preserved)
    open_issues: dict[str, dict[str, Any]] = {}
    for key, issue in current.items():
        prior = previous_open.get(key, {})
        first_seen = prior.get("first_seen_order_date") or as_of_order_date
        status = (
            "reopened"
            if key in buckets["reopened"]
            else "new"
            if key in buckets["new"]
            else "ongoing"
        )
        open_issues[key] = {
            **issue,
            "first_seen_order_date": first_seen,
            "last_seen_order_date": as_of_order_date,
            "status": status,
            "updated_at": now,
        }

    return {
        "version": 1,
        "last_run_date": run_date,
        "last_order_date": as_of_order_date,
        "updated_at": now,
        "open_issues": open_issues,
        "resolved_history": resolved_history,
        "last_buckets": {k: len(v) for k, v in buckets.items()},
    }


def should_notify(buckets: dict[str, list[str]], notify_ongoing: bool) -> bool:
    if buckets["new"] or buckets["reopened"] or buckets["resolved"]:
        return True
    if notify_ongoing and buckets["ongoing"]:
        return True
    # Explicit all-clear when we just cleared the board
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sql",
        type=Path,
        default=SQL_PATH,
        help="Path to wrong LT SQL",
    )
    parser.add_argument(
        "--state",
        type=Path,
        default=STATE_PATH,
        help="Path to persistent state JSON",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Directory for CSV/summary artifacts",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip BigQuery; classify an empty result against existing state",
    )
    parser.add_argument(
        "--notify-ongoing",
        action="store_true",
        help="Emit a Slack message even when only ongoing issues remain",
    )
    parser.add_argument(
        "--max-slack-rows",
        type=int,
        default=15,
        help="Max issues listed per Slack section",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    run_date = date.today().isoformat()
    as_of_order_date = (date.today() - timedelta(days=1)).isoformat()

    state = load_state(args.state)
    previous_open = state.get("open_issues", {})
    resolved_history = state.get("resolved_history", {})

    if args.dry_run:
        df = pd.DataFrame(columns=ISSUE_KEY_COLS + ["opid", "suname", "expected_lt", "actual_lt"])
        print("Dry run: skipping BigQuery (empty current mismatches).")
    else:
        df = query_df(args.sql.read_text())

    csv_path = args.output_dir / f"wrong_lt_{as_of_order_date}.csv"
    df.to_csv(csv_path, index=False)

    current = aggregate_issues(df)
    buckets = classify(current, previous_open, resolved_history)
    new_state = update_state(state, run_date, as_of_order_date, current, buckets)
    save_state(args.state, new_state)

    slack_msg = build_slack_message(
        run_date=run_date,
        as_of_order_date=as_of_order_date,
        buckets=buckets,
        issues=current,
        previous_open=previous_open,
        max_rows=args.max_slack_rows,
    )
    (args.output_dir / "slack_message.md").write_text(slack_msg)
    (args.output_dir / "latest_summary.md").write_text(slack_msg)

    notify = should_notify(buckets, notify_ongoing=args.notify_ongoing)
    # Always notify on true all-clear after prior open issues, or first clean baseline
    if not notify and not any(buckets.values()) and previous_open:
        notify = True
        slack_msg = build_slack_message(
            run_date=run_date,
            as_of_order_date=as_of_order_date,
            buckets=buckets,
            issues=current,
            previous_open=previous_open,
            max_rows=args.max_slack_rows,
        )
        (args.output_dir / "slack_message.md").write_text(slack_msg)

    print(slack_msg)
    print("---")
    print(f"rows={len(df)} issues={len(current)} notify={notify}")
    print(f"csv={csv_path}")
    print(f"state={args.state}")
    print(f"slack={args.output_dir / 'slack_message.md'}")
    print(f"buckets={json.dumps({k: len(v) for k, v in buckets.items()})}")


if __name__ == "__main__":
    main()
