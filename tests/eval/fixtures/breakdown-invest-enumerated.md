# PROJ-821 — Break down the notifications suite epic

**Requirement:** This epic (a notifications suite: in-app inbox, email digest, push delivery, and a
per-user preference centre) has cleared analysis(epic) and design(epic). Run `breakdown` to split it
into tickets.

## Context

`breakdown` emits a **counted** ticket list. The per-ticket **INVEST self-check must be ENUMERATED** —
all six letters checked per ticket (Independent, Negotiable, Valuable, Estimable, Small, Testable), each
either affirmed with a one-clause reason or marked N/A-with-reason. A **single descriptive sentence
labelled "INVEST" is a finding** — a nominal one-liner is INVEST theatre and cannot catch a boundary
problem.

A ticket that **fails a letter is a breakdown finding → re-split before ratification**. For example,
one proposed ticket — **"the whole preference centre + push delivery + email digest as one ticket"** —
is clearly **not Small** (three deliverables) and arguably **not Independent** (push delivery entangled
with delivery preferences). Per mango this ticket must be **flagged and re-split** before the human
ratifies the list; it may not be carried to the split-gate as-is. (Non-vacuous: the failing "Small"
letter must be caught, not rubber-stamped.)

The human holds the split-gate — the ticket list (and any re-split) is ratified before any ticket
executes.
