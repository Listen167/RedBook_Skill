# Diagnosis Rules

## Evidence Ladder

Use evidence in this order:

1. Deterministic metrics produced by the analysis script.
2. Redacted review evidence with stable `evidence_id` values.
3. Shop profile facts supplied by the user.
4. Explicit user observations.
5. Hypotheses to test.

Do not promote a hypothesis to a fact because it sounds plausible.

## Minimum Checks

Before diagnosing, inspect `validation.json` and confirm:

- At least one input mode completed without fatal errors.
- The analysis period and distinct day count are known.
- Skipped-row counts and parsing warnings are disclosed.
- Public or synthetic provenance is disclosed.
- No output contains unredacted customer identifiers.

## Select One Bottleneck

Create up to three candidates, then choose one. Score each candidate from 1 to 3 on impact, confidence, actionability, and effort. Use `priority = impact * confidence * actionability / effort`. The score ranks candidates; it does not prove business value. Show the component scores and supporting evidence.

Prefer a bottleneck that has both a transaction signal and feedback evidence. When only one source exists, narrow the claim accordingly.

## Metric Interpretation

- Compare revenue only across similar period lengths or use per-day values.
- Treat average order value separately from order volume.
- A product's low unit sales do not prove poor demand if it was unavailable.
- Refund frequency is a signal, not proof of product or service failure.
- Repeat-customer estimates require non-empty, stable customer IDs.
- Review theme counts are not representative market shares unless sampling is documented.
- Never invent industry benchmarks. Use only user-provided or cited benchmarks.

## Required Diagnosis Language

Each conclusion must be labelled:

- `FACT` followed by a metric path or evidence ID.
- `HYPOTHESIS` followed by the planned test.
- `UNKNOWN` followed by the smallest useful data request.

Example:

```text
FACT: Afternoon net revenue was CNY 420 across 5 observed days (`sales.time_windows.afternoon.net_revenue`).
FACT: Three wait-time complaints were found (EV-R002, EV-R006, EV-R009).
HYPOTHESIS: Slow preparation suppresses afternoon repeat visits; test a pre-batched pickup option for seven days.
UNKNOWN: Foot traffic was not supplied, so low orders cannot be separated from low conversion.
```

## Failure Behavior

If the input cannot support a responsible diagnosis, output a data-readiness plan instead. State the missing fields, why each matters, and the smallest collection method. Do not fill gaps with synthetic values unless the user explicitly selects demo mode.
