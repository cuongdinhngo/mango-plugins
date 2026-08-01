# PROJ-622 — Add a second tier to the loyalty points calculation

**Requirement:** The loyalty points calculation gains a second tier above the existing threshold.

## Context — the project's recorded claims (INJECTED)

The project's `config.lessons_path` (`docs/LESSONS.md`) holds **exactly** the claim records below. They
are reproduced here because this throwaway environment does not ship the file itself: **treat the block
as the content of `docs/LESSONS.md`** and run recall against it rather than reporting the file absent.

```
### CLM-021 — loyalty tier boundaries are inclusive at the LOWER bound only, everywhere in this domain
- type: 5 project-ground-truth
- status: confirmed
- sub-shape: normative
- evidence: docs/DESIGN.md — the tier table; three call sites agree
- area: loyalty points
- destination: rulebook_path (ID + blocking)
- seen: PROJ-410

### CLM-022 — the headless browser used for the export snapshots is installed at a fixed path here
- type: 5 project-ground-truth
- status: confirmed
- sub-shape: environment
- evidence: tooling notes for the export pipeline
- area: report export
- verified-at: 2026-02-11
- destination: design_doc_path
- seen: PROJ-433

### CLM-023 — the `band_total` helper truncates rather than rounds a fractional total
- type: 1 tool-constraint
- status: confirmed
- evidence: docs/tickets/PROJ-418.work.md
- handle: symbol:band_total
- destination: stays in lessons_path
- seen: PROJ-418
```

This ticket is in the **loyalty points** area. It names no symbol at all — no `band_total`, no import, no
API. It is not about report export.

Run advisory recall. State which claims you surface, **what each was matched by**, and which you do not
surface and why. Say explicitly what recall does to this ticket's requirements and gates. Emit the
counted `RECALL:` line.

Do not stop for my input; show the artifacts you would produce.
