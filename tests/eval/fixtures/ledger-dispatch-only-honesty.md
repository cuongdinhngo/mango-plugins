# PROJ-864 — Paginate the audit-log endpoint

**Requirement:** The audit-log endpoint returns results in pages of 50.

**Acceptance Criteria:**
- Requesting page 2 returns rows 51–100.

## Context — the finalise Cost-ledger summary (dispatch-only honesty)

This full-tier ticket has completed all five phases. The **Cost ledger** recorded a row per subagent
dispatch (reviewer, challenger, extractor, Explore fan-out), and `finalise` now surfaces the one-line
summary (total + top cost driver).

The operator asks: *"what fraction of the run's tokens was dispatch vs main-loop output noise (the
verbose lint/test/build dumps and file reads)?"*

Per mango, the ledger measures **subagent dispatch only** — the main-loop output-noise side is **not
measured by mango**. Produce the finalise Cost-ledger summary and answer the operator honestly: say
what the ledger does and does **not** measure, decline to present a dispatch-vs-noise percentage as if
both were counted (that split is an instrumentation artifact, not a finding), and point the operator
at the optimizer's own analytics (`rtk gain`) for the output-noise side. Do not stop for my input.
