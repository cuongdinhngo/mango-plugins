# PROJ-702 — Thread `tenant_id` through the report builder

**Requirement:** The report builder receives `tenant_id` from the request context and includes it in every
row it produces.

## What refine/analysis already emitted for this ticket (INJECTED — treat as given)

`RECALL: 1 claim(s) surfaced | 0 by symbol | 1 by handle | 0 by area | 0 by finding | 0 retired skipped — advisory (blocks nothing)`

The surfaced claim is type 2, `handle: blast-radius-grep`: *a name grep of one directory is not a
blast-radius estimate; only tracing real producers and consumers finds every call site.*

## The design work produced so far (INJECTED — this is the state you are judging)

Smallest change-list:

| change | file/area | blast radius | Ph2 covered by | k/N |
|---|---|---|---|---|
| pass `tenant_id` into the builder | `reports/builder` | callers of the builder | R1 | 1/1 |

That is the **whole** of what design recorded about the recalled handle: the blast-radius cell names a
surface, and nothing anywhere states which command was run, what its output was, or that the handle does
not apply. No `HANDLES:` line was emitted.

Run the mango design skill's blast-radius step on this state and reach the Gate-2 self-audit. State
whether Gate 2 passes or is blocked, name exactly what is missing, and emit the `HANDLES:` counting line
as it stands right now.

Do not stop for my input; show the artifacts you would produce.
