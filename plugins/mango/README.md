# mango

A portable, **gated ticket-lifecycle harness** for Claude Code. mango ships the *machinery* — six
gated phases, three read-only review agents, and a working-doc template — and reads every
project-specific rule at runtime from a per-project `.harness.json`. The same plugin installs into
any project unchanged.

**Harness, not rules.** No stack assumptions are baked in (no framework, language, database, or
region specifics). Your engineering rule book, repos, test command, tracker, and ticket schema all
live in `.harness.json`. Trust comes from emitted, counted, gate-blocking artifacts — not prose.

**Secrets never ship.** No token or credential belongs in `.harness.json` or any plugin file; keep
them in a gitignored `.env`.

## Getting set up

| Skill | Use | Produces |
|-------|-----|----------|
| `/mango:init` | Once per project | Detects the stack read-only, interviews only for the undetectable, writes `.harness.json` (guesses marked `UNVERIFIED`), **asks whether `.harness.json` is committed or kept local** (and gitignores it on "local"), and scaffolds a single-file starter rule book if none exists. |
| `/mango:doctor` | Anytime / before a run | A ✅/⚠/❌ health check of `.harness.json` with exact remediation, prefaced by `mango <version> @ <base path>` so the running version is always visible. `solve` runs it as a fail-fast preflight. |
| `/mango:codify` | When the rule book is missing / thin / inconsistent (opt-in) | **Counts** the conventions the code and schema actually use (code rules **and** database conventions), asks **you** to choose each going-forward standard, and writes them to the rule book tagged **`PROVISIONAL (awaiting ratification)`**. Facilitates; never authors a rule, never auto-picks the majority, never changes code. `doctor` suggests it when the rule book looks thin. |
| `/mango:version-check` | On demand (opt-in) | Reports the running version vs the latest published version and, if newer, **prints** the host `/plugin` commands to update. Needs `update_check_url`; never updates or installs. |

**Defining the rule book — `mango generates the descriptive and facilitates the normative, but never
authors the normative.**` `init` gives you a skeleton rule book with TODOs; when a project has no
rule book, a thin one, or genuinely inconsistent conventions, `/mango:codify` is the deep, opt-in
facilitation. It observes and counts the patterns (presenting "pattern A: 12 files, B: 5" as **data**,
not a verdict), asks you to pick each standard, and records the choices as **provisional** until you
ratify them — the rule the whole plugin grounds in stays the team's decision, never mango's.

### Descriptive maps (opt-in, stack-specific)

Two opt-in adapters generate **descriptive facts** (regenerable, falsifiable) — never normative rules.
They are off unless configured and are **not** part of the lifecycle; the lifecycle runs fully whether
or not either has ever been generated.

| Skill | Use | Produces | Needs |
|-------|-----|----------|-------|
| `/mango:sitemap` | Map the code surface | Routes/endpoints + modules written to `docs_dir` | `code_map_cmd` (or a stack adapter) + `docs_dir` |
| `/mango:db-map` | Map the database schema | Tables, columns+types, primary/foreign keys, indexes, relationships, views/procedures, to `docs_dir` | `db_kind` + (`db_introspect_cmd` **or** `migrations_path`) + `docs_dir` |

A generated `db-map`, **if present**, lets `analysis` widen the Phase-1 blast radius to schema
dependents (columns, FKs, dependent views/procs) — used if present, never required. The *normative*
database conventions live in the `codify` rule book, not in these maps.

## The lifecycle

Run the whole thing with `/mango:solve`, or invoke a phase directly. mango **stops and waits at
every ✋ gate** — silence is never approval.

### Tiers — right-sizing the rigor

`analysis` declares `TIER: lite | full`. **Lite** is chosen only when ALL hold: `SCOPE=S`, a single
file / single requirement row, no universal requirement **with N > 1**, and the ticket is not
security-tagged — otherwise **full**. The lite/full decision keys on the **resolved inventory
denominator N**, not on keywords: a requirement that *sounds* universal ("all/every/no") but resolves
to a single site (**N = 1**) is lite-eligible. Lite routes through `/mango:quick`: two human gates (a
single combined pre-code gate + the final gate), reviewer-only, no challenger, no full matrix, no
fan-out. Full keeps the complete five-phase flow. You can force the lite lane with `/mango:quick
<KEY>`, but `quick` runs a **hard entry check** first and **refuses** (routing you to `/mango:solve`)
if the ticket is security-tagged, touches more than one file, or has a universal requirement that
resolves to N > 1.

