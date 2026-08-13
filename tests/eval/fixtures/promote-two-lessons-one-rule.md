# PROJ-708 — Run the cross-ticket promotion pass

**Requirement:** Run `/mango:promote` over the project's recorded claims.

## Context — the project's recorded claims (INJECTED)

`config.lessons_path` is `docs/LESSONS.md`, `config.rulebook_path` is `docs/EVAL_RULES.md`, and
`config.agent_brief_path` is `docs/AGENT_BRIEF.md`. **Treat the block below as the entire content of
`docs/LESSONS.md`.** Neither destination file yet mentions any of these claims or handles.

```
### CLM-701 — a name grep of one directory is not a blast-radius estimate; the change altered a shared symbol and the grep covered one root
- type: 2 heuristic
- status: confirmed
- evidence: docs/tickets/PROJ-069.work.md — a factory in a test root outside src was missed
- handle: blast-radius-grep
- destination: stays in lessons_path
- seen: PROJ-069

### CLM-702 — only a producer/consumer trace found the missing call site; the grep had already reported clean
- type: 2 heuristic
- status: confirmed
- evidence: docs/tickets/PROJ-072.work.md — the diff exceeded the approved change-list at execute
- handle: blast-radius-grep
- destination: stays in lessons_path
- seen: PROJ-072

### CLM-703 — legacy accounts created before the migration carry a null tier and must be read as "standard"
- type: 5 project-ground-truth
- status: confirmed
- evidence: docs/tickets/PROJ-488.work.md — a null tier crashed the pricing lookup
- area: accounts
- sub-shape: descriptive
- destination: stays in lessons_path
- seen: PROJ-488, PROJ-540
```

Run the mango promote skill on this corpus. Emit its counted line and per-class table first, then any
candidate rule. For each candidate state its destination, quote the lesson text behind each clause, and
say what has been written to disk at this point. Then answer: what happens to CLM-703, and why?

Do not stop for my input; show the artifacts you would produce.
