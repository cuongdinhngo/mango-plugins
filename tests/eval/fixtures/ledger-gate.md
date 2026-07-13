# PROJ-902 — Batch the audit-log writes

**Requirement:** Audit-log entries produced within one request are written in a single batch, not one
insert per entry.

**Acceptance Criteria:**
- A request producing three audit entries issues one batched write, not three.

## Context — the Cost-ledger dispatch-count gate at finalise

This full-tier run reached finalise. Over the run the orchestrator made **four** subagent dispatches,
each of which **returned a usage block** the harness surfaced on return:

1. `analysis` — an Explore fan-out dispatch returned.
2. `execute` — an `extractor` dispatch returned.
3. `review` — the `reviewer` dispatch returned.
4. `review` — the ticket-blind `challenger` dispatch returned.

But the Cost ledger in the working doc currently has **only 2 rows** — two dispatch returns were never
transcribed. Per mango, the ledger is gated on **completeness**: `finalise` runs a **dispatch-count
check** and **refuses to proceed if the ledger has fewer rows than the run's dispatch count** — an
incomplete ledger blocks finalise exactly as an unfilled matrix column blocks a gate. It is a
**completeness** check, not a content check: it never inspects, ranks, or auto-cuts a row, and the
ledger stays descriptive.

State whether finalise **proceeds or blocks** here, why, and what must happen before it can proceed.
Do not stop for my input.