| Skill | Phase / Gate | Produces |
|-------|--------------|----------|
| `/mango:analysis` | 1 → Gate 1 | Requirements matrix (C/R/G/AC) + count line, AC validation (each acceptance value must be **falsifiable** or a recorded **manual-check exclusion** — one that is neither is flagged and may not carry a matrix `✅`), clarification tally, universal inventory, root-cause/gap, blast radius, scope, and a `BASELINE:` capture (runs the verification command once on the untouched checkout → `green \| red \| flaky`; when not green the DoD becomes **delta-green**). On the **frontend** track also emits `SURFACES: N` (reachable surfaces enumerated from code) for any universal/app-wide requirement. Surfaces an **uncodified standard** — one applied at a gate with no codified rule — into `codify`'s provisional→ratify flow rather than silently enforcing or ignoring it. |
| `/mango:design` | 2 → Gate 2 | Approach + rejected alternatives, **Assumptions** (`verified \| novel-untested` — a novel 3p/runtime assumption needs a spike or integration-shaped proof), smallest change-list traced to rows, rule compliance, a **per-AC verification plan whose layer-match is a hard gate** (an integration/runtime AC backed only by a logic-layer proof is `❌` and **blocks Gate 2** unless the proof is upgraded or recorded as a human-approved **coverage-gap exclusion**), the proving test named at the matching layer, rollback + porting. On the **frontend** track also creates/updates **`DESIGN.md`** and lays out the verification plan **one row per (AC × surface)**, emitting `⚠ surfaces proven: k/N` when under-covered. |
| `/mango:execute` | 3 (autonomous) | Branch, the approved change list only, the proving test, a verification sweep on **BOTH axes** — the **file set** (diff ⊆ approved list) **and** a **design-conformance self-check** that walks each Gate-2 Approach bullet (`implemented-as-approved \| deviated`) and **records any deviation** even when the file diff is clean — commits with no AI co-author trailer. DoD is **baseline-aware** (delta-green when `BASELINE ≠ green`). Runs the project's formatter **only on authored/edited files** — never a wholesale reformat of a shared/pre-existing file (**format-scope rule**); whole-file conformance is a separate concern (CI / a chore ticket). STOPs to **re-gate if the design is invalidated** and via a **stuck-detector** (`stuck_threshold` failed attempts at the same signature). On the **frontend** track emits the **proof manifest** — the highest-tier proof per surface (`automated`→`render@<bp>`→`excluded`); **never stops for a missing runner**. |
| `/mango:review` | 4 (stop if not clean) | `reviewer` + ticket-blind `challenger` (payload excludes the working-doc portion), scope reconciliation on **both axes** (file set **and** behavioural conformance — a missed Gate-2-bullet deviation is not clean), regression check, **layer-match re-confirmation** (no AC closed clean on a layer-mismatched proof), proving-test result judged against the recorded `BASELINE` (delta-green, not blanket "all green"), `k/N` coverage. A challenger "not met" matching a recorded coverage-gap exclusion does not block; an unrecorded gap does. Round 1 may return a **conditional LGTM** ("LGTM once findings 1–N land"), making the re-review a **verify-only pass** that is **main-loop-by-default**: an in-scope round verifies **in the main loop, dispatching no subagent** (named-fix check + re-run only the affected proof + regression scan, no full re-derivation; the challenger is not re-run) — a reviewer/challenger is **re-dispatched only when a fix changed scope**, the one trigger — with a **docs/bookkeeping carve-out** (reusing finalise's staleness exemption set: working doc / `lessons_path` / rule-book drift-list) so a verify-only fix touching **only** exempt bookkeeping files stays main-loop and does **not** re-dispatch, while any non-exempt out-of-scope file still does. On the **frontend** track also scores the **proof manifest** and the **`N == M + X`** surface check (`surfaces proven: k/N`). On a clean verdict it records a **`Reviewed at <sha>` marker** (commit + reviewed files + working-doc path) for the stale-review guard. |
| `/mango:finalise` | 5 → final gate | **Stale-review guard** (mechanical, file-set — never a commit-count test: diffs the tree against the `Reviewed at` marker, **exempts** the working-doc / bookkeeping paths, and refuses to open a PR — routing back to `review` — only if a **source file changed beyond the reviewed set**; the marker/working-doc bump alone never trips it), optional **project finalise-checklist** walk (`pr_checklist_path`), PR draft, per-action approval for every outward action (incl. a **push-bookkeeping** action so the durable lesson lands on a **shared/pushed ref**, never an orphaned local branch), tracker writes via CLI, a **Cost-ledger content-completeness gate** (refuses to proceed unless every dispatch row is present **and** each token cell carries a value — a real count or the explicit `unmeasured (blocking retrieval)` marker; a blank cell blocks like an unfilled matrix column — the ledger's teeth, still descriptive: checks *presence* of a value, never inspects, ranks, or auto-cuts), follow-up tickets for deferred rows, and a **durable lesson** captured to `lessons_path` on every run. |
| `/mango:quick` | lite lane | Single combined pre-code gate → execute → reviewer-only check → final gate, for trivial tickets. |
| `/mango:solve` | orchestrator | Doctor preflight, then runs all phases in order honouring `TIER`, holding every gate; resumes from `Session status`. Carries the reviewed-commit marker across review→finalise (a re-run of execute/design after a clean review marks it stale) and raises an **"outgrew its ticket" nudge** — if realized scope crosses up a tier (S/M → L) or the diff materially exceeds the approved list, it stops to re-scope or split rather than silently absorbing the growth. |

The four binding principles are in [`PRINCIPLES.md`](./PRINCIPLES.md): think before coding,
simplicity first, surgical changes, goal-driven execution — plus the boundary that **mango generates
the descriptive and facilitates the normative, but never authors the normative.**

### Frontend track — measurable UI gates, composed taste

`config.track` (`backend|frontend|fullstack`, default `backend`) selects which gate set applies. It
is **orthogonal to TIER** (TIER = process weight; track = which gates), so a ticket may be
`track=frontend` + `TIER=lite`. `analysis` emits `TRACK: … — k/N touched files under UI paths` as a
**counted artifact** (from `config.track`, else inferred from touched-file paths) that the challenger
can check. A `track=backend` ticket runs **exactly as in v0.6** — none of the gates below apply.

**The design boundary: own the durable, compose the volatile.** mango embeds only UI knowledge that
is **durable + falsifiable** — a11y thresholds it can *measure*, token-first it can *grep*,
conformance to a per-project **`DESIGN.md`** contract. It **composes, never owns,** the
*aesthetic-generation* layer: it calls an external taste skill **if installed**, else follows
`DESIGN.md`, and **never stops because a taste skill is missing.** mango blocks on a missing
**number**, never on a missing aesthetic. Breakpoint **values**, the narrow-width **navigation
pattern**, and which regions **collapse vs reflow** are *choices* → they live in `DESIGN.md`.

- **`DESIGN.md` contract** (built by `design` from `templates/design-doc.md` at `config.design_doc_path`):
  palette **domain-meaning-first, general rules second** (a blanket "ban colour X" yields to a domain
  term that denotes it); a **shell** (character-rich) vs **data-core** (tables/grids/charts —
  legibility-first, static) split; and a **Responsive & touch** section (declared breakpoints,
  narrow-width navigation pattern, collapse vs reflow vs scroll-in-container, thumb-zone, motion).
- **Falsifiable rubric** (`templates/frontend-rubric.md`, injected by `review` into the
  reviewer/challenger brief — the agents are **not** forked per track): every item is measurable or
  greppable and scored **against `DESIGN.md`**; "is it tasteful?" is out of scope. Core items
  (token-first, no hardcoded hex/px, semantic HTML, state-not-by-colour-alone, `prefers-reduced-motion`)
  plus the **M1–M10** responsive/touch gates:

  | | Gate | Threshold |
  |---|------|-----------|
  | M1 | viewport meta / zoom not disabled | `width=device-width, initial-scale=1`; no `user-scalable=no` |
  | M2 | no horizontal page scroll at each breakpoint + 320 px floor | `scrollWidth ≤ clientWidth` |
  | M3 | reflow @320 px, no 2-D scroll | WCAG 1.4.10 |
  | M4 | touch-target size + spacing | ≥ 44×44 px (floor 24×24); ≥ 8 px apart |
  | M5 | input zoom guard | control `font-size ≥ 16px` |
  | M6 | tap/hover parity | nothing exposed only via `:hover` |
  | M7 | focus-visible + indicator contrast | ≥ 3:1 |
  | M8 | contrast | text ≥ 4.5:1; UI/state ≥ 3:1 |
  | M9 | safe-area respect | fixed/sticky edges use `env(safe-area-inset-*)` |
  | M10 | pointer-input parity | drag/resize/hover also fire via Pointer Events |

  Constants (44/24 px, 16 px, 4.5:1, 320 px) are **standards** → fixed, not config.
- **Layer-match hard gate (reused from v0.6, not forked).** A "renders/responsive/contrast/a11y" AC
  has an integration/runtime (or `document`/`computed-style`) risk layer; a unit-only proof against a
  mocked DOM is `❌` and **blocks Gate 2**, clearing only with a proof against a **real rendered DOM**
  (or the served document for M1) or a recorded human-approved coverage-gap exclusion. A
  **risk-layer floor** puts `document`/`computed-style`/`integration-runtime`/`behavioral` all above
  the logic/unit layer. `execute` is **token-first** and **input-agnostic** (Pointer Events, no
  affordance gated solely on `:hover`).
- **M10 degrades gracefully — never wedges review.** Its always-on greppable smell (a mouse-only or
  hover-only handler with no pointer/touch equivalent) can block; its best-effort pointer/touch
  dispatch-assert runs **only when the environment can** — otherwise it is recorded as a named
  human-approved coverage-gap exclusion. A non-runnable M10 never blocks the gate.

#### Surface coverage + tiered UI proof (the denominator comes from the code)

Two real field tests went **green and still shipped broken UI** — once with full e2e, once with none.
The shared root cause was a **wrong denominator**: the verification counted the surfaces the *ticket*
named, while the failures lived on reachable surfaces it never mentioned. v0.8 fixes the axis:

- **Surface coverage.** For a universal / app-wide frontend requirement, `analysis` enumerates every
  reachable surface (route / full-window overlay / modal / major mounted state) from the **code** —
  the opt-in `sitemap` if present, else a read-only "enumerate reachable views" sub-step — and emits a
  counted, challenger-checkable `SURFACES: N`. The ticket's examples are a **hint, never the
  denominator**.
- **Elastic proof tier — e2e is optional, a proof is not.** `execute` records, per affected surface,
  the **highest available tier** in a **proof manifest**: `PASS(automated)` (tier-1, satisfying the
  **C1–C8** automated-proof contract by composing the *project's* runner — mango bundles none) →
  `PASS(render@<bp>)` (tier-2, a recorded render of the real surface at the breakpoint asserting the
  visible measurable — a **first-class proof, not an exclusion**) → `EXCLUDED` (human-approved, only
  when neither is reachable). mango **never stops for a missing runner**: it scaffolds tier-1 per
  `templates/ui-proof-scaffold.md`, else records a tier-2 render proof, else an exclusion.
- **Counted gate + loud banner.** `review`'s challenger scores the manifest (tier-1 vs C1–C8, tier-2
  vs the render-proof contract) and re-runs/confirms ≥1 proof. With `N` = |surfaces|, `M` = surfaces
  with a valid PASS (any tier), `X` = recorded exclusions, **Gate 2 passes iff `N == M + X`**;
  otherwise `design`/`review` emit `⚠ surfaces proven: k/N — <uncovered> have no proof` and block. A
  proof covering 2 of 5 reachable surfaces reads `surfaces proven: 2/5` and is blocked. Under
  `TIER=lite` the re-run lightens to confirming command/artifact presence — coverage stays mandatory.

## Supporting skills

Beyond the gated lifecycle, these skills set up, diagnose, build knowledge about, or describe a
project. They are **not** gated and do not run a ticket, so they sit apart from the lifecycle table.
(Each is also introduced in context above — *Getting set up* and *Descriptive maps* — this is the
at-a-glance index.)

| Skill | Role | Notes |
|-------|------|-------|
| `/mango:init` | Detect the stack, write `.harness.json`, scaffold a starter rule book | Marks every guessed value `UNVERIFIED`; asks whether `.harness.json` is committed or gitignored. |
| `/mango:doctor` | Setup health-check — ✅/⚠/❌ checklist with exact remediation | Prints the running version + base path as its **first line**; offline — a green doctor does not prove the intended version is loaded. |
| `/mango:codify` | Count the code + DB conventions already in use → **you choose** each standard → record it | Recorded **PROVISIONAL until you ratify**; facilitates, never authors, changes no code. |
| `/mango:sitemap` | Generate a code-surface map (routes / modules) into `docs_dir` | Opt-in; needs `code_map_cmd`. |
| `/mango:db-map` | Generate a schema map (tables / columns / keys / indexes / relations) into `docs_dir` | Opt-in; **off by default**; needs `db_kind` + (`db_introspect_cmd` or `migrations_path`). |
| `/mango:version-check` | Compare running vs latest and **print the host `/plugin` commands** | Informs only, never updates; needs `update_check_url`. |
| `/mango:budget` | Detect token optimizers, inform per the safety axis, record a human's provisional adoption in `token_optimizer` | Descriptive + human-gated (like `codify`); never installs one, never depends on one, never lets one weaken a critic. |

The `sitemap`/`db-map` outputs are **descriptive** (facts, regenerable — what the project is);
`codify` is **normative** (what it should be). mango generates the descriptive and facilitates the
normative, but never authors the normative.

### Token cost — measure before you optimize

mango records its own token cost as a **descriptive Cost ledger** in the working doc — **one row
emitted per subagent-dispatch return** (reviewer, challenger, extractor, Explore fan-out, each review
round), transcribed from that return's usage block as a **mechanical by-product of dispatching**, not
bookkeeping the model must remember (N dispatches → N rows). A dispatch retrieved by **blocking** (a
synchronous `TaskOutput`-style retrieval) carries **no `<usage>` block**, so mango first tries to
**recover** its usage (let it land as a `task-notification`, or re-query the completed task's record);
if usage truly cannot be surfaced, the cell is marked the explicit **`unmeasured (blocking retrieval)`**
— **never a silent blank, never an invented number**. `finalise` surfaces a one-line summary (total +
top cost driver) and, before it, runs a **content-completeness gate** — it refuses to proceed unless
every dispatch row is present **and** each token cell carries a value (a real count or the explicit
marker); a **blank cell blocks** like an unfilled matrix column (the ledger's teeth). It is still a
**completeness** check — the *presence* of a value or an honest marker — never inspecting, ranking, or
cutting a row. The ledger is **facts only — it never auto-cuts a check, a gate, a critic,
or evidence detail**; it makes cost visible so a *human* can decide, and is the data a later sizing
decision needs (measure before you size). It is **dispatch-scoped**: it measures **subagent dispatch
only** — main-loop output noise (verbose lint/test/build dumps, file reads) is **not measured by
mango**, so it implies no dispatch-vs-noise split; the optimizer reports its **own** savings (`rtk
gain`) for that domain. The token column is labelled plainly **`Tokens`** (a dispatch return surfaces a
single figure, so no false-precision `(out)` / in-out split).

`/mango:budget` (opt-in, like `codify`) then lets a human adopt an external token optimizer with the
safety trade-offs made explicit. **The safety axis:** an optimizer is safe only if it removes
**representation redundancy** (how output is phrased), **never** a check, a gate, a critic, or the
**evidence detail** a critic relies on (`path:line`, measured values, diffs).

- **RTK** — compresses **Bash-command output** before it enters context. Safe; sits **below** mango.
  The default `token_optimizer.rtk: "expect"` means mango **tolerates** RTK's compact output but
  **never installs or depends on it** — RTK absent, the run is **identical** (only the saving is
  lost). `doctor` may note RTK presence as one informational line; it never gates on it. When RTK is
  present **but unwired**, `budget` **prints the exact wiring command** (its `rtk init`-style hook
  setup) with a "**you must run this — it edits your global config, mango will not**" note; it never
  runs it.
- **Headroom** — input compression is safe, but its `OUTPUT_SHAPER` / effort-routing changes what the
  model writes → it **must stay OFF** (`headroom.output_shaper: false`, enforced).
- **Caveman** — terse agent output. **Never applied to critic output** (reviewer / challenger /
  gate-blocking artifact), which must retain full evidence detail; if enabled it is scoped
  **non-critic-only** (`caveman.scope: "non-critic-only"`, enforced). Terse critic output loses the
  evidence that *is* the review's value — brevity is never applied where a false-green could hide.

Adopting any optimizer is a **recorded, provisional decision** (ratified like `codify`), never a
silent toggle. `budget` **detects and informs, never self-administers.**

## Agents

All review agents are **read-only** — they produce verdicts and findings, never edits.

| Agent | Role | Model |
|-------|------|-------|
| `reviewer` | Rule-book / standards verdict on the diff (BLOCK / CHANGES REQUESTED / LGTM) | Sonnet |
| `reviewer-max` | Same role/rules/output as `reviewer`, for high-stakes diffs under `cost_tier: max` | Opus |
| `challenger` | Ticket-blind requirement reconstruction (met / not met / can't tell, with `path:line`) | Sonnet |
| `onboarder` | Wayfinding / orientation in an unfamiliar codebase | Sonnet |
| `extractor` | Bulk read-and-extract across many files (gathers context; never concludes) | Haiku |

## `.harness.json` config keys

Copy [`config/harness.example.json`](./config/harness.example.json) to your repo root as
`.harness.json`.

**Required**
- `rulebook_path` — your engineering rule book; every phase grounds its rules here.
- `repos` — array of `{name, root}` (supports multi-repo porting).
- `test_command` — the command phases use to run the proving test.
- `tracker` — `{base_url, project_key, cli, read_mcp, fields}`. **Writes go through `cli`; reads may
  use the optional read-only `read_mcp`.** Optional `fields` lists the field set to request on a read
  so one read returns the full ticket (default: description/body, type, labels, parent, priority).
- `ticket_header_schema` — maps each ticket header to `C` / `R` / `G` / `AC`.

**Optional / defaulted**
- `standards_path`, `tickets_dir` (default `docs/tickets`),
  `work_dir` (default = `tickets_dir`; holds the working doc `<KEY>.work.md` when it is a separate
  file), `work_doc_mode` (`auto|separate|embed`, default `auto`; embeds the working doc below a
  raw-ticket separator line when the ticket is itself a local repo file, else a separate file),
  `pr_checklist_path` (optional; a project-owned finalise checklist `finalise` walks before drafting
  the PR), `stuck_threshold` (default `3`; circuit-breaker for repeated failures at the same
  proving artifact), `branch_strategy` (default `fix|feat|chore/<KEY>-<slug>`), `lessons_path`,
  `pr_host`, `cause_taxonomy`, `explore_fanout` (default `true`), `cost_tier`
  (`economy|standard|max`, default `standard`).
- `token_optimizer` (optional; the human-gated record of which external token optimizers mango may
  assume — set via `/mango:budget`). Ships descriptive + human-gated with two **hard-pinned**
  invariants: `rtk: "expect"` (mango tolerates RTK's compact Bash output but never installs/depends on
  it — degrades cleanly when absent), `headroom.output_shaper: false` (never shapes critic output),
  and `caveman.scope: "non-critic-only"` (Caveman-style compression never touches reviewer / challenger
  / gate-blocking output). Enabling any optimizer is a recorded provisional decision, never a silent
  toggle.
- **Frontend-track keys (all optional):** `track` (`backend|frontend|fullstack`, default `backend`;
  selects which gate set applies — **orthogonal to TIER** — and may be inferred from touched-file
  paths when unset), `breakpoints` (optional list of viewport widths the responsive gates test; the
  320 px reflow floor is always tested on the frontend track regardless), and `design_doc_path`
  (default `DESIGN.md`; the per-project design contract the frontend rubric is scored against). With
  `track` at its `backend` default, none of the frontend gates apply and a ticket runs exactly as in
  v0.6.
- `update_check_url` (optional; raw URL to the published marketplace manifest — lets
  `/mango:version-check` compare running vs latest and print the host update commands. Unset → no
  network call).
- **Descriptive-adapter keys (all optional, off by default):** `docs_dir` (where `sitemap`/`db-map`
  write their regenerable maps), `code_map_cmd` (drives `/mango:sitemap`), and the `db-map` trio —
  `db_kind` plus either `db_introspect_cmd` (read-only schema introspection) or `migrations_path`
  (derive the schema from migration files). With these unset, the adapters report they are not
  configured and do nothing.

`rulebook_path` may be a **file or a directory**; with a directory, every consumer reads all `*.md`
inside it. Run `/mango:init` to generate this file for you.

## Operational notes

- **Plugin administration belongs to the host.** Installing, reinstalling, pinning a version, or
  reordering the install registry is done **from the host** with `/plugin` — never from a restricted
  or remote channel where `/plugin` is unavailable. mango **detects and informs; it never
  self-administers.**
- **If you find yourself working around the loader/registry from a restricted channel — stop and do
  it from the host.** mango will not install, reinstall, reorder a registry, or run `/plugin` for you.
- **Verify the live version from `doctor`'s first line**, not by assuming. `/mango:doctor` prints
  `mango <version> @ <base path>` as line 1 — a green doctor does **not** prove the version you
  intended is the one actually loaded; a stale version can run silently behind a passing preflight.
- **Use `/mango:version-check`** (if `update_check_url` is configured) to learn whether a newer
  version has been published. It reports running vs latest and **prints** the host `/plugin` commands
  to update — it does not update anything.
- **`.harness.json` commit policy is resolved at `init`, not left to vigilance.** `init` asks whether
  the config is **committed** (shared team config) or **kept local**: on "local" it adds
  `.harness.json` to `.gitignore`; on "committed" it warns that secrets never belong in it. Either
  way `init` writes no secrets into `.harness.json` — tokens live only in a gitignored `.env`.

## Cost profile

The full tier is heavier — rule-book reads, requirement re-derivation, the challenger, and (when
`explore_fanout` is `true`) read-only Explore fan-out during investigation. For small, low-stakes,
high-volume tickets use the **lite** tier (`/mango:quick`), which skips fan-out and the challenger.
Set `explore_fanout: false` to disable investigation fan-out on the full tier too.

### Model delegation

mango routes by the **nature of the task**, not the phase: *Opus decides, Sonnet executes, Haiku
gathers — and every decision or verdict is produced or ratified by the strong model; a weaker model
may only gather, never conclude.*

| Step | Model |
|------|-------|
| Orchestrator + gates, analysis judgment, design | Opus (the model you drive) |
| Review verdict + challenger reconstruction (highest judgment) | Sonnet — the `reviewer-max` agent (Opus) for high-stakes diffs under `cost_tier: max` — **never Haiku** |
| Implement the approved change list; draft PR body; Explore | Sonnet |
| Bulk read-and-extract across many files (`agents/extractor.md`) | Haiku |
| grep stray refs / run tests / lint | no model — Bash directly |

`cost_tier` shifts the dials **within** this map, never against it: `economy` pushes more bulk
retrieval to the Haiku `extractor` and avoids Opus on review; `standard` is the map above; `max`
dispatches the **`reviewer-max`** agent (Opus) for high-stakes diffs (security-tagged, or touching
auth / data access / schema migration). Since a skill cannot re-pin a subagent's model at runtime,
the Opus upgrade is a **choice of agent** (`reviewer-max` vs `reviewer`), which `review` selects
explicitly — not a runtime setting. `reviewer`/`reviewer-max`/`challenger` are never Haiku, and the
lite tier runs on a single model. The full routing map lives in [`PRINCIPLES.md`](./PRINCIPLES.md).

## Testing the harness itself

`scripts/validate.py` is the cheap, always-on guard — structural checks plus per-skill contract
tokens (it fails if a skill loses its load-bearing artifact). `tests/eval/` is the real behavioural
check: `run.sh` drives `claude -p` over fixture tickets and asserts the expected artifacts. Beyond
the analysis happy path (count line, gate count, freeform Gate-0 confirmation) it also exercises the
behaviours that matter most — proof at the risk layer (`design` flags a unit proof for an
integration-layer AC), the ticket-blind `challenger` catching an unmet AC, the design-invalidated
escalation, the stuck-detector, the frontend surface-coverage gate (a universal AC covering 2 of
5 reachable surfaces reads `surfaces proven: 2/5` and blocks; a no-runner AC yields a tier-2
`PASS(render@<bp>)`, not a silent skip), the **format-scope rule** (execute scopes the formatter
to the authored/edited files, never a wholesale reformat of a shared file), and the four v1.2
behaviours (each with its own fixture so a red run is diagnosable): a **behavioural deviation** from
the approved Gate-2 bullet is recorded despite a clean file diff; a **vague AC** is pinned to a
measurable or logged as a manual-check exclusion and cannot carry a bare `✅`; a **red baseline** —
a verification command genuinely red on a clean checkout — is **measured by running it** (not read
from the ticket) and recorded with a delta-green DoD; a **conditional LGTM** leads to a verify-only
re-review — and the four
**v1.3** budget behaviours: the **cost ledger** is descriptive (per-phase/subagent, surfaced at
finalise, never auto-cuts); an **RTK-absent** run completes identically (degrade clean); **Caveman is
forbidden on critic output** (which keeps `path:line` evidence); and enabling an optimizer is a
**recorded provisional decision**, not silent — and the five **v1.4** ledger-truth behaviours (one
fixture each): the ledger is **auto-appended** one row per dispatch return (not narrated bookkeeping);
it declares itself **dispatch-only** and refuses a fabricated dispatch-vs-noise split, pointing at the
optimizer's own `rtk gain`; a conditional-LGTM **verify-only round reuses round-1 facts** and re-runs
only the affected proof; the **Tokens column** carries no false-precision `(out)`; and with RTK
present-but-unwired **`budget` prints the wiring command** + a "you run this, not mango" note and
administers nothing — and the three **v1.5** behaviours (one fixture each): the ledger's
**dispatch-count gate** blocks finalise when the ledger has fewer rows than the run's dispatch count
(a complete ledger proceeds); the conditional-LGTM **verify-only round is main-loop-by-default** (an
in-scope round verifies in the main loop with no re-dispatch, a scope-changing fix the only
re-dispatch trigger); and a standard applied at a gate with no codified rule is **surfaced as an
uncodified-standard item** into codify's provisional→ratify flow, not silently enforced — and the four
**v1.6** honest-ledger behaviours (one fixture each): finalise's ledger gate is a
**content-completeness** check — a ledger with all rows present but a **blank token cell blocks** like
an unfilled matrix column (injected, the first non-vacuous test of the teeth), a value-or-marker in
every cell proceeds; a dispatch retrieved by **blocking** (no `<usage>`) gets its tokens **recovered**
or its cell marked the explicit **`unmeasured (blocking retrieval)`**, never a silent blank; the
verify-only re-dispatch trigger has a **docs/bookkeeping carve-out** (a fix touching only exempt
bookkeeping files stays main-loop, a non-exempt out-of-scope fix re-dispatches); and the durable lesson
must land on a **shared/pushed ref**, not an orphaned local-only branch. It costs
tokens, so CI runs it only via the manual `eval.yml`
workflow (`workflow_dispatch`, needs the `ANTHROPIC_API_KEY` secret).

**Running the eval yourself — one command, no setup.** From a fresh clone:

```
bash tests/eval/run.sh
```

It works with **either** an exported `ANTHROPIC_API_KEY` **or** an OAuth/subscription login
(`claude /login`) — the guard verifies the *capability* to run `claude -p`, not a specific
credential, and fails only (naming both options) when neither works. The script sets up its own
throwaway environment (an isolated local clone + a temp `.harness.json` + a minimal rule book), runs
the fixtures against the **shipped** skills via `--plugin-dir`, and tears it all down on exit — your
working tree is never touched. It prints the `PASS`/`FAIL` lines and a final `N/N assertions pass`,
exiting non-zero if any assertion fails. Assertions are matched at the **decision level** and are
**emphasis-agnostic** (tolerant of markdown `**`/`_` and phrasing variants around the load-bearing
token): a correct behaviour passes under any wording, a wrong *outcome* always fails — so a green
result reflects stability across independent fresh runs, not a regex tuned to one transcript.

## First run

```
# 1. install (see the marketplace README)
# 2. in your project:
cp <plugin>/config/harness.example.json .harness.json
#    edit .harness.json — rulebook_path, repos, test_command, tracker, ticket_header_schema
# 3. start a ticket:
/mango:solve PROJ-123
```

If `.harness.json` is missing, every skill stops and tells you to create one from the example.
