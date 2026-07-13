# PROJ-915 — Collapse duplicate webhook deliveries

**Requirement:** Two identical webhook events in one flush window are delivered once, not twice.

**Acceptance Criteria:**
- Two identical events in one window produce a single delivery.

## Context — a blocked dispatch's usage (for the Cost-ledger usage-surfacing step)

This full-tier run reached finalise. The orchestrator **blocked on its first dispatch** (`analysis`
Explore fan-out) via a synchronous `TaskOutput`-style retrieval — that return carried **no `<usage>`
block**. The other three dispatches (`extractor`, `reviewer`, `challenger`) landed as
`task-notification`s that **did** carry `<usage>`, so their token counts are known.

Per mango, **every dispatch row carries a value or an honest marker — never a silent blank.** In
priority order: **(a)** prefer a retrieval path that carries `<usage>` — let the dispatch complete as a
`task-notification`, or **re-query the completed task's usage record** after a blocking return — so even
the blocked first dispatch gets a real number; **(b)** only if the environment truly cannot surface
usage for that blocked dispatch, record its token cell as the explicit value **`unmeasured (blocking
retrieval)`** — never a fabricated number and never a silent blank.

Produce the Cost-ledger row for that **blocked** first dispatch, and state plainly what its token cell
holds (a recovered real count, or the explicit `unmeasured (blocking retrieval)` marker) and why it may
**never** be left blank or filled with an invented number. Do not stop for my input.
