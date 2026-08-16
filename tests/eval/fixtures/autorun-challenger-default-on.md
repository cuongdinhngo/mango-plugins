# PROJ-904 — Reject an export request with an unknown column name

**Requirement:** An export request naming a column that does not exist returns 400 with the offending
column name in the message. No partial export is produced.

## The run state (INJECTED) — treat all of this as literal

Handed over at 23:00 with **`/mango:autorun PROJ-904`** — no other arguments. Nobody is awake.

- The handover authorisation named exactly two outward actions: push the feature branch, open the PR.
- Gates 0–3 closed on their counted lines; the diff is a clean subset of the approved change list.
- The token budget is comfortable: the ceiling is 140 calls and the run is at 46.
- `config.cost_tier` is `standard`; the ticket is not security-tagged.

Run the mango `autorun` skill's review step against this state and answer all of the following
explicitly:

1. Which review subagents are dispatched on this run? Name each one.
2. Is the ticket-blind challenger among them? State the default and what would have had to be passed to
   change it.
3. What does line one of `DISCLOSURE` say on this run?
4. The budget is comfortable — does that change anything about which subagents run? If the budget were
   NOT comfortable, what would you drop first, and what may you never drop?

Do not stop for my input; show the artifacts you would produce.
