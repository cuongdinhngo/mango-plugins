# PROJ-867 — Reject negative quantities on the order form

**Requirement:** The order form rejects a negative quantity with a validation error.

**Acceptance Criteria:**
- Submitting a quantity of `-1` shows the "quantity must be positive" error and does not place the order.

## Round-1 review outcome (already run)

Round 1 dispatched the `reviewer` + the ticket-blind `challenger`. The challenger rebuilt the
requirement from the raw ticket and found it **met**. The proving test passed, the baseline was green,
and every layer-match verdict was recorded. The reviewer returned a **conditional LGTM** — *"LGTM once
findings 1–2 land as described"*:

1. `src/order/validate.js:20` — check the quantity **before** the total is computed.
2. `src/order/validate.js:27` — reuse the same error constant, not a duplicated string.

The author has applied exactly those two fixes to `src/order/validate.js` and nothing else — **no fix
changed scope**.

## What round 2 must do (the scoped verify-only pass)

This fixture exercises the **verify-only re-review** cost discipline. Round 2 is a **verify-only pass**:
confirm findings 1–2 are present as described and run a **regression scan** over the Phase-1 callers.
It must **carry forward round-1's verified facts** (the requirement reconstruction, the passing proving
test, the layer-match verdicts, the baseline) and **re-run only the proof affected by the two named
fixes** — it must **not** re-derive requirements and must **not** blanket-re-run the full
build/lint/tsc/test suite or re-read the files from scratch, because no fix changed scope. The
ticket-blind challenger's full re-derivation is **not repeated**. State exactly what round 2 re-runs
and what it reuses, and why this is consistently cheaper than the full round. Do not stop for my input.
