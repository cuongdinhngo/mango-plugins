# PROJ-703 — Fix an off-by-one in the retry backoff calculation

**Requirement:** The third retry waits 8 s, not 4 s. The fix is one arithmetic expression inside
`retry/backoff`.

## What refine/analysis already emitted for this ticket (INJECTED — treat as given)

`RECALL: 1 claim(s) surfaced | 0 by symbol | 1 by handle | 0 by area | 0 by finding | 0 retired skipped — advisory (blocks nothing)`

The surfaced claim is type 2, `handle: blast-radius-grep`: *a name grep of one directory is not a
blast-radius estimate; only tracing real producers and consumers finds every call site.*

## The design work produced so far (INJECTED — this is the state you are judging)

Smallest change-list:

| change | file/area | blast radius | Ph2 covered by | k/N |
|---|---|---|---|---|
| correct the exponent in the backoff expression | `retry/backoff` | none identified | R1 | 1/1 |

Design's answer to the recalled handle, recorded verbatim:

> `blast-radius-grep` — **does not apply because** this change alters one arithmetic expression inside a
> single private function. It introduces no shared symbol, no new core module, and threads no value to a
> downstream consumer, so there is no producer/consumer set to trace.

Run the mango design skill's blast-radius step on this state and reach the Gate-2 self-audit. State
whether Gate 2 passes or is blocked, say explicitly whether that recorded answer is a **legal** answer to
the recalled handle, and emit the `HANDLES:` counting line.

Do not stop for my input; show the artifacts you would produce.
