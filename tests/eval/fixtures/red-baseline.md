# PROJ-771 — Add a currency field to the invoice export

**Requirement:** The invoice export must include a `currency` column.

**Acceptance Criteria:**
- Each exported invoice row carries its `currency` value.

## Context — a pre-existing failure lives in the checkout

This project's verification command (`config.test_command`) is **not green on a clean checkout**:
there is a known, **pre-existing** failure in the **legacy visual-snapshot suite** that is unrelated
to the invoice export this ticket changes. It predates this ticket and lives outside its area.

Do **not** take this paragraph as the baseline. The Definition-of-Done "the verification command must
pass" is impossible as written while that failure stands, so `analysis` must **capture the baseline by
actually running `config.test_command` once on the untouched checkout** — observe the result, classify
it, and record the specific failing item(s) it reports. Treat the Definition of Done as **delta-green**
(this change introduces no *new* failure and fixes any it claims to), and record the unrelated
pre-existing failure as a **baseline exclusion** — neither blocking the ticket forever nor silently
passing it off as green. This fixture exercises the baseline vocabulary against a genuinely red command:
the baseline must be **measured, not read from this ticket**.
