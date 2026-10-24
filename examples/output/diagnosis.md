# Corner Cup Demo Growth Diagnosis

> Disclosure: every input and result in this example is synthetic and generated with seed `20261023`. It is an executable demonstration, not evidence about a real shop or a completed real-world experiment.

## Scope And Provenance

- Shop alias: Corner Cup Demo
- Objective: increase afternoon orders while keeping refund rate stable
- Baseline period: 2026-10-01 to 2026-10-07
- Input mode: full review
- Data origin: synthetic
- Data quality: 274/274 order rows, 14/14 reviews, and 6/6 products were valid; no rows were skipped

## Facts

| ID | Finding | Metric path or evidence ID |
|---|---|---|
| F1 | The baseline contains 227 orders and CNY 4,838 net revenue across seven days. | `sales.orders`, `sales.net_revenue` |
| F2 | Afternoon has 30 orders and CNY 655 net revenue, below every other active time window. | `sales.time_windows.afternoon` |
| F3 | Five of fourteen reviews are rated 2/5 and all five describe waiting uncertainty or delay. | `feedback.negative_reviews`; EV-R001 to EV-R005 |
| F4 | The baseline refund rate is 0.44%; the only refunded product line is Latte. | `sales.refund_rate`; `sales.products[P02].refund_lines` |

## Hypotheses

| ID | Explanation to test | Supporting facts | Falsifying signal |
|---|---|---|---|
| H1 | An unclear afternoon handoff process suppresses completed afternoon orders. | F2, F3 | The handoff change is followed by no improvement in afternoon orders or waiting feedback. |
| H2 | Afternoon demand is low regardless of service speed. | F2 | Orders increase during the same time window without a promotion or price change. |

## Unknowns

| Missing information | Why it matters | Smallest collection method |
|---|---|---|
| Afternoon foot traffic | Separates low demand from low conversion. | Seven hourly manual counts. |
| Actual preparation time | Tests whether perceived waiting matches production delay. | Record order-ready minutes for a sample of ten drinks per day. |
| Product availability | Prevents interpreting sold-out items as weak demand. | Mark each stockout and time. |

## Candidate Bottlenecks

| Candidate | Impact | Confidence | Actionability | Effort | Priority | Evidence |
|---|---:|---:|---:|---:|---:|---|
| Afternoon pickup uncertainty | 3 | 3 | 3 | 1 | 27 | F2, F3 |
| Low cheesecake volume | 2 | 1 | 2 | 2 | 2 | `sales.products[P06]`; availability unknown |
| Latte refund | 1 | 1 | 2 | 1 | 2 | F4; one event only |

## Selected Bottleneck

Afternoon pickup uncertainty ranks first because it appears in both transaction timing and every negative review, and the shop can test one handoff change within seven days. The evidence does not establish that waiting caused low demand.

## Seven-Day Experiment

- Decision: retain, revise, or stop a dedicated afternoon pickup handoff.
- Hypothesis: one visible pickup point with a stated order-ready sequence will increase afternoon completed orders and reduce waiting complaints.
- Primary intervention: from 14:00 to 17:00, route completed pickup orders through one clearly labelled handoff point and use the same ready-order callout.
- Primary metric: afternoon completed orders per observed day; baseline `30 / 7 = 4.29`.
- Target: at least 5.15 afternoon orders per day, a planning threshold of +20%, not an industry benchmark.
- Guardrails: refund rate must remain below 1%; stop if the workflow creates a safety obstruction or worsens median observed preparation time.
- Review date: after seven comparable operating days.

## Synthetic Comparison

The generated after period contains 74 afternoon orders versus 30 before, while negative review rate changes from 35.71% to 7.14%. These values were deliberately generated to exercise the comparison workflow. They are not real results, and the before/after association does not establish causality.

## Evidence Trail

- `examples/output/before/metrics.json`
- `examples/output/before/evidence.csv`
- `examples/output/before/validation.json`
- `examples/output/comparison.json`
