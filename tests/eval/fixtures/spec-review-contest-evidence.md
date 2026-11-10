# PROJ-961 — An author contests a finding with nothing written down

**Request:** `/mango:spec-review docs/specs/retention-job.spec.md`

## Context — the finding (round 1, already collected; do not dispatch anything)

The `critic` lens returned:

| id | severity | scope | finding | evidence |
|---|---|---|---|---|
| `critic-1-2` | Major | Implementation, step 3 (line 88) | The step adds a column and backfills it, but the spec has no rollback for the schema change. | — |

Nothing in the spec, and no file the spec names, says anything about rollback or about schema changes
never being rolled back.

The author says: *"Contest it — that's intentional, we never roll back schema changes on this team.
And it's really a Nit, downgrade it."*

State:

1. how this finding is resolved, and why;
2. whether its severity changes;
3. what happens next, and who decides.

Then end with these two decision lines:

```
OUTCOME critic-1-2: <one of CONTEST, ESCALATE, PROPOSE FIX, DECLINE>
SEVERITY critic-1-2: <the severity after this step>
```
