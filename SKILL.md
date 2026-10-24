---
name: local-shop-growth-loop
description: "Analyze small-shop orders, products, and customer feedback to produce an evidence-linked diagnosis, one measurable seven-day growth experiment, and an optional before/after review. Use for store performance reviews, order analysis, customer-review analysis, or weekly reviews of cafes, bakeries, food stalls, convenience shops, and similar local stores; also use to create a clearly labelled synthetic demo when no shop data exists. Do not use for bookkeeping, tax advice, autonomous platform scraping, or causal claims unsupported by the supplied data."
---

# 小店增长闭环

Turn a small shop's exported records into one practical experiment that can be measured on the next run. Prefer a narrow, defensible conclusion over a long list of generic suggestions.

## Choose The Mode

- **Full review:** orders plus reviews; products and shop profile are recommended.
- **Sales review:** orders only. Diagnose sales patterns, but do not infer customer sentiment.
- **Feedback review:** reviews only. Diagnose recurring feedback, but do not infer revenue impact.
- **Demo:** no user data. Run `scripts/prepare_demo.py`; label every resulting artifact as synthetic.
- **Comparison:** two completed analysis periods. Run `scripts/compare_periods.py` after analyzing each period separately.

## Workflow

1. Establish the shop objective, analysis period, and data provenance. Never describe public or synthetic data as the user's real business data.
2. For user-supplied files, read [references/input-schema.md](references/input-schema.md) and [references/privacy-and-safety.md](references/privacy-and-safety.md). Request only missing fields that block the selected mode.
3. Run `scripts/analyze_shop_data.py` for each period. Use its `metrics.json`, `evidence.csv`, and `validation.json` as the factual layer; do not silently recalculate or replace those values.
4. Read [references/diagnosis-rules.md](references/diagnosis-rules.md). Separate every substantive statement into:
   - **Fact:** directly supported by a metric or evidence ID.
   - **Hypothesis:** a plausible explanation that still requires testing.
   - **Unknown:** information the inputs cannot establish.
5. Select one bottleneck. Cite the supporting metric paths and feedback evidence IDs. If evidence is weak, say so and propose data collection instead of a confident diagnosis.
6. Read [references/experiment-design.md](references/experiment-design.md). Design one seven-day experiment with one primary intervention, one primary metric, guardrails, a stop condition, and a next-review date.
7. Render the deliverables from `assets/diagnosis-template.md` and `assets/experiment-plan-template.csv`. Use `assets/xiaohongshu-case-template.md` only when the user requests a public case note.
8. For a later period, analyze it independently and then run `scripts/compare_periods.py`. Describe changes as associations, not proof that the intervention caused them.

## Commands

Generate a deterministic two-period demo:

```bash
python scripts/prepare_demo.py --output-dir demo-data
```

Analyze one period:

```bash
python scripts/analyze_shop_data.py --profile demo-data/before/shop_profile.json --products demo-data/before/products.csv --orders demo-data/before/orders.csv --reviews demo-data/before/reviews.csv --output-dir analysis/before
```

Compare periods:

```bash
python scripts/compare_periods.py --before analysis/before/metrics.json --after analysis/after/metrics.json --output analysis/comparison.json
```

## Required Deliverables

Produce these unless the selected mode makes one inapplicable:

1. `diagnosis.md`: scope, data quality, facts, hypotheses, unknowns, one bottleneck, and evidence trail.
2. `experiment-plan.csv`: seven daily actions with owner, metric, guardrail, and completion status.
3. Script outputs: `metrics.json`, `evidence.csv`, and `validation.json`.
4. `comparison.json` and a short comparison section when two periods exist.
5. `xiaohongshu-case.md` only on request; disclose synthetic/public data and anonymization prominently.

## Hard Rules

- Never fabricate transactions, reviews, benchmarks, user feedback, or experiment results.
- Never join unrelated public datasets and present them as one shop's history.
- Never expose names, phone numbers, email addresses, government IDs, exact addresses, payment details, or raw customer identifiers.
- Never scrape or log in to a platform without the user's explicit request and authorization.
- Never provide accounting, tax, legal, medical, or food-safety determinations.
- Do not recommend broad price cuts by default. Treat pricing changes as bounded experiments with margin guardrails.
- Do not claim causality from a before/after comparison. State competing explanations and material data limitations.
- Stop and ask for confirmation before publishing, contacting a shop, modifying source data, or taking any external action.

## Resource Routing

- Read `references/input-schema.md` when mapping or validating data.
- Read `references/privacy-and-safety.md` whenever raw user or customer data is involved.
- Read `references/diagnosis-rules.md` after deterministic analysis succeeds.
- Read `references/experiment-design.md` only when drafting or reviewing an experiment.
- Use `examples/` to understand the expected artifact shape, not as evidence about a real shop.
