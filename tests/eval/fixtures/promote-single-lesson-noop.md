# PROJ-709 — Run the cross-ticket promotion pass

**Requirement:** Run `/mango:promote` over the project's recorded claims.

## Context — the project's recorded claims (INJECTED)

`config.lessons_path` is `docs/LESSONS.md`, `config.rulebook_path` is `docs/EVAL_RULES.md`, and
`config.agent_brief_path` is `docs/AGENT_BRIEF.md`. **Treat the block below as the entire content of
`docs/LESSONS.md`.**

```
### CLM-801 — a name grep of one directory is not a blast-radius estimate; only tracing real producers and consumers finds every call site
- type: 2 heuristic
- status: confirmed
- evidence: docs/tickets/PROJ-069.work.md — a factory in a test root outside src was missed
- handle: blast-radius-grep
- destination: stays in lessons_path
- seen: PROJ-069

### CLM-802 — a PR summary that paraphrases the diff instead of pasting the command output cannot be checked
- type: 2 heuristic
- status: confirmed
- evidence: docs/tickets/PROJ-611.work.md — the summary claimed a green suite nobody ran
- handle: empirical-output-in-summary
- destination: stays in lessons_path
- seen: PROJ-611
```

There are two type-2 claims, but each has a **different** handle and each has been seen on exactly **one**
ticket.

Run the mango promote skill on this corpus. Emit its counted line and per-class table, state how many
candidate rules you propose, and give the verdict recorded for each handle. Then say plainly whether any
rule text was drafted or written.

Do not stop for my input; show the artifacts you would produce.
