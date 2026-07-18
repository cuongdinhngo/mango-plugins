# PROJ-823 — Thread a `locale` value into the summary builder

**Requirement:** Thread a new `locale` value into the `summaryBuilder` so the generated summary text is
localised.

**Goal:** The design change-list must enumerate every place the `locale` value originates — every
`summaryBuilder` call site — not just the surface that owns the feature.

**Acceptance Criteria:**
- Every call site that invokes `summaryBuilder` supplies the `locale` value.

## Existing call sites (blast radius)

`summaryBuilder` is called from **multiple sites**, not only the feature's owning page:

- `src/report/reportPage.ts` (the owning surface)
- `src/digest/emailDigest.ts`
- `src/notify/pushSummary.ts`

Tracing only the **owning page** (`reportPage`) — the shallow approach — would **miss** the
`emailDigest` and `pushSummary` call sites where the threaded `locale` value also originates,
under-scoping the change so the diff exceeds the approved change-list at execute.

Per mango's design blast-radius step, a **VALUE threaded to a downstream consumer** requires
enumerating **every builder call site** of the relevant builder/producer — all `summaryBuilder` call
sites — not just the surface/page that owns the feature. A shallow estimate that misses a known
consumer/call site is a **finding**.
