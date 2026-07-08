---
name: design
description: Phase 2 of the mango ticket lifecycle. Use after analysis clears Gate 1. Produces the approach, rejected alternatives, the smallest change-list traced to matrix rows, rule-compliance check, and the named proving test. Stops at Gate 2.
---

Operate under `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md`. This phase enforces principle 2 (Simplicity
first) via the smallest change list + `SCOPE`, and principle 4 (Goal-driven) via the named proving
test, the **per-AC verification plan** (proof at the layer where each requirement can fail), and the
**Assumptions** check (no unresolved novel-untested third-party/runtime assumption) — all required
at this gate.

**Ground rules.** Read `${CLAUDE_PROJECT_DIR}/.harness.json` and ground every rule in
`config.rulebook_path` and `config.standards_path`. If `.harness.json` is missing, STOP and tell the
user to create one from `${CLAUDE_PLUGIN_ROOT}/config/harness.example.json`. No code is written in
this phase.

## Steps

1. **Confirm Gate 1 cleared.** Read the working doc `<config.work_dir>/<KEY>.work.md`. The
   requirements matrix and AC table must be filled and `CLARIFICATION` `j = 0`. If not, return to
   analysis.
2. **Approach + Rejected alternatives.** State the chosen approach in a few lines, then record at
   least one **Rejected alternative** and why (enforces principle 1's record of thought).
3. **Assumptions.** List every assumption the approach leans on, each tagged `verified |
   novel-untested`. For any `novel-untested` assumption about **third-party or runtime behaviour**
   (e.g. "two live editors of library X can coexist", "this API is idempotent under retry"), the
   design must EITHER (a) run a throwaway **spike** now and record the result here, OR (b) shape the
   Gate-2 proving test (step 7) as an integration/e2e proof that would **fail if the assumption is
   false**. **Gate 2 may not pass with an unresolved `novel-untested` assumption.** (Observed
   failure: a design leaned on an untested "two live rich-text editors coexist" assumption — the
   exact thing that broke — because nothing forced de-risking a novel runtime assumption.)
4. **Smallest change-list table.** List the minimum set of changes. Columns: change, file/area,
   `Ph2 covered by` (which matrix row(s)), `k/N`. **Every item must trace to a matrix row** — an
   item with no row behind it fails the gate. Prefer the smallest edit; no speculative abstraction,
   no indirection serving a single call site.

   **Test blast-radius (mechanical) — fold invalidated existing assertions in as proof collateral.**
   Before closing the change list, **mechanically enumerate the existing assertions this change will
   invalidate**: grep the repo for the exact **copy keys, headings, route shapes, or exports** the
   change touches (the strings/symbols being renamed, moved, or reworded), and list every existing
   test / spec / snapshot that references them. **Fold each hit into the approved change list as an
   explicit *proof collateral* item** (file/area + the matrix row it rides), up front — an existing
   test whose assertion the change breaks is a **planned edit**, not an execute surprise. This
   converts a predictable execute deviation into a Gate-2 item. *(Observed failure: a change reworded
   a heading that an existing shell test asserted; the change list never mentioned that test, so it
   surfaced only as an execute deviation.)*
5. **Rule compliance.** Check the proposed change against `config.rulebook_path` and
   `config.standards_path`; note any rule that constrains the design and how you comply.
6. **Verification plan (per-AC, layer-matched) — fill the layer-match column BEFORE naming the
   proving test (step 7).** Emit a table with one row per acceptance criterion / at-risk
   requirement:

   `AC | risk layer (logic | integration | runtime/3p | e2e) | proof artifact (unit | integration | e2e | manual-recorded) | layer-match? ✅/❌`

   Classify each AC's **risk layer** first — the layer where the requirement can *actually fail* —
   then choose its proof artifact to match. A requirement that can only fail at integration/runtime
   (classification cue: worded as "renders / runs / dispatches / persists / sends") cannot be proven
   by a pure-logic test. Do **not** triage on keywords alone — the gate keys on the **risk-layer vs
   proof-layer comparison** the plan records; the wording is only a hint to classify the risk layer.

   **Frontend ACs (when `config.track` includes frontend) are classified honestly by the same rule.**
   A "renders / responsive / no horizontal scroll / contrast / focus / a11y / touch-target" AC has an
   **integration/runtime** (or `document` / `computed-style`) risk layer — never pure logic. A
   unit-only proof (a mocked DOM) is a layer-match `❌` and **blocks Gate 2**; it clears only with an
   integration/e2e proof against a **real rendered DOM** (or the served document for the viewport-meta
   gate), or a recorded human-approved coverage-gap exclusion. The M1–M10 risk-layer floor in
   `${CLAUDE_PLUGIN_ROOT}/templates/frontend-rubric.md` lists each gate's layer; reuse the v0.6
   layer-match mechanism here — do not fork it.

   **Surface-aware rows — one row per (AC × affected surface).** For a universal / app-wide frontend
   AC, the denominator is the **surface inventory N** from analysis (`SURFACES: N`, enumerated from
   code). Lay out the verification plan / proof manifest with **one row per affected surface**, not a
   single ticket-scoped row — proving "the surfaces the ticket named" while reachable surfaces go
   unproven is the exact bug this removes. Each row names its proof **tier** (the ladder is elastic
   but a proof is never optional): `automated` (tier-1, satisfies the C1–C8 automated-proof contract)
   → `render@<bp>` (tier-2, a recorded render of the real surface at the breakpoint asserting the
   visible measurable — a **first-class proof, not an exclusion**) → `excluded` (human-approved, only
   when neither tier is reachable). See `${CLAUDE_PLUGIN_ROOT}/templates/ui-proof-scaffold.md` for the
   tier-1 shape `execute` will fill.

   **Mechanism-4 banner — under-coverage must be impossible to miss.** For each universal/app-wide
   frontend requirement, let `N` = |surfaces|, `M` = surfaces with a planned valid proof (any tier),
   `X` = recorded exclusions. When `M + X < N`, emit a loud line — as unmissable as an unfilled matrix
   column — and **block Gate 2**:

   `⚠ surfaces proven: <M+X>/<N> — <uncovered surfaces> have no proof; cover or record an exclusion.`

   **Binding gate rule — the layer-match is enforced, not advisory.** If an AC's **risk layer is
   integration / runtime / e2e and its proof artifact is at the logic/unit layer**, that row is a
   layer mismatch → `❌` and **Gate 2 is blocked**. The row passes only when the proof is **upgraded**
   to the matching layer, OR it is recorded as a **named, human-approved coverage-gap exclusion**
   (item · risk tier · why deferred · follow-up) in the working doc's *Coverage-gap exclusions* slot.
   A layer-match `❌` that is neither upgraded nor a recorded human-approved exclusion **blocks Gate 2
   — it does not pass silently.** (Observed failures: a named proving test was a store unit test that
   mocked the integration layer, so it stayed green while the real integration-layer behaviour was
   broken; separately, an "in-browser confirm" acceptance criterion had no planned proof and surfaced
   only at Gate 4. And: a requirement whose real risk sat at an integration/behavioural tier was only
   unit-proven, so the challenger's later "not met" read as a hard failure when it was a proof-tier
   mismatch that should have been a recorded exclusion.)
7. **Proving test (at the matching layer).** With the risk layer classified (step 6), name the
   **proving test**: the specific assertion that **fails pre-change and passes post-change**,
   runnable via `config.test_command`, and **sitting at the risk layer** of the AC it proves. State
   the exact invocation. Gate 2 cannot pass without it; a proving test below its AC's risk layer is a
   layer-match `❌` and blocks Gate 2 (see step 6).
8. **Rollback + porting plan.** State how to revert, and the porting plan across `config.repos` if
   the change touches shared code (which repos, in what order).
9. **Confirm SCOPE.** Re-affirm or adjust `SCOPE: S|M|L` from analysis; if it grew, say why. If the
   realized scope has **crossed up a tier** (especially S/M → L) or the change-list materially
   exceeds the analysis baseline, raise the *outgrew-its-ticket* nudge at this gate: stop to
   **re-scope or split** (and flag any branch/PR-type drift) rather than silently absorbing it.
10. **Self-audit, then STOP at Gate 2.** Confirm: every change-list item has a matrix row, `Ph2
    covered by` filled `k/N`, every assumption tagged and every `novel-untested` 3p/runtime one
    resolved (spike result or integration-shaped proving test), proving test named and runnable, the
    verification plan has **no ❌** (or every ❌ is recorded as a human-approved coverage-gap
    exclusion with a follow-up), rollback + porting recorded, and — when track includes frontend —
    `DESIGN.md` created/updated (see below) and, for any universal/app-wide frontend requirement,
    the proof manifest laid out **one row per (AC × surface)** with `N == M + X` (no under-coverage
    banner standing). Write Phase 2 into the working doc and update `Session status`, then STOP and
    wait for the user. Do not begin execution.

## Frontend track — the `DESIGN.md` contract (only when `config.track` includes frontend)

When TRACK (from analysis) includes frontend, **create or update the project design contract** at
`config.design_doc_path` (default `DESIGN.md`) from `${CLAUDE_PLUGIN_ROOT}/templates/design-doc.md`
**before naming the verification plan (step 6)** — the frontend rubric is scored *against this file*,
so it must exist and be current. Hard rules for it:

- **Palette derives from domain meaning FIRST, general aesthetic rules SECOND.** A blanket rule (e.g.
  "ban colour X") must yield to domain meaning — a domain term may literally denote that colour.
  Record each token's meaning so the reviewer checks against the contract, not a blanket rule.
- **Separate "shell" (character-rich pages) from "data-core" (tables/grids/charts):** data-core is
  **legibility-first and static**; a data-core region may scroll inside its own bounded container, but
  the document must not.
- Include the generic **"Responsive & touch"** section: declared breakpoints (mirror
  `config.breakpoints`); the narrow-width **navigation pattern**; which regions **collapse vs reflow
  vs scroll-in-container**; thumb-zone priority; the **motion** policy (honour `prefers-reduced-motion`,
  limit animation to `transform`/`opacity`). These are the **choices** the responsive gates (M2/M3
  and the rest of M1–M10) are scored against — they live here, never gated by mango.

**Own the durable, compose the volatile.** mango owns only the measurable/greppable conformance to
this contract. The *aesthetic-generation* layer is **composed, never owned**: call an installed taste
skill if present, else follow `DESIGN.md` — **never stop because a taste skill is missing** (mango
blocks on a missing **number**, never on a missing aesthetic). The breakpoint **values**, the
narrow-width **navigation pattern**, and which regions **collapse vs reflow** are `DESIGN.md` choices,
not mango gates.
