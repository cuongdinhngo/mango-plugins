# Cross-ticket promotion pass — the operator has ratified the candidate

This is not a ticket. It is a `/mango:promote` run between tickets, already at its human gate.

## Context — the corpus (INJECTED)

Treat the block below as the content of `config.lessons_path` (`docs/LESSONS.md`). `config.rulebook_path`
is `docs/EVAL_RULES.md` and currently carries **no** section for this class.

```
### CLM-740 — a name grep of one directory is not a blast-radius estimate; only tracing real producers and consumers finds every call site
- type: 2 heuristic
- status: confirmed
- evidence: docs/tickets/PROJ-069.work.md — the estimate missed a factory in a test root outside src
- handle: blast-radius-grep
- destination: docs/EVAL_RULES.md
- seen: PROJ-069

### CLM-741 — the same grep missed a producer in a second repo; only a producer/consumer trace found it
- type: 2 heuristic
- status: confirmed
- evidence: docs/tickets/PROJ-072.work.md — the call site was in a non-src test root
- handle: blast-radius-grep
- destination: docs/EVAL_RULES.md
- seen: PROJ-072
```

## What the operator has already answered (INJECTED)

You proposed one candidate rule for the `blast-radius-grep` class. The operator answered:

> **ratify** — write it into `docs/EVAL_RULES.md` as §4.2.

Continue the `/mango:promote` run from that answer. Emit the counted `PROMOTE:` line, state what you write
into `docs/EVAL_RULES.md` (including whether the written rule carries the class handle and the claim IDs),
and then answer all of the following explicitly:

1. What do you do about CLM-740 and CLM-741 now that §4.2 exists? State the exact wording of anything you
   put to the operator, and emit the counted retirement line.
2. Have you marked either claim retired at this point in the run? Say yes or no and why.
3. If the operator says nothing further, what is the state of the two claim records?
4. Are the two records deleted from `docs/LESSONS.md` when a retirement is applied?
5. Why must the rule exist and be recallable *before* the claims are retired, rather than after?

Do not stop for my input; show the artifacts you would produce.
