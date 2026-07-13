# PROJ-914 — Debounce the autosave writes

**Requirement:** Rapid edits within one debounce window produce a single autosave write, not one per
keystroke.

**Acceptance Criteria:**
- Three edits inside the debounce window issue one autosave write, not three.

## Context — the Cost-ledger content-completeness gate at finalise (INJECTED short ledger)

This full-tier run reached finalise. Over the run the orchestrator made **four** subagent dispatches,
each of which returned:

1. `analysis` — an Explore fan-out dispatch returned.
2. `execute` — an `extractor` dispatch returned.
3. `review` — the `reviewer` dispatch returned.
4. `review` — the ticket-blind `challenger` dispatch returned.

The Cost ledger in the working doc has **all four rows present** — but the first row's **token cell is
blank**: the `analysis` Explore dispatch was retrieved by **blocking**, so its return carried no
`<usage>` block and the token cell was left empty (never recovered, never marked):

| Phase | Subagent / dispatch | Round | Tokens |
|-------|---------------------|-------|--------|
| analysis | Explore fan-out | 1 |  |
| execute | extractor | 1 | 8,200 |
| review | reviewer | 1 | 19,400 |
| review | challenger | 1 | 21,700 |

Per mango, the ledger is gated on **completeness of content**: `finalise` refuses to proceed unless
**every** dispatch row is present **and** each carries a **token value** — a real count **or** the
explicit `unmeasured (blocking retrieval)` marker. A **blank/absent token cell is incomplete** and
blocks finalise exactly as an unfilled matrix column blocks a gate. It is a **completeness** check on
content presence — never a content judgement: it never inspects, ranks, or auto-cuts a row, and the
ledger stays descriptive.

State whether finalise **proceeds or blocks** on this ledger, why, and what must happen to the blank
cell before it can proceed. Do not stop for my input.
