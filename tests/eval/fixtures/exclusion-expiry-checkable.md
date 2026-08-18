# PROJ-411 — Two deferred checks on the reporting export

**Requirement:** The nightly export produces a report file the finance team downloads.

**Goal:** The export is correct and the layout matches the finance template.

**Acceptance Criteria:**
- AC1: every row in the source table appears in the export (unit-testable — measurable).
- AC2: the export renders correctly in the finance team's spreadsheet tool, which this project cannot
  drive in CI (runtime/manual — no runner).

## The design state (INJECTED) — treat all of this as literal

Assume Gate 1 cleared. AC2's risk layer is runtime/manual and its only available proof is a unit test →
a layer-match **mismatch**, so AC2 is recorded as a coverage-gap exclusion. Two candidate exclusion
records are on the table; both name the item, tier, why-deferred and follow-up. They differ ONLY in
their `expiry:` value:

```
Exclusion candidate A:
  expiry: PROJ-450   (the ticket that adds a spreadsheet-rendering runner to CI)

Exclusion candidate B:
  expiry: later — once we get around to it
```

Run the mango `design` skill against this state and answer all of the following explicitly:

1. Candidate A: is its `expiry:` checkable by a reader who is not the author? Does the exclusion count as
   recorded, and does the AC2 layer-match close at Gate 2?
2. Candidate B: is its `expiry:` checkable by a non-author? What does the skill do with it — accept it,
   or flag it — and why?
3. State the difference between checking that an `expiry:` is PRESENT and checking that it is CHECKABLE.
4. Emit the `EXCLUSIONS:` counted line for a working doc that recorded candidate A only.

Do not stop for my input; show the artifacts you would produce.
