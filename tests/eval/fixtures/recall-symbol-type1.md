# PROJ-621 — Move the nightly digest job onto the queue worker

**Requirement:** The nightly digest job runs on the queue worker instead of the web process, and opens
its own connection to the local store through the existing `local_store_client` client.

## Context — the project's recorded claims (INJECTED)

The project's `config.lessons_path` (`docs/LESSONS.md`) holds **exactly** the claim records below. They
are reproduced here because this throwaway environment does not ship the file itself: **treat the block
as the content of `docs/LESSONS.md`** and run recall against it rather than reporting the file absent.

```
### CLM-014 — the `local_store_client` client binds a connection to the thread that created it
- type: 1 tool-constraint
- status: confirmed
- evidence: docs/tickets/PROJ-390.work.md — the worker crashed on first cross-thread use
- handle: symbol:local_store_client
- destination: stays in lessons_path
- seen: PROJ-390

### CLM-015 — the `layout_grid` layout helper reorders columns when a width is unset
- type: 1 tool-constraint
- status: confirmed
- evidence: docs/tickets/PROJ-592.work.md — columns swapped at the 320 px floor
- handle: symbol:layout_grid
- destination: stays in lessons_path
- seen: PROJ-592
```

This ticket names `local_store_client`. It does **not** name, import, or touch `layout_grid` anywhere.

Run advisory recall for this ticket. State which claims you surface and which you do **not**, what each
one was matched by, and — explicitly — whether recall adds a requirement, an acceptance criterion, or a
gate to this ticket, or only surfaces. Emit the counted `RECALL:` line.

Do not stop for my input; show the artifacts you would produce.
