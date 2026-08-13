# PROJ-710 — Run the cross-ticket promotion pass a second time

**Requirement:** Run `/mango:promote` over the project's recorded claims.

## Context — the project state after an earlier promote run (INJECTED)

`config.lessons_path` is `docs/LESSONS.md` and `config.rulebook_path` is `docs/EVAL_RULES.md`.

**Treat the block below as the entire content of `docs/LESSONS.md`** — unchanged since the last promote
run:

```
### CLM-901 — a name grep of one directory is not a blast-radius estimate; the change altered a shared symbol
- type: 2 heuristic
- status: confirmed
- evidence: docs/tickets/PROJ-069.work.md — a factory in a test root outside src was missed
- handle: blast-radius-grep
- destination: docs/EVAL_RULES.md
- seen: PROJ-069

### CLM-902 — only a producer/consumer trace found the missing call site
- type: 2 heuristic
- status: confirmed
- evidence: docs/tickets/PROJ-072.work.md — the diff exceeded the approved change-list
- handle: blast-radius-grep
- destination: docs/EVAL_RULES.md
- seen: PROJ-072
```

**And treat this as the relevant part of `docs/EVAL_RULES.md`**, written and ratified by the earlier run:

```
## Blast radius

- `blast-radius-grep` (from CLM-901, CLM-902) — when a change touches a shared symbol, a type, or a value
  threaded to a downstream consumer, the blast-radius estimate enumerates the real producers and consumers
  across every test root and records the command run and its output. A name-grep of one directory is not
  an estimate.
```

Run the mango promote skill on this corpus **again**. Emit its counted line and per-class table, give the
verdict for the `blast-radius-grep` class with the evidence you based it on, and state how many **new**
candidate rules this run proposes.

Do not stop for my input; show the artifacts you would produce.
