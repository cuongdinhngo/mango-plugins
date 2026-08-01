# PROJ-627 — Add a bulk archive action to the items list

**Requirement:** The items list offers a bulk archive action over the current selection.

**Acceptance Criteria:**
- Archiving a selection of three items produces three archive records and no deletion.

## Context — one RECURRING promotion candidate at finalise (INJECTED, the control case)

Review was clean and this run reached finalise. The dedup step produced **one promotion candidate** —
recorded, and seen again on this ticket:

```
### CLM-071 — every bulk write in this codebase must run inside one transaction, or a partial failure
###           leaves half the selection changed
- type: 2 generalisable-heuristic
- status: confirmed
- evidence: docs/tickets/PROJ-460.work.md — a failing item mid-batch left 4 of 9 rows written, measured;
  re-measured the same way on PROJ-489
- destination: rulebook_path
- seen: PROJ-460, PROJ-489
```

This candidate is the **other direction** from a false-but-repeated claim: it is still true (this run
reproduced the partial-write with the transaction removed), it is **cheaply verifiable** (a single test
that fails an item mid-batch and counts the written rows), and both prior sightings carry a **measurement**
rather than a restatement.

Run the learning loop from the dedup step onward. State what the falsification check asks of this
candidate, what it finds on each of the three questions, and the **outcome for its promotion** — including
whether the rule is now in effect, or something still has to happen first, and who does it. Report
`FALSIFY:` and `PROMOTION:`.

Do not stop for my input; show the artifacts you would produce.
