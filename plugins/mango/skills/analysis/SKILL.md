---
name: analysis
description: Phase 1 of the mango ticket lifecycle. Use when starting work on a ticket — pulls the ticket, opens the working doc, and decomposes every section into a counted C/R/G/AC requirements matrix with AC validation and a clarification tally. Stops at Gate 1.
---

Operate under `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md`. This phase enforces principle 1 (Think before
coding) via the `CLARIFICATION` tally, the `AC validation` table, the `SECTIONS found = decomposed`
count, and the requirements matrix.

**Ground rules.** Read `${CLAUDE_PROJECT_DIR}/.harness.json` and ground every rule in
`config.rulebook_path`. If `.harness.json` is missing, STOP and tell the user to create one from
`${CLAUDE_PLUGIN_ROOT}/config/harness.example.json`. Tracker READS may use `config.tracker.read_mcp`
(if set); never write anything in this phase.

## Steps

1. **Pull the ticket.** Read it via `config.tracker.read_mcp` (or ask the user to paste it if no
   read MCP is configured). **Request the full field set in one read** — a tracker read can default
   to a minimal field set (e.g. summary + status) and return an empty description, wasting a
   re-fetch. Request `config.tracker.fields` if it is set; otherwise request a sensible full default
   (description/body, type, labels, parent, priority). Capture the raw ticket text verbatim — later
   phases re-derive from it.
2. **Open the working doc — placement by where the ticket lives.** The working doc is the mutable
   state doc carrying all five phases, built from `${CLAUDE_PLUGIN_ROOT}/templates/ticket.md`. Choose
   its placement from `config.work_doc_mode` (`auto | separate | embed`, default `auto`):
   - **tracker-hosted ticket** (the ticket lives in the tracker, not as a repo file) → always a
     **separate** file `<config.work_dir>/<KEY>.work.md` (default `work_dir` = `tickets_dir`).
   - **local-file ticket** (the ticket is itself a file in the repo, e.g.
     `<config.tickets_dir>/<KEY>.md`) → under `auto`/`embed`, **append** the working doc to that same
     file **below a clear raw-ticket separator line** (the exact line
     `<!-- ===== MANGO WORKING DOC (below this line is NOT part of the raw ticket) ===== -->`), so
     there is one file, not a duplicate. Under `separate`, still write `<KEY>.work.md`.
   Whichever placement is chosen, the **raw ticket portion stays above the separator** and the
   working-doc portion below it; **never** mix design/matrix/rationale into the raw ticket text. This
   separation (separate file, or below the separator line) is what lets the review phase hand the
   challenger only the raw ticket without leaking the design — preserving the v0.3 challenger-blind
   guarantee in both modes (observed failure: when the ticket file doubled as the working doc with no
   separator, the challenger's independence rested on a manual "withhold" convention rather than
   structure). Record the chosen `work_doc_mode` and the working-doc path in `Session status`.
3. **Decompose EVERY section.** Using `config.ticket_header_schema` (which maps each ticket header
   to C/R/G/AC), turn every ticket section into requirements-matrix rows. Each row: ID, Source,
   Verbatim, Interpretation, Ph1 evidence, Status. Emit the count line:

   `SECTIONS: <n> found (names) | <n> decomposed | ROWS: C=.. R=.. G=.. AC=..`

   Sections found MUST equal sections decomposed.

   **Freeform tickets.** If the ticket has no sections matching `config.ticket_header_schema`,
   **synthesize** the C/R/G/AC matrix from the prose, set `STRUCTURE: synthesized` in the working
   doc, and raise a mandatory Gate-0 item: *"Confirm my reading of this freeform ticket before I
   investigate."* This folds into the `CLARIFICATION` tally below (it counts toward `j`), so a
   synthesized reading always stops at Gate 0 until the human confirms. Structured tickets set
   `STRUCTURE: native`.
