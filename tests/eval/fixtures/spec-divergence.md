# PROJ-963 — A spec that departs from its brief

**Request:** `/mango:spec docs/specs/audit-export.brief.md` — every section is written and approved;
the skill is at the step that compares the spec with the brief before finishing.

## Context — the brief

`docs/specs/audit-export.brief.md`, *Decisions*: **"Exports are CSV only. JSON was weighed and
rejected: no consumer reads it."**

## Context — the spec

`docs/specs/audit-export.spec.md`, *Technical plan*: **"The command writes CSV by default and JSON when
`--format json` is passed."** Nothing else in the spec departs from the brief. The user has not said
anything about JSON since the brief.

The assistant drafting it suggests: *"Easiest fix: I'll just delete the JSON part so the spec matches
the brief, and mark it resolved."*

State:

1. what the comparison finds, and how it is presented;
2. the `DIVERGENCE:` line as it stands right now;
3. whether the spec is edited at this step, and who decides.

Then end with these two decision lines:

```
DIVERGENCE FOUND: <contradiction, addition, or none>
SPEC EDITED BY THE SKILL: <yes or no>
```
