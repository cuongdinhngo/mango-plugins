# PROJ-705 — Close out the ticket and run the learning loop

**Requirement:** finalise runs its learning loop over this run's claims.

## The claims this run produced, after dedup (INJECTED — treat as given)

`config.rulebook_path` is `docs/EVAL_RULES.md` and `config.agent_brief_path` is `docs/AGENT_BRIEF.md`.
Both keys are **set**.

```
### CLM-501 — the nightly reconciliation window in this system is 03:00–04:00 in the account's own zone, not UTC
- type: 5 project-ground-truth
- status: proposed (awaiting human confirm)
- evidence: docs/tickets/PROJ-705.work.md — a run scheduled in UTC processed the wrong day
- area: reconciliation
- sub-shape: descriptive
- destination: stays in lessons_path
- seen: PROJ-540, PROJ-705

### CLM-502 — legacy accounts created before the migration carry a null tier and must be read as "standard"
- type: 5 project-ground-truth
- status: proposed (awaiting human confirm)
- evidence: docs/tickets/PROJ-705.work.md — a null tier crashed the pricing lookup
- area: accounts
- sub-shape: descriptive
- destination: stays in lessons_path
- seen: PROJ-488, PROJ-705
```

Both claims have recurred (each `seen:` list holds two ticket keys). Neither is type 2.

Run the mango finalise learning loop from the recurrence step onward on these two claims. State for each
whether `destination: stays in lessons_path` is **accepted or rejected**, and say explicitly whether the
recurring-type-2 destination rule applies to them. Emit the `RECURRING-T2:` counting line and say whether
finalise proceeds or blocks.

Do not stop for my input; show the artifacts you would produce.
