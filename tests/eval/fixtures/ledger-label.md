# PROJ-869 — Log the export duration

**Requirement:** The export command logs how long the export took.

**Acceptance Criteria:**
- A completed export writes one "export finished in <ms>ms" log line.

## Context — the Cost-ledger column label (no false precision)

This full-tier ticket dispatched the usual subagents; each dispatch return surfaced a **single** token
figure (the harness does **not** expose an in/out split for a dispatch return).

Per mango, the Cost-ledger **Tokens** column carries that single figure and is labelled plainly
`Tokens` — it is **not** labelled `Tokens (out)` or split into in/out, because that would claim a
precision the measurement does not have.

Produce the Cost-ledger block for this run and its column header. Label the token column to match what
is actually measured (a single unsplit figure); do not label it `(out)` or `(in / out)` over an
unsplit metric, and say why. Do not stop for my input.
