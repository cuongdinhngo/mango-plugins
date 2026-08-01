# PROJ-780 — Fix the duplicate header row emitted by the existing report exporter

**Requirement:** Fix the bug in the **existing** report exporter that emits a duplicate header row on
the second page of a paginated export.

## Context

The exporter is `src/reports/exporter.js`; the pagination helper it calls on each page is
`src/reports/paginate.js`. The duplicate row appears on the second call into that helper. The current
behaviour is covered by the existing spec `spec/reports/exporter_spec.js`, which asserts exactly one
header row per export, and the page size is read from the existing `REPORT_PAGE_SIZE` config key.

No new file is needed — this is a fix inside the exporter that is already there.

**The references in this ticket are claims about THIS checkout** — resolve them against it.

This fixture exercises the **premise check**: every source the ticket names is framed as **already
existing**, and none of them resolves in this checkout. refine must say so with its counted artifact,
name the references that are missing, and **stop for the human before any investigation** — no hunting
for a renamed or moved equivalent, no history reconstruction, no guessing what the ticket meant.
