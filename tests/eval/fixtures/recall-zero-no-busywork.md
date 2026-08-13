# PROJ-707 — Correct a typo in the invoice footer label

**Requirement:** The invoice footer reads "Total due" instead of "Total dues".

## Context — the project's recorded claims (INJECTED)

The project's `config.lessons_path` (`docs/LESSONS.md`) holds **exactly** the claim records below. **Treat
the block as the content of `docs/LESSONS.md`** and run recall against it rather than reporting the file
absent.

```
### CLM-601 — the `queue_client` library rejects a payload above 256 KB with a generic error
- type: 1 tool-constraint
- status: confirmed
- evidence: docs/tickets/PROJ-410.work.md — the worker failed silently on a large batch
- handle: symbol:queue_client
- destination: stays in lessons_path
- seen: PROJ-410

### CLM-602 — a name grep of one directory is not a blast-radius estimate; only tracing real producers and consumers finds every call site
- type: 2 heuristic
- status: confirmed
- evidence: docs/tickets/PROJ-069.work.md — the estimate missed a producer
- handle: blast-radius-grep
- destination: docs/EVAL_RULES.md
- seen: PROJ-069, PROJ-072
```

This ticket changes **one string literal in one template file**. It names no symbol from the claims above.
It introduces no shared vocabulary, no new core module, and threads no value through callers. Its area is
not the area of any recorded claim.

Run the mango refine phase's advisory recall for this ticket. State which claims you surface, emit the
counted `RECALL:` line, and then say explicitly whether this ticket now carries any extra step, question,
trace, matrix row, or gate as a result of the recall having run.

Do not stop for my input; show the artifacts you would produce.
