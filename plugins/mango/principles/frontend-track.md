## Frontend track — own the durable, compose the volatile

> **mango embeds only UI knowledge that is durable + falsifiable; it composes, never owns, the
> aesthetic-generation layer — and never stops because a taste skill is missing.**

Active only when `config.track` includes frontend (default `backend` — unchanged behaviour). `track`
is **orthogonal to TIER**: TIER is process weight, track is which gate set applies.

- **Falsifiable-only rubric.** Every frontend rubric item is **measurable or greppable** and scored
  **against the project's `DESIGN.md`** (`config.design_doc_path`). Any "is it tasteful?" judgment is
  **out of the rubric** — taste exists only as `DESIGN.md` conformance. A blanket rule (e.g. "ban
  colour X") **yields to domain meaning** recorded in `DESIGN.md` — a domain term may literally denote
  that colour, so the reviewer checks the contract, not a blanket rule.
- **Compose, never own, the aesthetic.** mango embeds only durable, measurable knowledge (a11y
  thresholds, token-first, `DESIGN.md` conformance). The aesthetic-*generation* layer is **composed**:
  call an external taste skill if installed, else follow `DESIGN.md`. **Never stop because a taste
  skill is missing** — mango blocks on a missing **number**, never on a missing aesthetic. Breakpoint
  values, the narrow-width navigation pattern, and which regions collapse vs reflow are **choices** →
  they live in `DESIGN.md`, never gated by mango.
- **Risk-layer floor (so the layer-match gate cannot be diluted).** Frontend ACs ride the **same**
  layer-match hard gate as Principle 4 — not a fork. `document`, `computed-style`,
  `integration/runtime`, and `behavioral` are **all above the logic/unit layer**: a unit-only proof
  (a mocked DOM) clears **none** of the M1–M10 gates; `computed-style` requires a **real resolved
  DOM**. A proof below an AC's risk layer is a layer-match `❌` and **blocks Gate 2** unless upgraded
  or recorded as a human-approved coverage-gap exclusion.
- **Surface coverage — the denominator comes from the CODE, not the ticket.** A universal / app-wide
  frontend requirement (no horizontal scroll, reflow, focus-visible, contrast — anything page-wide)
  has its denominator **N = |reachable surfaces|** enumerated from the code surface (the opt-in
  `sitemap`, else a read-only "enumerate reachable views" sub-step). The ticket's examples are a
  **hint, never the denominator** — counting only the surfaces the ticket named is the exact failure
  this removes. `analysis` emits `SURFACES: N` (counted, challenger-checkable); the gate passes iff
  `N == M + X` (`M` = surfaces with a valid proof at any tier, `X` = recorded exclusions), with a loud
  `surfaces proven: k/N` banner whenever `M + X < N`.
- **Elastic proof tier — e2e is optional, a proof is not.** Per affected surface, `execute` produces
  the **highest available tier**: `PASS(automated)` (tier-1, satisfying the C1–C8 automated-proof
  contract by composing the **project's** runner — mango bundles none) → `PASS(render@<bp>)` (tier-2,
  a recorded render of the real surface at the breakpoint asserting the visible measurable — a
  **first-class proof, not an exclusion**) → `EXCLUDED` (human-approved, only when neither is
  reachable). Dropping a tier because there is no runner is fine; dropping to *nothing* is not. mango
  **never stops for a missing runner** — it scaffolds tier-1 (per `templates/ui-proof-scaffold.md`),
  else records a tier-2 render proof, else an exclusion.

Enforced at `analysis` (the `TRACK` + `SURFACES` artifacts), `design` (the `DESIGN.md` contract +
layer-matched, surface-aware verification plan + under-coverage banner), `execute` (token-first +
Pointer Events + the elastic-tier proof manifest), and `review` (the rubric scored against `DESIGN.md`
+ the `N == M + X` surface check, re-running ≥1 proof); guarded by `scripts/validate.py` (the track +
surface/manifest tokens). The M10 pointer-parity gate **degrades gracefully** — an always-on greppable
smell can block, while the behavioral dispatch-assert runs only when the environment can and is
otherwise a recorded exclusion, so it never wedges review. **Own** the coverage rule, the tier ladder,
the manifest schema, and the runner-agnostic scaffold spec; **compose** the runner itself.
