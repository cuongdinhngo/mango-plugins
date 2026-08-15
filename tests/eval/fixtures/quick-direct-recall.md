# PROJ-724 — Correct the rounding of the summary total in the ledger formatter

**Requirement:** The ledger formatter rounds the summary total down; it must round half-up. One file, one
line, one requirement row. Not security-tagged.

This ticket is being started by a **direct `/mango:quick PROJ-724`** — the operator typed the lite lane
skill itself. `refine` and `analysis` have **not** run for it, so nothing has been carried forward.

## Context — the project's recorded claims (INJECTED)

Treat the block below as the content of `config.lessons_path` (`docs/LESSONS.md`).

```
### CLM-724 — a rounding change is a value threaded to every consumer of the formatted total; each consumer needs its own assertion
- type: 2 heuristic
- status: confirmed
- evidence: docs/tickets/PROJ-410.work.md — the export path kept the old rounding for two releases
- handle: value-threading-callers
- destination: docs/EVAL_RULES.md
- seen: PROJ-410, PROJ-455
```

## Context — the project's rule book (INJECTED)

Treat the block below as the content of `config.rulebook_path` (`docs/EVAL_RULES.md`).

```
## §2.1 — Naming  (RATIFIED)
Identifiers use snake_case.

## §6.4 — A threaded value is proven at every consumer  (RATIFIED)
handle: value-threading-callers — promoted from CLM-724, seen PROJ-410, PROJ-455
Every consumer that reads a changed computed value is enumerated, and each has an assertion that it
received the new value — not only the producer.
```

Run the mango `quick` skill on this ticket, up to and including its pre-code gate artifacts. Answer all of
the following explicitly:

1. Which counted lines does the lite lane emit before the working doc, and what are they?
2. Which claims does recall surface, and what was each matched by?
3. Which rule-book sections are applicable, by which source, and how is each answered?
4. Does this direct invocation read the lesson corpus, or only write to it at finalise?
5. Does the lane run a challenger, a full requirements matrix, an Explore fan-out, or a baseline capture?

Do not stop for my input; show the artifacts you would produce.
