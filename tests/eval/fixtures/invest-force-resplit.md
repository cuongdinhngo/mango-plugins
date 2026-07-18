# PROJ-831 — Break down the billing epic (INVEST force-re-split)

**Requirement:** This epic (a billing suite) has cleared analysis(epic) and design(epic). Run
`breakdown` to split it into tickets, emitting the **counted** ticket list with a per-ticket **six-letter
enumerated INVEST self-check** (Independent, Negotiable, Valuable, Estimable, Small, Testable).

## Context — one oversized ticket, one right-sized control

Two proposed tickets to check:

- **Oversized (fails Small):** *"invoice generation + payment capture + dunning retries + refund
  handling as ONE ticket"* — this **bundles four independent deliverables**. It clearly **fails Small**
  (four deliverables) and arguably **fails Independent** (payment capture entangled with refunds). Per
  mango this ticket must be **flagged AND actually re-split** — broken into smaller tickets **before the
  split-gate ratifies** — not merely noted and carried through as-is. This is the "flag → re-split" ACT
  half: detection alone is not enough; the ticket must be split.

- **Right-sized control (passes):** *"add a downloadable PDF invoice"* — a single, independent,
  right-sized deliverable that passes the INVEST check. It must **NOT** be split — non-vacuous proof that
  breakdown re-splits the oversized ticket specifically, not every ticket.

The human holds the split-gate — the ticket list (after any re-split) is ratified before any ticket
executes.
