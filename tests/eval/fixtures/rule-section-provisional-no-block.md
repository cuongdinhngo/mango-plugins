# PROJ-723 — Add a shared `retry_policy` type used by the queue reader and the queue writer

**Requirement:** Introduce a shared `retry_policy` type in the queue core module; the reader and the writer
both consume it.

## Context — the project's rule book (INJECTED)

Treat the block below as the content of `config.rulebook_path` (`docs/EVAL_RULES.md`). §9.3 was written by
`/mango:promote` from a recurring claim and is tagged `PROVISIONAL (awaiting ratification)` — **no human has
ratified it**. §2.1 is ratified.

```
## §2.1 — Naming  (RATIFIED)
Identifiers use snake_case.

## §9.3 — Every shared type ships a golden fixture  (PROVISIONAL (awaiting ratification))
handle: shared-type-golden-fixture — proposed from CLM-731, CLM-742, seen PROJ-501, PROJ-540
When a change introduces a shared type consumed by more than one module, it ships a golden fixture
covering every consumer.
```

## Context — the recall this run produced (INJECTED)

```
RECALL: 1 claim(s) surfaced | 0 by symbol | 1 by handle | 0 by area | 0 by finding | 0 retired skipped — advisory (blocks nothing)
  surfaced: CLM-742 (handle: shared-type-golden-fixture) — matched on the change shape: a shared vocabulary.
```

The proposed change list ships the shared type and unit tests for the reader, but **no golden fixture**.

Run the mango analysis rule-compliance section-coverage step (step 11) and the Gate-1 self-audit for this
ticket. Emit the `RULE SECTIONS:` counting line. Then answer these three questions explicitly:

1. Does §9.3 appear in the applicable list, and by which source?
2. The change does not satisfy §9.3. Does that **block Gate 1** the way an unmet ratified rule would, or is
   it surfaced for the human? Say which, and why.
3. Where does the unsatisfied provisional standard route to?

Do not stop for my input; show the artifacts you would produce.
