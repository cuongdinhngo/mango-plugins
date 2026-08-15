# PROJ-725 — Add a shared `audit_reason` enum used by the writer and the exporter

**Requirement:** Introduce a shared `audit_reason` enum in the audit core module; the writer and the
exporter both consume it.

## Context — the project's recorded claims (INJECTED)

Treat the block below as **the whole content** of `config.lessons_path` (`docs/LESSONS.md`). Note that
CLM-730 carries a `retired:` line and CLM-731 does not.

```
### CLM-730 — a name grep of one directory is not a blast-radius estimate; only tracing real producers and consumers finds every call site
- type: 2 heuristic
- status: confirmed
- evidence: docs/tickets/PROJ-069.work.md — the estimate missed a factory in a test root outside src
- handle: blast-radius-grep
- destination: docs/EVAL_RULES.md
- seen: PROJ-069, PROJ-072
- retired: promoted to §4.2 — the rule for this class has landed

### CLM-731 — a shared type consumed by more than one module needs an assertion per consumer
- type: 2 heuristic
- status: confirmed
- evidence: docs/tickets/PROJ-501.work.md — only the producer had a test
- handle: shared-type-per-consumer
- destination: docs/EVAL_RULES.md
- seen: PROJ-501, PROJ-540
```

Both handles match this change's shape (it introduces a shared vocabulary consumed by two modules).

Run the mango refine phase's advisory recall for this ticket. Emit the counted `RECALL:` line and then
answer all of the following explicitly:

1. Which claims do you surface, and which do you not, and why for each?
2. Which count on the `RECALL:` line reports CLM-730?
3. Is CLM-730 still present in `docs/LESSONS.md` after this run, or was it removed?
4. Is `promoted to §4.2` a recognised retirement reason, and who is allowed to have applied it?

Do not stop for my input; show the artifacts you would produce.
