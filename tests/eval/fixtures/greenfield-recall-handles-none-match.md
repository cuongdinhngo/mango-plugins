# PROJ-729 — Raise the export command's log level from debug to info

**Requirement:** One line in the export command changes the log level of an existing message from debug to
info. No shared vocabulary, no new core module, no value threaded through callers.

## Context — the project's recorded claims (INJECTED)

Treat the block below as the content of `config.lessons_path` (`docs/LESSONS.md`). Both claims are type 2
and **both carry a handle** — but neither handle's change shape is present in this ticket.

```
### CLM-750 — a name grep of one directory is not a blast-radius estimate; only tracing real producers and consumers finds every call site
- type: 2 heuristic
- status: confirmed
- evidence: docs/tickets/PROJ-069.work.md — the estimate missed a factory outside src
- handle: blast-radius-grep
- destination: docs/EVAL_RULES.md
- seen: PROJ-069, PROJ-072

### CLM-751 — a shared type consumed by more than one module needs an assertion per consumer
- type: 2 heuristic
- status: confirmed
- evidence: docs/tickets/PROJ-501.work.md — only the producer had a test
- handle: shared-type-per-consumer
- destination: docs/EVAL_RULES.md
- seen: PROJ-501, PROJ-540
```

## Context — the project's rule book (INJECTED)

Treat the block below as the content of `config.rulebook_path` (`docs/EVAL_RULES.md`). **Both** handles
above have already been promoted into ratified sections that carry them.

```
## §2.1 — Naming  (RATIFIED)
Identifiers use snake_case.

## §4.2 — Blast-radius estimates must trace producers and consumers  (RATIFIED)
handle: blast-radius-grep — promoted from CLM-750, seen PROJ-069, PROJ-072

## §7.3 — A shared type needs an assertion per consumer  (RATIFIED)
handle: shared-type-per-consumer — promoted from CLM-751, seen PROJ-501, PROJ-540
```

Run the mango analysis phase's advisory recall and its rule-compliance section-coverage step (step 11) for
this ticket. Emit the counted `RECALL:` line and the counted `RULE SECTIONS:` line, then answer all of the
following explicitly:

1. How many claims are surfaced by handle, and why?
2. How many sections does the handle-matched source add to the applicable list?
3. Are §4.2 and §7.3 applicable to this ticket? Say which source would have had to make them so.
4. Does this ticket carry any extra trace, row, question or gate because two ratified, handle-carrying
   sections exist in the rule book?

Do not stop for my input; show the artifacts you would produce.
