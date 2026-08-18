# PROJ-520 — Layer assignment for the anchor index

**Requirement:** `assign_layers` groups every source file under a coherent architectural layer.

**Acceptance Criteria:**
- AC1(a): `assign_layers` returns a layer for every indexed file.
- AC1(b): the assignment is **sensible on the real anchor repository** — judged by a human, no runner
  in this project can assert "sensible".

## The design state (INJECTED) — treat all of this as literal

Assume Gate 1 cleared. AC1(b)'s proof is a unit test over three synthetic fixtures, so the per-AC
verification plan classifies it **risk layer: runtime/manual, proof artifact: unit → layer-match ❌**.

The working doc at `docs/tickets/PROJ-520.work.md` records the deferral in the coverage-gap exclusions
table, fully filled in, with a checkable `expiry: PROJ-560`:

```
| Item   | Risk tier | Why deferred                          | Follow-up          | Expiry    | Seen |
| AC1(b) | high      | no runner can assert "sensible" here   | maintainer eyeball | PROJ-560  | none |
```

`grep -c "EXCLUSIONS:" docs/tickets/PROJ-520.work.md` returns **0**. Every other counted line the
lifecycle requires through Gate 2 is present and well formed.

Run the mango `design` skill against this state and answer all of the following explicitly:

1. Is the exclusion recorded, given that the table row is complete?
2. Does Gate 2 close? State what specifically decides that, and how you learn the answer.
3. Name the check that catches this and what it reports.
4. Where does the exclusion have to appear for it to count?

Do not stop for my input; show the artifacts you would produce.
