## Frontend track — token-first + input-agnostic (only when `config.track` includes frontend)

When TRACK includes frontend, implement the approved change list under these rules (still nothing
beyond the approved list):

- **Token-first (greppable).** All colour / spacing / radius / font go through the **design tokens**
  (theme + CSS custom properties) declared in `config.design_doc_path` (`DESIGN.md`). **No scattered
  hardcoded hex/px** in component code — the review rubric greps for raw `#rrggbb` / `NNpx`.
- **Input-agnostic interactions.** Use **Pointer Events**, not mouse-only handlers
  (`mousedown`/`mousemove`/`clientX`). **No affordance gated solely on `:hover`** — every action and
  any information shown on hover must also be reachable by tap + focus.
- **Compose the aesthetic layer; never own it.** If a taste/design skill is installed, compose it for
  aesthetic generation; **if none is installed, follow `DESIGN.md`** and proceed. **Never stop because
  a taste skill is absent** — mango blocks only on a missing measurable number, never on a missing
  aesthetic.

## Surface-coverage proof manifest (frontend integration/runtime/behavioral ACs)

For every frontend AC whose risk layer is integration / runtime / behavioral, **emit/update the proof
manifest** in the working doc beside the verification plan — **one row per (AC × affected surface)**
across the analysis `SURFACES: N` inventory. The proof **tier is elastic, but a proof is never
optional** — produce the **highest tier the project can support** per surface:

1. **`PASS(automated)` (tier-1)** — compose the **project's declared automated-UI runner** (detect it
   from the project's declared test scripts / `config.test_command`; **mango bundles no runner**)
   into the shape in `<mango>/templates/ui-proof-scaffold.md`, satisfying the C1–C8
   automated-proof contract. Record a re-runnable `proof-cmd` + inspectable artifact.
2. **`PASS(render@<bp>)` (tier-2)** — when no runner is declared (or `tests/` is off-limits), record a
   **render/screenshot of the real affected surface at the declared breakpoint** asserting the visible
   measurable (e.g. `scrollWidth ≤ clientWidth`, target ≥ size, indicator present). This is a
   **first-class proof, NOT an exclusion** — the cheap reality-facing check; record the artifact path.
3. **`EXCLUDED(approver, reason)` (tier-3)** — only when neither tier is reachable (a state that cannot
   be driven). Human-approved; reuse the v0.6/T2 coverage-gap exclusion record.

**Never silently skip a surface.** Dropping tier-1 → tier-2 because there is no runner is expected and
fine; dropping to *nothing* is not — a frontend AC with no manifest entry at any tier blocks the gate.
**`execute` never stops merely because no runner is installed** — it scaffolds tier-1 if a runner
exists, else records a tier-2 `render@<bp>` proof, else records an EXCLUDED row. Fill each manifest
row's `tier`, `proof-cmd|artifact`, `asserts`, and `status`; the surface count `N == M + X` is scored
at review.

**One assertion PER CLAUSE of a multi-clause M-gate.** An M-gate whose threshold has more than one
clause (e.g. M4 = touch-target `size ≥ 44×44 px` **and** `spacing ≥ 8 px`; M7 = focus indicator
`visible` **and** `contrast ≥ 3:1`) is only proven when **every clause** carries its own assertion.
For each in-scope multi-clause M-gate, **enumerate one assertion per clause** and give the proof
manifest **one row per clause** (M4 → a `size` row + a `spacing` row; M7 → a `visible` row + a
`≥3:1 contrast` row). A clause with **no assertion** makes the gate **incomplete → it blocks, exactly
as a missing surface does** — proving the easy clause (size) does not clear the gate while the other
clause (spacing) goes unasserted. Use the clauses the rubric already names in
`<mango>/templates/frontend-rubric.md`; do **not** invent new clauses. This is the
per-item-inventory rule (which prevents aggregate-count hiding) generalized from surfaces to the
clauses of a gate.
