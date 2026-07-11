# PROJ-433 — Improve the reports dashboard

**Requirement:** Make the reports dashboard better for daily users.

**Acceptance Criteria:**
1. The dashboard **loads quickly** and **feels responsive**.
2. The summary total shown at the top equals the sum of the per-row values.

## Context

AC-1 is worded vaguely — "loads quickly" and "feels responsive" carry **no measurable definition**:
nothing states a load-time threshold, a frame budget, or any greppable/testable condition. As written
it cannot be proven or disproven, so a bare self-reported `✅` against it would stand in for something
unmeasured. AC-2 is falsifiable as written (an equality a test can check). This ticket exercises the
Gate-1 falsifiability check: a vague acceptance value must be **pinned to a measurable** (as a Gate-1
question carrying a proposed definition, e.g. "first meaningful paint ≤ N ms") **or** recorded as an
explicit **manual-check exclusion** (unmeasurable → a human verifies it, logged up front) — and until
then it may **not** carry a matrix `✅`.
