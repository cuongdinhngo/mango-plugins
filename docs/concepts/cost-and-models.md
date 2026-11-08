# Cost and models

> **In 30 seconds.** Which model does which step, how the full and lite tiers differ in weight, how
> mango records its own token cost, and how to adopt a token optimizer without losing a check.
> **Status:** Implemented in 1.21.0; measured runs are in [`docs/COST.md`](../COST.md).

## Tier weight

The full tier is heavier — rule-book reads, requirement re-derivation, the challenger, and (when
`explore_fanout` is `true`) read-only `explorer` fan-out. For small, low-stakes, high-volume tickets use
the **lite** tier (`/mango:quick`), which skips fan-out and the challenger. Set `explore_fanout: false`
to disable investigation fan-out on the full tier too.

## Model delegation

mango routes by the **nature of the task**, not the phase: *Opus decides, Sonnet executes, Haiku
gathers — every decision or verdict is produced or ratified by the strong model; a weaker model may
only gather, never conclude.*

| Step | Model |
|------|-------|
| Orchestrator + gates, analysis judgment, design | Opus (the model you drive) |
| Review verdict + challenger reconstruction | Sonnet — `reviewer-max` (Opus) for high-stakes diffs under `cost_tier: max` — **never Haiku** |
| Implement the approved change list (`implementer`); draft PR body | Sonnet — high-stakes change → the main loop |
| Explore: handler, callers, blast radius (`explorer`) | Sonnet |
| Bulk read-and-extract across many files (`extractor`) | Haiku |
| grep stray refs / run tests / lint | no model — Bash directly |

`cost_tier` shifts the dials within this map: `economy` pushes more bulk retrieval to Haiku and avoids
Opus on review; `standard` is the map above; `max` dispatches `reviewer-max` (Opus) for high-stakes
diffs (security-tagged, touching auth / data access / schema migration, or touching
`high_stakes_paths`). The two Sonnet rows are pinned by **choice of agent** (`implementer`, `explorer`),
the same mechanism `review` uses for `reviewer` vs `reviewer-max`, so they hold even when the main loop
runs on Opus. The full routing map lives in [`PRINCIPLES.md`](../../plugins/mango/PRINCIPLES.md).

## Token ledger — measure before you optimize

mango records its own token cost as a **descriptive Cost ledger** in the working doc — one row per
subagent-dispatch return, transcribed from that return's usage block as a by-product of dispatching
(N dispatches → N rows). A dispatch retrieved by blocking carries no `<usage>` block, so mango first
tries to recover the usage; if it truly cannot, the cell is marked the explicit
`unmeasured (blocking retrieval)` — never a silent blank, never an invented number. `finalise` runs a
**completeness gate** that refuses to proceed unless every row is present and every token cell carries
a value or the marker. The gate checks *presence* only — it never inspects, ranks, or auto-cuts. The
ledger is dispatch-scoped: main-loop output noise (lint/test/build dumps, file reads) is not measured.

To keep the response cheap, mango emits **deltas, not full artifacts**: on a partial update it prints
only the changed row/cell ("ledger **unchanged except** row N"), while the full artifact stays **complete
on disk** in the working doc (the single source of truth the completeness gate reads). Emitting less into
the response never means storing less on disk.

`/mango:budget` (opt-in) lets a human adopt an external token optimizer with the trade-offs explicit.
**The safety axis:** an optimizer is safe only if it removes **representation redundancy** (how output
is phrased), never a check, a gate, a critic, or the **evidence detail** a critic relies on
(`path:line`, measured values, diffs).

- **RTK** — compresses Bash-command output before it enters context. Safe. The default `rtk: "expect"`
  means mango tolerates RTK's compact output but never installs or depends on it — RTK absent, the run
  is identical (only the saving is lost). When present but unwired, `budget` prints the wiring command
  for you to run; it never runs it.
- **Headroom** — input compression is safe, but its `OUTPUT_SHAPER` changes what the model writes → it
  must stay OFF (`headroom.output_shaper: false`, enforced).
- **Caveman** — terse agent output, never applied to critic output (`caveman.scope: "non-critic-only"`,
  enforced), which must retain full evidence detail.

Adopting any optimizer is a recorded, provisional decision (ratified like `codify`), never a silent
toggle. `budget` detects and informs, never self-administers.
