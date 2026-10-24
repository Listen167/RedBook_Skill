# Input Schema

Use UTF-8 CSV files with a header row. Column names are case-sensitive. Extra columns may remain in source files but are ignored unless mapped explicitly.

## `shop_profile.json`

Recommended fields:

| Field | Type | Meaning |
|---|---|---|
| `shop_id` | string | Non-sensitive shop identifier |
| `shop_name` | string | Public name or anonymous alias |
| `category` | string | For example `cafe`, `bakery`, or `food-stall` |
| `currency` | string | Currency code such as `CNY` |
| `timezone` | string | Reporting timezone |
| `objective` | string | One outcome the shop wants to improve |
| `data_origin` | string | `user-provided`, `public`, or `synthetic` |
| `source_url` | string | Required when `data_origin` is `public` |
| `license` | string | Required when `data_origin` is `public` |

Never infer `data_origin`. Missing provenance is a validation warning and must be disclosed in the diagnosis.

## `orders.csv`

Required columns:

| Column | Format | Rule |
|---|---|---|
| `order_id` | string | Stable within one analysis period |
| `ordered_at` | ISO 8601 datetime | Local shop time unless profile says otherwise |
| `product_id` | string | One row per line item |
| `quantity` | positive number | Zero and negative values are invalid |
| `unit_price` | non-negative number | Price before line discount |

Optional columns:

| Column | Format | Default |
|---|---|---|
| `discount_amount` | non-negative number | `0` |
| `refunded` | boolean | `false` |
| `customer_id` | opaque string | blank; used only for aggregate repeat counts |
| `channel` | string | `unknown` |

The script calculates line revenue as `quantity * unit_price - discount_amount`. Refunded lines are excluded from net revenue and counted separately. Do not include payment cards, phone numbers, names, or addresses.

## `products.csv`

Required columns are `product_id`, `product_name`, and `category`. Optional columns are `unit_price`, `unit_cost`, and `active`. Unit cost is used only when supplied; never invent margin figures.

## `reviews.csv`

Required columns:

| Column | Format | Rule |
|---|---|---|
| `review_id` | string | Stable within one period |
| `reviewed_at` | ISO 8601 date or datetime | Must fall near the period or be explained |
| `rating` | integer 1-5 | Blank is allowed only if all ratings are absent |
| `text` | string | Customer-provided feedback |

Optional columns are `source` and `order_id`. The script redacts common phone, email, and identity-number patterns before writing `evidence.csv`.

## Partial Modes

- Orders without products: product IDs remain usable, but output names and categories may be missing.
- Reviews without orders: report feedback frequency, not revenue impact.
- Orders without customer IDs: omit repeat-customer metrics.
- Fewer than seven distinct sales days: describe the result as a short observation window.
- Fewer than ten reviews: treat theme counts as examples, not stable prevalence estimates.

## Public And Synthetic Data

Keep provenance adjacent to the data. For public data, record the source URL, creator, license, retrieval date, and transformations. For synthetic data, record the generator and seed. Never combine unrelated order and review datasets into a claimed real case.

Recommended public benchmarks:

- UCI Online Retail: <https://archive.ics.uci.edu/dataset/352/online+retail>. Real transaction data, CC BY 4.0. Use a documented subset to test transaction metrics.
- UCI Sentiment Labelled Sentences: <https://archive.ics.uci.edu/dataset/331/sentiment+labelled+sentences>. Includes a small Yelp restaurant-review subset, CC BY 4.0. Use it only as an independent feedback-classification test.
- Olist Brazilian E-Commerce: <https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce>. Anonymized linked orders and reviews under CC BY-NC-SA 4.0. Use for non-commercial development only unless the intended competition or commercial use is confirmed to comply with the license; do not redistribute it inside this skill by default.

Do not join the two UCI datasets as if their transactions and reviews belong to the same shop. Keep full public datasets outside the skill package; package only small attributed fixtures when their license allows redistribution.