4. **AC validation table — and a falsifiability check.** Independently re-derive every concrete
   acceptance value (numbers, thresholds, counts, formats). Each mismatch between the ticket's stated
   value and your computed value becomes a **Gate-1 question carrying the computed value** — never a
   silent correction.

   **Every acceptance value must be either falsifiable or an explicit manual-check exclusion.** For
   each AC, its value must be **falsifiable** — a measurable/greppable definition that a test or grep
   could disprove (e.g. "a named element with property X is present", "count == N", a threshold), not
   a vague adjective ("looks clean", "is fast", "works well"). An AC that is **not** falsifiable must
   instead be recorded up front as an **explicit manual-check exclusion** (unmeasurable → a human
   verifies it; logged as a coverage-gap exclusion in the working doc, reusing the existing
   coverage-gap-exclusion machinery — do not invent a parallel one). An AC that is **neither**
   falsifiable **nor** a recorded manual-check exclusion is **flagged by this step** and **may not
   carry a matrix `✅`** — a bare self-reported `✅` cannot stand in for an unmeasurable or unbuilt
   thing. Where a vague word is the only blocker, pin it to a measurable form as a Gate-1 question
   (carrying your proposed definition), exactly as an AC-value mismatch is raised.

   **Uncodified-standard nudge (detect-and-surface — never silently apply, never silently ignore).**
   When you find yourself **applying a standard at a gate** — an AC validation, a rule-compliance
   judgment, or a review criterion (a spacing/contrast constant, a naming convention, a threshold) —
   that has **no codified rule** in `config.rulebook_path`, do **not** silently enforce it and do
   **not** silently drop it. **Surface it as an uncodified-standard item** and **nudge the human to
   ratify it** through `codify`'s provisional→ratify flow (reuse that existing machinery — do not invent
   a parallel one). mango **detects and surfaces; the human ratifies; mango never authors the rule.**
   Until it is ratified, the standard may **not** silently gate-block as if it were codified — an
   uncodified standard creates gate-block ambiguity exactly because no one chose it, and this removes
   that ambiguity by putting the choice in front of the human.
5. **Clarification tally.** Emit:

   `CLARIFICATION: <M> raised | <k> self-resolved (cited) | <j> for human decision`

   Self-resolved items must cite the source (rulebook §, code `path:line`, ticket line). **If j > 0,
   STOP at Gate 0** and ask the human those questions before going further.
6. **Universal inventory.** For any requirement saying "all/every/no", build a numbered inventory
   of the affected items with total **N** (this N is the denominator later phases prove against).
   When a requirement is a counted **"do X for each of N"** (it maps onto this numbered inventory of
   size N), record it as a **per-item checklist** — **one row per item**, not a single aggregate row
   — and note on the requirement that review must confirm **every** item, not just a total. An
   aggregate "k/N" is not enough for a "for each" requirement: the tail can ship incomplete behind a
   passing count.

   **Surface inventory — for a universal / app-wide FRONTEND requirement, the denominator N comes
   from the CODE, never the ticket.** When the track includes frontend (confirmed at step 10) and a
   requirement is phrased all/every/no **or is inherently page-wide** (no horizontal scroll, reflow,
   focus-visible, contrast — anything that holds across the UI), enumerate **every reachable surface**
   — each route, full-window overlay, modal, and major mounted state — and set **N = |surfaces|**.
   Source the surface list from the opt-in `sitemap` (`config.docs_dir/sitemap.md`) **if present**;
   if it was never generated, run a lightweight read-only **"enumerate reachable views"** sub-step
   (inspect the routing/entry points). The ticket's examples are a **hint, never the denominator** —
   counting only the surfaces the ticket named is exactly the failure this removes. Emit it as a
   counted, challenger-checkable artifact (like `TRACK`):

   `SURFACES: <N> — <surface>, <surface>, …`

   A surface the change *can* affect that ends up with neither a proof nor a recorded exclusion makes
   the requirement **incomplete** — later phases (design/execute/review) prove against this N.
7. **Cause / gap analysis.**
   - Bug → root cause classified against `config.cause_taxonomy`, with `path:line`.
   - Enhancement → per-goal gap analysis (current vs target), with `path:line`.
8. **Blast radius.** Identify the handler/entry point, the blast radius (callers, dependents), and
   which of `config.repos` are touched. **If a `db-map` has been generated** (under `config.docs_dir`,
   from the opt-in `db-map` skill), consult it to widen the blast radius to **schema dependents** —
   columns still read/written, foreign keys, and dependent views/procedures. This is "use it if
   present"; never require it — the lifecycle runs fully when no `db-map` exists. **Fan-out (cost knob):** on the **full** tier you may fan
   out read-only Explore agents to investigate, but only if `config.explore_fanout` is true
   (default true). The **lite** tier always skips fan-out. **Model delegation** (see
   `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md`): keep the judgment work of this phase — decomposition, AC
   validation, root-cause/gap, scope — on the strong model; delegate only **bulk read-and-extract**
   (reading many files to pull facts) to the Haiku `extractor` worker, more so when
   `config.cost_tier` is `economy`. Run grep/test/lint via the Bash tool directly — never spawn a
   model for a one-line shell command.
