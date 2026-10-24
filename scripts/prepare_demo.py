#!/usr/bin/env python3
"""Generate a deterministic, explicitly synthetic two-period cafe demo."""

from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path


PRODUCTS = [
    ("P01", "Americano", "drink", 16, 5),
    ("P02", "Latte", "drink", 22, 8),
    ("P03", "Fruit Tea", "drink", 18, 6),
    ("P04", "Croissant", "bakery", 15, 7),
    ("P05", "Chicken Sandwich", "food", 26, 12),
    ("P06", "Cheesecake", "dessert", 28, 13),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261023)
    return parser.parse_args()


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def make_period(root: Path, start: datetime, improved: bool, rng: random.Random, seed: int) -> None:
    root.mkdir(parents=True, exist_ok=True)
    profile = {
        "shop_id": "demo-corner-cup",
        "shop_name": "Corner Cup Demo",
        "category": "cafe",
        "currency": "CNY",
        "timezone": "Asia/Shanghai",
        "objective": "Increase weekday afternoon orders while keeping refund rate stable.",
        "data_origin": "synthetic",
        "seed": seed,
        "scenario_note": "After period simulates an afternoon pickup workflow; it is not a real experiment result.",
    }
    (root / "shop_profile.json").write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(
        root / "products.csv",
        ["product_id", "product_name", "category", "unit_price", "unit_cost", "active"],
        [
            {
                "product_id": pid,
                "product_name": name,
                "category": category,
                "unit_price": price,
                "unit_cost": cost,
                "active": "true",
            }
            for pid, name, category, price, cost in PRODUCTS
        ],
    )

    orders = []
    order_number = 1
    windows = [(8, 12), (12, 9), (15, 10 if improved else 5), (19, 7)]
    product_weights = [0.28, 0.26, 0.13, 0.15, 0.1, 0.08]
    for day in range(7):
        current = start + timedelta(days=day)
        for hour, count in windows:
            for offset in range(count + rng.randint(-1, 1)):
                order_id = f"{'A' if improved else 'B'}-{order_number:04d}"
                customer_id = f"C-{rng.randint(1, 95):03d}"
                product = rng.choices(PRODUCTS, weights=product_weights, k=1)[0]
                order_time = current.replace(hour=hour, minute=(offset * 7 + rng.randint(0, 6)) % 60)
                refunded = (not improved and product[0] == "P02" and hour == 15 and rng.random() < 0.12)
                orders.append(
                    {
                        "order_id": order_id,
                        "ordered_at": order_time.isoformat(),
                        "product_id": product[0],
                        "quantity": 1,
                        "unit_price": product[3],
                        "discount_amount": 0,
                        "refunded": str(refunded).lower(),
                        "customer_id": customer_id,
                        "channel": "walk_in" if rng.random() < 0.72 else "pickup",
                    }
                )
                if rng.random() < 0.22:
                    addon = PRODUCTS[3]
                    orders.append(
                        {
                            "order_id": order_id,
                            "ordered_at": order_time.isoformat(),
                            "product_id": addon[0],
                            "quantity": 1,
                            "unit_price": addon[3],
                            "discount_amount": 0,
                            "refunded": "false",
                            "customer_id": customer_id,
                            "channel": orders[-1]["channel"],
                        }
                    )
                order_number += 1

    write_csv(
        root / "orders.csv",
        ["order_id", "ordered_at", "product_id", "quantity", "unit_price", "discount_amount", "refunded", "customer_id", "channel"],
        orders,
    )

    positive = [
        "咖啡味道稳定，取餐也很方便。",
        "店员服务很友好，下次还会来。",
        "可颂很新鲜，搭配拿铁不错。",
        "环境干净，下午适合短暂休息。",
    ]
    waiting = [
        "下午等太久，拿铁出餐慢。",
        "排队不长但等饮品花了很久。",
        "服务态度不错，不过下午取餐太慢。",
        "赶时间时不敢点拿铁，等待时间不确定。",
    ]
    reviews = []
    for index in range(14):
        use_waiting = index < (1 if improved else 5)
        text = rng.choice(waiting if use_waiting else positive)
        reviews.append(
            {
                "review_id": f"{'AR' if improved else 'BR'}-{index + 1:03d}",
                "reviewed_at": (start + timedelta(days=index % 7, hours=15)).isoformat(),
                "rating": 2 if use_waiting else rng.choice([4, 5]),
                "text": text,
                "source": "synthetic_demo",
                "order_id": "",
            }
        )
    write_csv(root / "reviews.csv", ["review_id", "reviewed_at", "rating", "text", "source", "order_id"], reviews)


def main() -> int:
    args = parse_args()
    rng = random.Random(args.seed)
    make_period(args.output_dir / "before", datetime(2026, 10, 1), False, rng, args.seed)
    make_period(args.output_dir / "after", datetime(2026, 10, 8), True, rng, args.seed)
    print(f"Wrote synthetic demo data to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
