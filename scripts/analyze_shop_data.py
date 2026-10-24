#!/usr/bin/env python3
"""Validate and summarize small-shop orders and reviews using only stdlib."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ORDER_REQUIRED = {"order_id", "ordered_at", "product_id", "quantity", "unit_price"}
REVIEW_REQUIRED = {"review_id", "reviewed_at", "rating", "text"}
PRODUCT_REQUIRED = {"product_id", "product_name", "category"}
TRUE_VALUES = {"1", "true", "yes", "y", "是"}

THEMES = [
    ("waiting_time", ("wait", "slow", "queue", "等待时间", "等太久", "排队", "出餐慢", "取餐慢", "太慢", "服务慢")),
    ("product_quality", ("cold", "stale", "taste", "bad flavor", "冷", "难吃", "口味", "不新鲜")),
    ("price_value", ("price", "expensive", "value", "价格", "太贵", "性价比")),
    ("service", ("staff", "rude", "service", "店员", "态度", "服务")),
    ("availability", ("sold out", "unavailable", "缺货", "售罄", "卖完")),
    ("environment", ("clean", "seat", "noisy", "环境", "卫生", "座位", "太吵")),
]

REDACTION_PATTERNS = [
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[REDACTED_EMAIL]"),
    (re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)"), "[REDACTED_PHONE]"),
    (re.compile(r"(?<!\d)\d{17}[0-9Xx](?!\d)"), "[REDACTED_ID]"),
]


class DataError(Exception):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--products", type=Path)
    parser.add_argument("--orders", type=Path)
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def load_json(path: Path | None) -> dict:
    if path is None:
        return {}
    with path.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise DataError(f"Profile must be a JSON object: {path}")
    return value


def load_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = set(reader.fieldnames or [])
        missing = sorted(required - headers)
        if missing:
            raise DataError(f"{path.name} is missing required columns: {', '.join(missing)}")
        return [dict(row) for row in reader]


def parse_datetime(value: str, field: str) -> datetime:
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid {field}: {value!r}") from exc


def parse_number(value: str, field: str, minimum: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid {field}: {value!r}") from exc
    if number < minimum:
        raise ValueError(f"{field} must be >= {minimum}: {value!r}")
    return number


def rounded(value: float) -> float:
    return round(value + 0.0, 2)


def ratio(value: float) -> float:
    return round(value + 0.0, 4)


def time_window(hour: int) -> str:
    if 6 <= hour <= 10:
        return "morning"
    if 11 <= hour <= 13:
        return "lunch"
    if 14 <= hour <= 17:
        return "afternoon"
    if 18 <= hour <= 23:
        return "evening"
    return "overnight"


def redact(text: str) -> tuple[str, int]:
    result = text
    count = 0
    for pattern, replacement in REDACTION_PATTERNS:
        result, replacements = pattern.subn(replacement, result)
        count += replacements
    return result, count


def classify_theme(text: str) -> str:
    lowered = text.casefold()
    for theme, keywords in THEMES:
        if any(keyword.casefold() in lowered for keyword in keywords):
            return theme
    return "other"


def analyze_orders(
    rows: list[dict[str, str]], products: dict[str, dict[str, str]], validation: dict
) -> tuple[dict, list[datetime]]:
    valid = []
    skipped = 0
    for index, row in enumerate(rows, start=2):
        try:
            ordered_at = parse_datetime(row["ordered_at"], "ordered_at")
            quantity = parse_number(row["quantity"], "quantity", 0.000001)
            unit_price = parse_number(row["unit_price"], "unit_price")
            discount = parse_number(row.get("discount_amount") or "0", "discount_amount")
            gross = quantity * unit_price
            if discount > gross:
                raise ValueError("discount_amount exceeds line gross")
            valid.append(
                {
                    "order_id": row["order_id"].strip(),
                    "ordered_at": ordered_at,
                    "product_id": row["product_id"].strip(),
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "discount": discount,
                    "refunded": (row.get("refunded") or "").strip().casefold() in TRUE_VALUES,
                    "customer_id": (row.get("customer_id") or "").strip(),
                    "channel": (row.get("channel") or "unknown").strip() or "unknown",
                }
            )
        except ValueError as exc:
            skipped += 1
            validation["warnings"].append(f"orders.csv row {index} skipped: {exc}")

    validation["rows"]["orders"] = {"input": len(rows), "valid": len(valid), "skipped": skipped}
    if not valid:
        raise DataError("orders.csv has no valid rows")

    order_revenue = defaultdict(float)
    order_items = defaultdict(float)
    order_dates = {}
    refunded_orders = set()
    product_stats = defaultdict(lambda: {"quantity": 0.0, "net_revenue": 0.0, "refund_lines": 0})
    daily = defaultdict(lambda: {"order_ids": set(), "net_revenue": 0.0})
    windows = defaultdict(lambda: {"order_ids": set(), "net_revenue": 0.0})
    order_channels = {}
    customer_orders = defaultdict(set)
    discount_total = 0.0

    for row in valid:
        order_id = row["order_id"]
        order_dates.setdefault(order_id, row["ordered_at"])
        date_key = row["ordered_at"].date().isoformat()
        window = time_window(row["ordered_at"].hour)
        net_line = row["quantity"] * row["unit_price"] - row["discount"]
        discount_total += row["discount"]
        if row["refunded"]:
            refunded_orders.add(order_id)
            product_stats[row["product_id"]]["refund_lines"] += 1
            continue
        order_revenue[order_id] += net_line
        order_items[order_id] += row["quantity"]
        daily[date_key]["order_ids"].add(order_id)
        daily[date_key]["net_revenue"] += net_line
        windows[window]["order_ids"].add(order_id)
        windows[window]["net_revenue"] += net_line
        order_channels.setdefault(order_id, row["channel"])
        product_stats[row["product_id"]]["quantity"] += row["quantity"]
        product_stats[row["product_id"]]["net_revenue"] += net_line
        if row["customer_id"]:
            customer_orders[row["customer_id"]].add(order_id)

    order_count = len({row["order_id"] for row in valid})
    completed_order_count = len(order_revenue)
    net_revenue = sum(order_revenue.values())
    dates = [row["ordered_at"] for row in valid]
    distinct_days = len({item.date() for item in dates})

    if distinct_days < 7:
        validation["warnings"].append("Fewer than seven distinct order days; treat results as a short observation window.")

    product_output = []
    for product_id, values in product_stats.items():
        meta = products.get(product_id, {})
        product_output.append(
            {
                "product_id": product_id,
                "product_name": meta.get("product_name") or product_id,
                "category": meta.get("category") or "unknown",
                "quantity": rounded(values["quantity"]),
                "net_revenue": rounded(values["net_revenue"]),
                "refund_lines": values["refund_lines"],
            }
        )
    product_output.sort(key=lambda item: (-item["net_revenue"], item["product_id"]))

    sales = {
        "order_rows": len(valid),
        "orders": order_count,
        "completed_orders": completed_order_count,
        "refunded_orders": len(refunded_orders),
        "refund_rate": ratio(len(refunded_orders) / order_count) if order_count else None,
        "items_sold": rounded(sum(order_items.values())),
        "net_revenue": rounded(net_revenue),
        "discount_total": rounded(discount_total),
        "average_order_value": rounded(net_revenue / completed_order_count) if completed_order_count else None,
        "per_day": {
            "net_revenue": rounded(net_revenue / distinct_days) if distinct_days else None,
            "orders": rounded(completed_order_count / distinct_days) if distinct_days else None,
        },
        "daily": [
            {
                "date": day,
                "orders": len(values["order_ids"]),
                "net_revenue": rounded(values["net_revenue"]),
            }
            for day, values in sorted(daily.items())
        ],
        "time_windows": {
            name: {
                "orders": len(windows[name]["order_ids"]),
                "net_revenue": rounded(windows[name]["net_revenue"]),
            }
            for name in ("morning", "lunch", "afternoon", "evening", "overnight")
        },
        "products": product_output,
        "channels": dict(sorted(Counter(order_channels.values()).items())),
    }

    if customer_orders:
        repeat = sum(1 for order_ids in customer_orders.values() if len(order_ids) > 1)
        sales["customers"] = {
            "identified": len(customer_orders),
            "repeat_customers": repeat,
            "repeat_customer_rate": ratio(repeat / len(customer_orders)),
        }
    else:
        validation["warnings"].append("No usable customer_id values; repeat-customer metrics were omitted.")

    return sales, dates


def analyze_reviews(rows: list[dict[str, str]], validation: dict) -> tuple[dict, list[dict[str, str]], list[datetime]]:
    evidence = []
    ratings = []
    dates = []
    themes = Counter()
    skipped = 0
    redactions = 0

    for index, row in enumerate(rows, start=2):
        try:
            reviewed_at = parse_datetime(row["reviewed_at"], "reviewed_at")
            text = (row.get("text") or "").strip()
            if not text:
                raise ValueError("text is blank")
            rating_text = (row.get("rating") or "").strip()
            rating = None
            if rating_text:
                rating = int(rating_text)
                if not 1 <= rating <= 5:
                    raise ValueError("rating must be between 1 and 5")
                ratings.append(rating)
            clean_text, count = redact(text)
            redactions += count
            theme = classify_theme(clean_text)
            themes[theme] += 1
            dates.append(reviewed_at)
            evidence.append(
                {
                    "evidence_id": f"EV-R{len(evidence) + 1:03d}",
                    "review_id": row["review_id"].strip(),
                    "reviewed_at": reviewed_at.isoformat(),
                    "rating": "" if rating is None else str(rating),
                    "theme": theme,
                    "source": (row.get("source") or "unknown").strip() or "unknown",
                    "redacted_text": clean_text,
                }
            )
        except (TypeError, ValueError) as exc:
            skipped += 1
            validation["warnings"].append(f"reviews.csv row {index} skipped: {exc}")

    validation["rows"]["reviews"] = {"input": len(rows), "valid": len(evidence), "skipped": skipped}
    validation["redactions"] = redactions
    if not evidence:
        raise DataError("reviews.csv has no valid rows")
    if len(evidence) < 10:
        validation["warnings"].append("Fewer than ten reviews; theme counts are examples, not stable prevalence estimates.")

    negative_count = sum(1 for rating in ratings if rating <= 2)
    feedback = {
        "reviews": len(evidence),
        "rated_reviews": len(ratings),
        "average_rating": rounded(sum(ratings) / len(ratings)) if ratings else None,
        "negative_reviews": negative_count,
        "negative_rate": ratio(negative_count / len(ratings)) if ratings else None,
        "theme_counts": dict(sorted(themes.items(), key=lambda item: (-item[1], item[0]))),
        "theme_evidence": {
            theme: [item["evidence_id"] for item in evidence if item["theme"] == theme]
            for theme in sorted(themes)
        },
    }
    return feedback, evidence, dates


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    validation = {"status": "ok", "errors": [], "warnings": [], "rows": {}, "redactions": 0}

    try:
        if args.orders is None and args.reviews is None:
            raise DataError("Provide --orders, --reviews, or both")

        profile = load_json(args.profile)
        safe_profile = {
            key: profile.get(key)
            for key in ("shop_id", "shop_name", "category", "currency", "timezone", "objective", "data_origin", "source_url", "license", "seed")
            if profile.get(key) is not None
        }
        if not profile.get("data_origin"):
            validation["warnings"].append("Profile does not declare data_origin; disclose provenance before sharing results.")

        products = {}
        if args.products:
            product_rows = load_csv(args.products, PRODUCT_REQUIRED)
            products = {row["product_id"].strip(): row for row in product_rows if row["product_id"].strip()}
            validation["rows"]["products"] = {"input": len(product_rows), "valid": len(products), "skipped": len(product_rows) - len(products)}

        all_dates = []
        sales = None
        if args.orders:
            sales, order_dates = analyze_orders(load_csv(args.orders, ORDER_REQUIRED), products, validation)
            all_dates.extend(order_dates)

        feedback = None
        evidence = []
        if args.reviews:
            feedback, evidence, review_dates = analyze_reviews(load_csv(args.reviews, REVIEW_REQUIRED), validation)
            all_dates.extend(review_dates)

        period = {
            "start": min(all_dates).date().isoformat() if all_dates else None,
            "end": max(all_dates).date().isoformat() if all_dates else None,
            "distinct_order_days": len({item["date"] for item in sales["daily"]}) if sales else 0,
        }
        metrics = {
            "schema_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "profile": safe_profile,
            "period": period,
            "sales": sales,
            "feedback": feedback,
        }

        write_json(args.output_dir / "metrics.json", metrics)
        with (args.output_dir / "evidence.csv").open("w", encoding="utf-8", newline="") as handle:
            fields = ["evidence_id", "review_id", "reviewed_at", "rating", "theme", "source", "redacted_text"]
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(evidence)
    except (DataError, FileNotFoundError, json.JSONDecodeError) as exc:
        validation["status"] = "error"
        validation["errors"].append(str(exc))

    write_json(args.output_dir / "validation.json", validation)
    if validation["status"] == "error":
        print("Analysis failed; see validation.json", file=sys.stderr)
        return 2
    print(f"Wrote analysis to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
