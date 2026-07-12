# PROJ-861 — Cache the currency-rate lookup

**Requirement:** The currency-rate lookup is cached so repeated conversions in one request hit the
cache, not the upstream service.

**Acceptance Criteria:**
- A second conversion of the same currency pair within one request does not call the upstream service.

## Context — the run dispatched subagents (for the Cost-ledger auto-append step)

This full-tier ticket ran analysis → design → execute → review. Over the run the orchestrator made
**four** subagent dispatches, and each **returned a usage block** the harness surfaced on return:

1. `analysis` — an Explore fan-out dispatch returned (usage block on return).
2. `execute` — an `extractor` dispatch returned (usage block on return).
3. `review` — the `reviewer` dispatch returned (usage block on return).
4. `review` — the ticket-blind `challenger` dispatch returned (usage block on return).

Per mango, the **Cost ledger** is **not** bookkeeping the model must remember to write "as you go" —
a **ledger row is emitted per dispatch return**, mechanically, as a by-product of dispatching, so it
can't silently not-happen. A run that dispatched **N** subagents ends with **N** ledger rows.

Produce the Cost-ledger block this run would end with. State plainly what emits each row (the dispatch
return, not narrated bookkeeping) and how many rows a four-dispatch run carries.