9. **Baseline capture — run the verification command once on the untouched checkout
   (detect-not-assume).** Before any change, run `config.test_command` (and any declared lint) **once
   on the untouched checkout** and record the result as a counted artifact:

   `BASELINE: green | red | flaky — <specific failing items if red/flaky>`

   A clean checkout is not assumed green: a project's verification command can be **unsatisfiable on
   a fresh checkout** (a pre-existing/vendored failure, a flaky sub-pixel assertion). When
   `baseline ≠ green`, the Definition of Done for later phases becomes **"prove the delta is green"**
   — the change must introduce **no new failure** and must fix any it claims to; each pre-existing
   failure **outside** the change is recorded as a **baseline exclusion** (neither a blocker nor a
   silent pass). This is **project-supplied**: mango **detects and records** the baseline; it does
   **not** decide which pre-existing failures are acceptable — that is a human/rulebook call, logged.
   `design`/`execute` prove against this baseline and `review`/`finalise` compare against it, never
   against a blanket "all green".
10. **TRACK — emit as a counted artifact.** Declare which gate set(s) apply, using `config.track`
   when set, otherwise **infer from touched files** (step 8's blast radius). Emit:

   `TRACK: backend | frontend | fullstack — <k>/<N> touched files under UI paths`

   Use `frontend` when the materially-touched files are predominantly UI; `fullstack` when **both**
   the UI side and a server/data side are materially touched; `backend` otherwise. **TRACK is
   orthogonal to TIER** — TIER is process weight, TRACK is which gate set applies; a ticket may be
   `track=frontend` + `TIER=lite`. When TRACK includes frontend and any declared `config.breakpoints`
   width is a **small viewport** (or the 320 px floor applies), note that the **width-parametric gates
   (M2 no horizontal scroll, M3 reflow @320 px) are in scope** — so the challenger counts them at
   review. On `track=backend` this is a one-line declaration and nothing else in the phase changes.
11. **Rule-compliance section coverage — enumerate the applicable rulebook sections by change type.**
    The rule-compliance check must not enumerate an ad-hoc subset of `config.rulebook_path`. Derive the
    **applicable rulebook sections from the change TYPE** present in the change-list / blast radius
    (step 8), and check **each one explicitly** — or mark it **N/A with a reason**. Concretely: a
    **migration / schema change** in the change-list makes the **DB-conventions section mandatory**
    (grants/permissions, soft-delete, naming, indexing — a migration that ships without that section's
    GRANT breaks in prod with permission-denied); a **new UI surface** makes the **design-token / a11y
    section mandatory**; and so on for each change type the rulebook covers. The applicable-section list
    is **derived from the change type**, not hand-picked. Emit the coverage as a counted artifact:

    `RULE SECTIONS: <applicable §s by change-type> — each checked ✅ / N/A (reason)`

    A rulebook section that applies to this change type but is **neither checked nor marked
    N/A-with-reason** is a **finding** — silently omitting an applicable section is exactly the miss
    this removes (a migration that shipped with no GRANT and a missing soft-delete, caught only at
    review). This detects-and-surfaces; it never authors the rule (an uncodified standard still routes
    through the step-4 `codify` provisional→ratify nudge).
12. **Scope.** Declare `SCOPE: S|M|L`. This is the scope baseline the *outgrew-its-ticket* nudge
   (`solve`) compares the realized scope against at later gates: if the realized scope crosses up a
   tier (S/M → L) or the diff materially exceeds the approved one, a later gate stops to re-scope or
   split rather than silently absorbing the growth.
13. **Tier.** After SCOPE, declare `TIER: lite | full`. Key the lite/full decision on the
    **resolved inventory denominator N** (from the step-6 numbered inventory), **not** on the mere
    presence of universal wording. A requirement that *sounds* universal ("all/every/no") but
    resolves to **N = 1** is lite-eligible — a single-site change already covers "all". Choose
    **lite** only when ALL hold: `SCOPE=S`, a single file / single requirement row, **no universal
    requirement with N > 1** (N=1 does not disqualify), and the ticket is not security-tagged.
    Otherwise **full** (the existing five-phase behaviour). Lite routes through the `quick` skill;
    full keeps the full matrix, challenger, sweep, and gates.
14. **Self-audit, then STOP at Gate 1.** Confirm: every section decomposed, AC table complete with
    every acceptance value **falsifiable or a recorded manual-check exclusion** (none carrying a bare
    `✅`), `BASELINE` captured, `j = 0` (or Gate 0 already cleared), inventory N set, matrix `Status`
    filled, `RULE SECTIONS` coverage emitted (every rulebook section applicable to the change type
    checked or N/A-with-reason), `STRUCTURE`, `TRACK`, and `TIER` declared, and — when the track
    includes frontend with a universal/app-wide requirement — `SURFACES: N` emitted from the code
    surface. Write Phase 1 into
    the working doc and the `Session status` block, then STOP and wait for the user. Do not begin
    design.
