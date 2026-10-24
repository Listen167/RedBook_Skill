#!/usr/bin/env python3
"""Compare two analysis metric files without making causal claims."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


METRICS = (
    "sales.net_revenue",
    "sales.orders",
    "sales.average_order_value",
    "sales.refund_rate",
    "sales.per_day.net_revenue",
    "sales.per_day.orders",
    "sales.time_windows.afternoon.orders",
    "sales.time_windows.afternoon.net_revenue",
    "feedback.average_rating",
    "feedback.negative_rate",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def nested(value: dict, path: str):
    current = value
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def main() -> int:
    args = parse_args()
    before = load(args.before)
    after = load(args.after)
    comparisons = {}

    for path in METRICS:
        old = nested(before, path)
        new = nested(after, path)
        if not isinstance(old, (int, float)) or not isinstance(new, (int, float)):
            continue
        absolute = round(new - old, 2)
        percent = None if old == 0 else round((new - old) / abs(old) * 100, 2)
        direction = "unchanged" if absolute == 0 else ("increased" if absolute > 0 else "decreased")
        comparisons[path] = {
            "before": old,
            "after": new,
            "absolute_change": absolute,
            "percent_change": percent,
            "direction": direction,
        }

    before_days = nested(before, "period.distinct_order_days") or 0
    after_days = nested(after, "period.distinct_order_days") or 0
    warnings = []
    if before_days and after_days and abs(before_days - after_days) / max(before_days, after_days) > 0.2:
        warnings.append("The periods differ in observed-day count by more than 20%; prefer per-day metrics.")
    if before.get("profile", {}).get("data_origin") != after.get("profile", {}).get("data_origin"):
        warnings.append("The periods declare different data origins; verify that comparison is meaningful.")

    output = {
        "schema_version": "1.0",
        "before_period": before.get("period"),
        "after_period": after.get("period"),
        "comparisons": comparisons,
        "warnings": warnings,
        "interpretation_boundary": "This before/after association does not by itself establish causality.",
        "competing_explanations_to_check": [
            "weekday mix",
            "stock availability",
            "weather or local events",
            "seasonality",
            "incomplete or changed data collection",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote comparison to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
