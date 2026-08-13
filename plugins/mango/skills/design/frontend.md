   **Frontend ACs (when `config.track` includes frontend) are classified honestly by the same rule.**
   A "renders / responsive / no horizontal scroll / contrast / focus / a11y / touch-target" AC has an
   **integration/runtime** (or `document` / `computed-style`) risk layer — never pure logic. A
   unit-only proof (a mocked DOM) is a layer-match `❌` and **blocks Gate 2**; it clears only with an
   integration/e2e proof against a **real rendered DOM** (or the served document for the viewport-meta
   gate), or a recorded human-approved coverage-gap exclusion. The M1–M10 risk-layer floor in
   `<mango>/templates/frontend-rubric.md` lists each gate's layer; reuse the v0.6
   layer-match mechanism here — do not fork it.

   **Surface-aware rows — one row per (AC × affected surface).** For a universal / app-wide frontend
   AC, the denominator is the **surface inventory N** from analysis (`SURFACES: N`, enumerated from
   code). Lay out the verification plan / proof manifest with **one row per affected surface**, not a
   single ticket-scoped row — proving "the surfaces the ticket named" while reachable surfaces go
   unproven is the exact bug this removes. Each row names its proof **tier** (the ladder is elastic
   but a proof is never optional): `automated` (tier-1, satisfies the C1–C8 automated-proof contract)
   → `render@<bp>` (tier-2, a recorded render of the real surface at the breakpoint asserting the
   visible measurable — a **first-class proof, not an exclusion**) → `excluded` (human-approved, only
   when neither tier is reachable). See `<mango>/templates/ui-proof-scaffold.md` for the
   tier-1 shape `execute` will fill.

   **Mechanism-4 banner — under-coverage must be impossible to miss.** For each universal/app-wide
   frontend requirement, let `N` = |surfaces|, `M` = surfaces with a planned valid proof (any tier),
   `X` = recorded exclusions. When `M + X < N`, emit a loud line — as unmissable as an unfilled matrix
   column — and **block Gate 2**:

   `⚠ surfaces proven: <M+X>/<N> — <uncovered surfaces> have no proof; cover or record an exclusion.`


## Frontend track — the `DESIGN.md` contract (only when `config.track` includes frontend)

When TRACK (from analysis) includes frontend, **create or update the project design contract** at
`config.design_doc_path` (default `DESIGN.md`) from `<mango>/templates/design-doc.md`
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
