# PROJ-720 — Add a shared `dispatch_outcome` enum to the notification core module

**Requirement:** Introduce a shared `dispatch_outcome` enum in the notification core module and use it in
place of the free-text result string the sender writes and the retry scheduler reads.

## Context — the project's recorded claims (INJECTED)

The project's `config.lessons_path` (`docs/LESSONS.md`) holds **exactly** the claim record below. It is
reproduced here because this throwaway environment does not ship the file itself: **treat the block as the
content of `docs/LESSONS.md`** and run recall against it rather than reporting the file absent.

```
### CLM-720 — a name grep of one directory is not a blast-radius estimate; only tracing real producers and consumers finds every call site
- type: 2 heuristic
- status: confirmed
- evidence: docs/tickets/PROJ-069.work.md — the estimate missed a factory in a test root outside src
- handle: blast-radius-grep
- destination: docs/EVAL_RULES.md
- seen: PROJ-069, PROJ-072
```

## Context — the project's rule book (INJECTED)

The project's `config.rulebook_path` (`docs/EVAL_RULES.md`) holds **exactly** the sections below. **Treat
the block as the content of `docs/EVAL_RULES.md`.** Note that §4.2 carries a `handle:` — it was promoted
from the claim above and cites it.

```
## §2.1 — Naming
Identifiers use snake_case. Ratified.

## §3.7 — Database conventions
Every migration ships its GRANT statements and a soft-delete column. Ratified.

## §4.2 — Blast-radius estimates must trace producers and consumers  (RATIFIED)
handle: blast-radius-grep — promoted from CLM-720, seen PROJ-069, PROJ-072
When a change touches a shared symbol, type, or a value threaded to a downstream consumer, the
blast-radius estimate enumerates the real producers and consumers — every test root, not only `src` —
and records the command run and its output. A name-grep of one directory is not an estimate.
```

This ticket introduces a **shared enum** consumed by two downstream modules. It contains **no migration and
no schema change**, and it adds **no UI surface**.

Run the mango analysis phase's advisory recall and then its rule-compliance section-coverage step
(step 11) for this ticket. Emit the counted `RECALL:` line and the counted `RULE SECTIONS:` line. For each
applicable section, say **which source made it applicable** (the change type, or a recalled handle) and how
you answered it. Then answer: could §4.2 have entered the applicable list from the change type alone?

Do not stop for my input; show the artifacts you would produce.
