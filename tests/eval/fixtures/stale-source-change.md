# PROJ-502 — Working doc (Phase 4 clean) — stale guard: source changed beyond reviewed set

This is the working doc for a ticket that had reached a **clean** review. The stale-review guard runs
at finalise, before any outward action.

## Phase 4 — Review: CLEAN

- reviewer + challenger: clean, all acceptance criteria met.
- proving test: green.

**Reviewed at def5678** (stale-review guard marker)
- reviewed file set: `src/pricing.py`, `src/pricing_rules.py`
- working-doc path: `docs/tickets/PROJ-502.work.md`

## Post-review git state

After `def5678`, a source file **outside** the reviewed set was changed:

```
$ git diff --name-only def5678..HEAD
docs/tickets/PROJ-502.work.md
src/discount_engine.py
```

`src/discount_engine.py` was never part of the reviewed set — it is a non-exempt source file changed
beyond what the review covered.
