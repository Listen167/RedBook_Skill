# Privacy And Safety

## Data Minimization

Request only fields required by the selected mode. Aggregate outputs whenever record-level detail is unnecessary.

Do not request or retain:

- Names, phone numbers, email addresses, government identifiers, or exact home addresses.
- Payment card, bank account, authentication, or platform-session data.
- Health, ethnicity, religion, or other sensitive customer attributes.
- Private employee performance records.

Opaque customer IDs are optional and may be used only for aggregate repeat counts. Do not reproduce them in reports.

## Redaction

The analysis script redacts common phone, email, and identity-number patterns in review text. Treat this as a baseline, not a guarantee. Review `evidence.csv` before sharing or publishing it.

When a user supplies raw files:

1. Work on a copy or output directory; do not modify the source.
2. Report detected sensitive patterns in aggregate.
3. Stop before publishing or transmitting any record-level material.
4. Ask the user to confirm that they have authority to use the data.

## Platform Boundaries

Do not scrape review platforms, bypass access controls, reuse browser sessions, or automate account actions unless the user explicitly requests and authorizes that separate action. Prefer user exports, pasted feedback, or documented public datasets.

## Claim Boundaries

- Do not make accounting, tax, legal, medical, employment, or food-safety determinations.
- Do not infer protected or sensitive traits from purchasing behavior.
- Do not identify or rank individual customers or employees.
- Do not state that an intervention caused an outcome based only on before/after data.
- Disclose public-data licenses and synthetic-data generation in every public case study.
