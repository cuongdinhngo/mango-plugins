## Frontend track — score the rubric against `DESIGN.md` (only when `config.track` includes frontend)

When TRACK includes frontend, the reviewer **and** the challenger also score
`<mango>/templates/frontend-rubric.md`. Every rubric item is **falsifiable**
(measurable or greppable) and is checked **against the project's `DESIGN.md`**
(`config.design_doc_path`), never against a blanket aesthetic rule — "is it tasteful?" is **out** of
the rubric; taste exists only as `DESIGN.md` conformance. The rubric covers:

- **Core (always):** matches `DESIGN.md` (colour/font/spacing/radius from agreed tokens); no
  hardcoded hex/px outside tokens (grep); semantic HTML; **state never by colour alone** (icon +
  text); `prefers-reduced-motion` respected; no aesthetic change mixed into a logic/backend PR.
- **Responsive & touch — M1–M10 (all falsifiable):** viewport meta / zoom (M1), no horizontal scroll
  at each breakpoint + the 320 px floor (M2), reflow @320 px (M3), **touch-target** ≥ 44×44 px with
  ≥ 8 px spacing (M4), input zoom guard ≥ 16 px (M5), tap/hover parity (M6), focus-visible + ≥ 3:1
  indicator (M7), contrast (M8), safe-area respect (M9), pointer-input parity (M10). These are the
  **a11y** / responsive gates; each carries its risk layer for the layer-match gate.

**Layer-match re-confirmation extends to the frontend ACs (do not fork it).** Each M-gate carries a
risk layer above the logic/unit layer (`document` / `computed-style` / `integration/runtime` /
`behavioral`); a unit-only proof (mocked DOM) clears **none** of them. Re-confirm at step 8 that no
frontend AC closed clean on a layer-mismatched proof — a `❌` blocks clean unless it is a recorded,
human-approved coverage-gap exclusion.

**M10 degrades gracefully — it never wedges the review.** Its always-on greppable smell (a mouse-only
handler or hover-only interaction with no pointer/touch equivalent) always runs and can block; its
best-effort behavioral dispatch-assert runs **only when the environment can**, and when it can't it
is recorded as a named human-approved coverage-gap exclusion rather than blocking.

## Surface-coverage proof manifest — the `N == M + X` check (frontend universal/app-wide reqs)

For each universal / app-wide frontend requirement, the challenger scores the **proof-manifest**
(`execute`'s one-row-per-(AC × surface) record) — independently of the working doc, preserving its
ticket-blindness: it **re-enumerates the reachable surfaces from the branch code** (this is its own
`SURFACES` count) and rebuilds the requirement from the raw ticket, then checks every reachable
surface has a proof in the diff. The count:

- `N` = |reachable surfaces from code| · `M` = surfaces with a valid **PASS (any tier)** · `X` =
  recorded human-approved **EXCLUDED**. **The gate passes iff `N == M + X`.** A ticket-scoped proof
  covering 2 of 5 reachable surfaces yields `N=5, M=2` → **blocked**, with the loud banner
  `⚠ surfaces proven: 2/5 — <uncovered> have no proof; cover or record an exclusion.`
- **Score each entry by tier:** a `PASS(automated)` row against the **C1–C8** automated-proof contract
  (real SUT not mocked, threshold asserted not "looks ok", role+name selectors — a non-role selector
  with no recorded reason is flagged, one layer per AC, determinism); a `PASS(render@<bp>)` row against
  the lighter **render-proof contract** (real surface at the breakpoint, visible measurable asserted,
  a recorded artifact the reviewer can see). A `render@<bp>` is a **first-class proof, not an
  exclusion** — do not demand a runner where the project has none.
- **Defeat fabricated entries:** the challenger **re-runs ≥ 1** tier-1 `proof-cmd` (or, for tier-2,
  **confirms the recorded render artifact exists**). Under **`TIER=lite`** this lightens to
  **confirming command/artifact presence** rather than a live re-run — but surface coverage, the
  manifest, and a proof per surface stay **mandatory**.

This **extends** the step-8 layer-match re-confirmation; it does not fork it. `fullstack` applies this
to its frontend ACs only; a `track=backend` ticket has no manifest and this section is inert.
