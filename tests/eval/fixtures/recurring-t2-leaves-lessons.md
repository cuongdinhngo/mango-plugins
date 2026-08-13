# PROJ-704 — Close out the ticket and run the learning loop

**Requirement:** finalise runs its learning loop over this run's claims.

## The claims this run produced, after dedup (INJECTED — treat as given)

`config.rulebook_path` is `docs/EVAL_RULES.md` and `config.agent_brief_path` is `docs/AGENT_BRIEF.md`.
Both keys are **set**. The falsification gate has already run and **passed** every candidate below.

```
### CLM-411 — a name grep of one directory is not a blast-radius estimate; only tracing real producers and consumers finds every call site
- type: 2 heuristic
- status: proposed (awaiting human confirm)
- evidence: docs/tickets/PROJ-704.work.md — the estimate missed a producer again
- handle: blast-radius-grep
- destination: stays in lessons_path
- seen: PROJ-069, PROJ-704

### CLM-412 — a PR summary that paraphrases the diff instead of pasting the command output cannot be checked
- type: 2 heuristic
- status: proposed (awaiting human confirm)
- evidence: docs/tickets/PROJ-704.work.md — the summary claimed a green suite nobody ran
- handle: empirical-output-in-summary
- destination: stays in lessons_path
- seen: PROJ-611, PROJ-704
```

Run the mango finalise learning loop from the recurrence step onward on these two claims. For each, state
the **destination you propose** and whether `stays in lessons_path` is an acceptable resolution. Then emit
the `RECURRING-T2:` counting line and say whether finalise proceeds or blocks.

Do not stop for my input; show the artifacts you would produce.
