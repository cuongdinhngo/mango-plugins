# PROJ-624 — Widen the retry window on the outbound webhook sender

**Requirement:** The outbound webhook sender retries over a wider window, using the existing `outbound_client`
client.

## Context — the project's recorded claims (INJECTED)

The project's `config.lessons_path` (`docs/LESSONS.md`) holds **exactly** the claim records below. They
are reproduced here because this throwaway environment does not ship the file itself: **treat the block
as the content of `docs/LESSONS.md`** and run recall against it rather than reporting the file absent.

```
### CLM-041 — the `outbound_client` client caps a retry backoff at two seconds and ignores a larger value
- type: 1 tool-constraint
- status: confirmed
- evidence: docs/tickets/PROJ-288.work.md — a 30 s backoff behaved as 2 s
- handle: symbol:outbound_client
- destination: stays in lessons_path
- seen: PROJ-288
- retired: the cap was configurable all along and the earlier reading was wrong — superseded by CLM-042
  (human-retired at PROJ-471)

### CLM-042 — the `outbound_client` client reads its retry cap from the client options, with a two-second default
- type: 1 tool-constraint
- status: confirmed
- evidence: docs/tickets/PROJ-471.work.md — the option was set and a 30 s backoff was observed
- handle: symbol:outbound_client
- supersedes: CLM-041
- destination: stays in lessons_path
- seen: PROJ-471
```

Both claims carry the **same** symbol handle, `outbound_client`, which this ticket uses. One of them is
`retired:`.

Run advisory recall. State which claims you surface and which you skip, and why. Then state whether the
retired record was deleted from the file, and whether anything auto-retired a claim in this run. Emit the
counted `RECALL:` line including its retired-skipped count.

Do not stop for my input; show the artifacts you would produce.
