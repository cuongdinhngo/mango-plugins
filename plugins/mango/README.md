# mango

A portable, **gated ticket-lifecycle harness** for Claude Code. mango ships the *machinery* — a Phase-0
`refine` phase, five gated lifecycle phases, read-only review agents, and a working-doc template — and
reads every project-specific rule at runtime from a per-project `.harness.json`. The same plugin
installs into any project unchanged.

**Harness, not rules.** No stack assumptions are baked in (no framework, language, database, or
region). Your rule book, repos, test command, tracker, and ticket schema all live in `.harness.json`.
Trust comes from emitted, counted, gate-blocking artifacts — not prose. mango generates the
descriptive and facilitates the normative, but **never authors the normative** — the rules stay your
team's decision. No secrets ship: tokens live only in a gitignored `.env`.

## Quickstart

```
# 1. install (see the marketplace README)
# 2. in your project:
cp <plugin>/config/harness.example.json .harness.json
#    edit .harness.json — rulebook_path, repos, test_command, tracker, ticket_header_schema
#    (or run /mango:init to generate it for you)
# 3. start a ticket:
/mango:solve PROJ-123
```

If `.harness.json` is missing, every skill stops and tells you to create one from the example.

## Key ideas

A few terms recur throughout; here they are once.

- **Gate** — a ✋ stop where mango waits for your approval. Silence is never approval.
- **Requirements matrix (C/R/G/AC)** — every ticket line classified as **C**ontext, **R**equirement,
  **G**oal, or **A**cceptance **C**riterion, and counted so nothing goes unnamed.
- **Proving test** — the test that demonstrates the requirement is met, named at the *matching layer*.
- **Layer-match** — a requirement's risk layer (unit / integration / runtime) must be proven at that
  layer. A runtime AC "proven" only by a unit test against a mock is a mismatch and blocks the gate.
- **BASELINE** — the verification command's result on the *untouched* checkout (`green | red | flaky`).
  If it isn't green, the definition of done becomes **delta-green** (fix what you touched, don't claim
  the whole suite green).
- **challenger** — a ticket-blind agent that reconstructs the requirements from the diff alone and
  reports met / not met / can't tell. It never sees the ticket, so it can't rubber-stamp.
- **TIER** — process weight (`lite | full`); **track** — which gate set (`backend | frontend`).
  Orthogonal.

## Getting set up

| Skill | Use | Produces |
|-------|-----|----------|
| `/mango:init` | Once per project | Detects the stack read-only, interviews only for the undetectable, writes `.harness.json` (guesses marked `UNVERIFIED`), asks whether it is committed or kept local, and scaffolds a starter rule book if none exists. |
| `/mango:doctor` | Anytime / before a run | A ✅/⚠/❌ health check of `.harness.json` with exact remediation, prefaced by `mango <version> @ <base path>`. `solve` runs it as a fail-fast preflight. |
| `/mango:codify` | When the rule book is missing / thin (opt-in) | **Counts** the conventions the code and schema actually use, asks **you** to choose each standard, and writes them tagged `PROVISIONAL (awaiting ratification)`. Any drift list carries the counted line `DRIFT: <n> entries \| <m> tickets` (counted from the list, never narrated). Facilitates; never auto-picks the majority, never changes code. |
| `/mango:version-check` | On demand (opt-in) | Reports running vs latest version and **prints** the host `/plugin` commands to update. Needs `update_check_url`; never updates. |
| `/mango:promote` | Between tickets, once a lesson class recurs (opt-in) | Groups **type-2** claims in `lessons_path` by their `handle:`, and for each class seen on **≥ 2 tickets** proposes **one** candidate rule citing every instance, then **stops for a per-candidate ratify**. Emits `PROMOTE: … \| rules written: 0`. Cross-ticket by design — a single ticket's `finalise` cannot see across tickets. Proposes; never authors a rule, never touches a mango file. |

**Where mango's own contract lives.** `plugins/mango/PRINCIPLES.md` is the always-loaded core — the four
principles, the `<mango>` path-resolution order, and the model-delegation map. The rest of the contract sits
in `plugins/mango/principles/*.md`, each file read **on demand** by the phase that applies it under an
explicit read instruction in that skill, so a run pays only for the contract it actually uses. Each skill's
frontend-only rules likewise live in `skills/<name>/frontend.md`, read when `config.track` includes
frontend. Every mango-shipped path resolves through the documented order — `${CLAUDE_PLUGIN_ROOT}` when the
host sets it, else the plugin root located from the loaded skill file, else a read-only search — so no
shipped file depends on one host variable.

`init` gives you a skeleton rule book with TODOs; `/mango:codify` is the deeper facilitation for a
project with no rule book, a thin one, or inconsistent conventions. It observes and counts the
patterns (presenting "pattern A: 12 files, B: 5" as **data**, not a verdict), asks you to pick each
standard, and records the choices as provisional until you ratify them.

### Descriptive maps (opt-in, stack-specific)

Two opt-in adapters generate **descriptive facts** (regenerable, falsifiable). They are off unless
configured and are **not** part of the lifecycle, which runs fully whether or not either has been
generated.

| Skill | Use | Produces | Needs |
|-------|-----|----------|-------|
| `/mango:sitemap` | Map the code surface | Routes/endpoints + modules, into `docs_dir` | `code_map_cmd` + `docs_dir` |
| `/mango:db-map` | Map the database schema | Tables, columns+types, keys, indexes, relationships, views/procs, into `docs_dir` | `db_kind` + (`db_introspect_cmd` **or** `migrations_path`) + `docs_dir` |

A generated `db-map`, if present, lets `analysis` widen the Phase-1 blast radius to schema dependents
(columns, FKs, dependent views/procs) — used if present, never required. The *normative* database
conventions live in the `codify` rule book, not in these maps.

## The lifecycle

Run the whole thing with `/mango:solve`, or invoke a phase directly. mango stops and waits at every ✋
gate. The lifecycle is:

```
refine → analysis → design → execute → review → finalize                       (ticket path)
refine → analysis(epic) → design(epic) → breakdown → N× ticket-lifecycles       (epic path)
```

### Phase 0 — `refine` (expose the decisions, never author the intent)

A raw request rarely arrives lifecycle-ready. **`refine`** (the first phase) scans the project (reusing
`sitemap`/`db-map`) and **tries to expose the unresolved product-decisions** — and the count it finds
**is** the gate:

**0 → self-skip → analysis** (recorded, so refine is never a tax on a clear ticket),
**≥1 → refine works**, **when in doubt → run**. It classifies **every** decision before asking:

- **how-decision (HOW)** — answerable from convention / code / the rule book / the ticket text, or a
  tool choice → refine **resolves it and cites** the source, and **does not ask** (asking a
  HOW-question launders a decision; an **uncited** how-decision resolution is itself a finding).
- **want-decision (WANT)** — intent / priority / stakes / a genuinely new choice → refine **asks you**
  in want-language. **Tie-breaker: a decision about the acceptance BAR itself (what counts as done / a
  threshold / a sourcing standard) is a want-decision by default, even when it looks derivable — you
  own the bar.** A handed-back want-decision ("your call") **must** be marked **`ASSUMED (awaiting
  ratification)`** and requires an **explicit next-gate confirm**; a tripwire fires if it would reverse
  a prior human decision.

**Premise first — a ticket whose named sources do not exist halts instead of digging.** The scan's first
act is to resolve every source the ticket references **as already existing**, wherever a grep can decide
it: a **path, file, symbol, config key, table, route**. A **prose noun** ("the dashboard banner") is not
a resolvable reference — it is **surfaced as ambiguous**, never a halt — and a path the ticket frames as
**to be created** never counts as missing. A referenced-as-existing identifier that does not resolve
emits `PREMISE FALSIFIED: <n> … missing — <ref>` and **stops for you immediately**: no hunting for a
renamed equivalent, no history reconstruction, no guessing what the ticket meant. Every run emits
`PREMISE: <r> checked | <m> missing | <a> ambiguous`, zero included.

refine stops at solution **DIRECTIONS** (wrap vs rebuild), never the specific tool — that is analysis's
job. Its completeness backstop is the **ticket-blind challenger as a 1-dispatch exposure-checker**, not
a debate — and it runs on **both paths**: on an epic it dispatches **before `breakdown`**, so the epic
(costliest place for an un-exposed decision) is never the one path that skips the backstop. It holds **no gate of its own** — its want-decision questions are its interaction and its
output is challenged at Gate 1. **refine exposes for you to decide; it never authors intent** (the same boundary
`codify` holds for rules). An **epic** input routes to the epic path (below).

### Tiers — right-sizing the rigor

`analysis` declares `TIER: lite | full`. **Lite** is chosen only when ALL hold: `SCOPE=S`, a single
file / requirement, no universal requirement **with N > 1**, and not security-tagged — otherwise
**full**. The decision keys on the **resolved denominator N**, not keywords: a requirement that
*sounds* universal but resolves to one site (**N = 1**) is lite-eligible. Lite routes through
`/mango:quick` (one combined pre-code gate + the final gate, reviewer-only, no challenger, no matrix,
no fan-out); full keeps the five-phase flow. `/mango:quick <KEY>` forces the lite lane but runs a
**hard entry check** first and **refuses** — routing to `/mango:solve` — if the ticket is
security-tagged, touches more than one file, or has a universal requirement resolving to N > 1.

| Skill | Phase / Gate | Produces |
|-------|--------------|----------|
| `/mango:refine` | 0 (no gate of its own) | A **refined ticket** as counted artifacts: a `REFINE:` count line + tables for **settled wants** (want-decision → AC constraints), **cited** (how-decision → starting premise), **ASSUMED (awaiting ratification)** (mandatory tag + explicit next-gate confirm), and scan-surfaced constraints. Applies the acceptance-bar tie-breaker (bar decisions → want-decision by default). Self-skips a clear ticket (records "0 unresolved product-decisions"). Runs a 1-dispatch ticket-blind exposure-checker. Detects an epic and routes to the epic path. Surfaces past claims as **advisory recall** (`RECALL:` — type 1 by symbol, type 5 by area, type 6 by the re-raised finding; `retired:` skipped) which never injects a requirement and never blocks. |
| `/mango:analysis` | 1 → Gate 1 | Requirements matrix (C/R/G/AC) with counts, falsifiable-AC check (a value that is neither falsifiable nor a recorded manual-check exclusion is flagged and may not carry `✅`), root-cause & blast radius, a `RULE SECTIONS` coverage line (applicable rulebook sections derived from the change type — migration → DB-conventions mandatory, etc. — each checked or N/A), scope, and a `BASELINE` capture from the untouched checkout. A ratified **multi-clause** want-decision is split into **one matrix + proof row per clause** (a clause with no row of its own is a finding). Frontend: emits `SURFACES: N` for universal requirements. Surfaces any **uncodified standard** into `codify`'s provisional→ratify flow rather than enforcing it silently. |
| `/mango:design` | 2 → Gate 2 | Approach + rejected alternatives, assumptions (`verified \| novel-untested`), smallest row-traced change list, rule compliance, the named proving test, and a **per-AC verification plan whose layer-match is a hard gate** (an integration/runtime AC backed only by a logic-layer proof blocks Gate 2 unless upgraded or recorded as a human-approved coverage-gap exclusion). Its **test blast-radius traces to real producers/consumers** — a shared type/symbol change enumerates every test root + factory patterns + `typecheck`, a threaded value enumerates every builder call site — so the change-list is the smallest **complete** set and a shallow name-grep miss is a finding. Frontend: builds/updates `DESIGN.md`, plans one row per (AC × surface). |
| `/mango:execute` | 3 (autonomous) | Branch, the approved changes only, the proving test, a verification sweep on **both axes** — file set (diff ⊆ approved list) **and** a design-conformance self-check that records any deviation from a Gate-2 bullet even when the diff is clean — with a baseline-aware DoD, commits carrying no AI co-author trailer. Formats **only authored/edited files**. **Commits the change-set BEFORE review is dispatched**, so the ref-based review sees a real committed diff. STOPs to re-gate on an invalidated design or via a **stuck-detector** (`stuck_threshold` failed attempts at the same signature). Frontend: emits the proof manifest. |
| `/mango:review` | 4 (stop if not clean) | `reviewer` + ticket-blind `challenger`, scope reconciliation on both axes (file set **and** behavioural conformance), regression check, layer-match re-confirmation, proving-test result judged against `BASELINE`, `k/N` coverage. A round-1 **conditional LGTM** makes the re-review a **verify-only pass** (named-fix check + affected proof + regression scan, no full re-derivation), re-dispatching a subagent only when a fix changed scope. Frontend: also scores the M1–M10 rubric + `N == M + X` surface check. On a clean verdict records a `Reviewed at <sha>` marker for the stale-review guard. Subagents inspect **ref-based or worktree-isolated**; a worktree used to *run* a suite must **carry the untracked env** (or run in place at the reviewed SHA), and a **near-total** worktree failure is an **env-fault, not a finding**. An **empty** `<base>..<branch>` range falls back to `git diff HEAD` + `git status --porcelain -uall` before concluding no-change. |
| `/mango:finalise` | 5 → final gate | **Stale-review guard** (routes back to `review` only if a source file changed beyond the reviewed set), optional `pr_checklist_path` walk, PR draft, per-action approval for every outward action, tracker writes via CLI, a **cost-ledger completeness gate**, follow-up tickets for deferred rows, and a **durable lesson** captured to `lessons_path` and pushed to a shared ref — then the **learning loop** on it: split into atomic claims → classify (a proposal) → recurrence/supersession → a **falsification check in front of** the ratification gate → each promotion **proposed** into a **project** file and ratified per claim. No lesson edits a mango skill. |
| `/mango:quick` | lite lane | Single combined pre-code gate → execute → reviewer-only check → final gate, for trivial tickets. |
| `/mango:breakdown` | epic path (after design(epic)) | Splits an epic into tickets from the thin epic-level architecture: a **counted** ticket list with a per-ticket **enumerated six-letter INVEST** self-check (each of Independent/Negotiable/Valuable/Estimable/Small/Testable affirmed or N/A — a one-liner is a finding; a ticket failing a letter is flagged for **re-split**), held at a **✋ human gate** — the human ratifies the split before any ticket executes. Each ratified ticket then runs its own full lifecycle. **Boundary sizing is corrected by retro; the re-ratification behaviour is Experimental.** |
| `/mango:solve` | orchestrator | Runs `refine` (Phase 0) FIRST and branches — **skip** / **ticket-refine** / **epic-path** — then a Doctor preflight and every gated phase in order honouring `TIER`, holding each gate; resumes from `Session status`. Raises an **"outgrew its ticket" nudge** — if realized scope crosses up a tier (S/M → L) or the diff materially exceeds the approved list, it stops to re-scope or split. |

### Epic path — thin by design

When `refine` detects an **epic** (the exposed work spans multiple independent, each-execute-able
deliverables), the run takes the epic path: **`analysis(epic)` → `design(epic)` → `breakdown` → N×
ticket-lifecycles**. The epic-level analysis/design are **deliberately thin** — architecture-level, only
enough to draw ticket boundaries — and `breakdown` emits a counted ticket list (per-ticket **enumerated
six-letter INVEST**; a ticket failing a letter is flagged for re-split) behind a human split-gate. The
epic path is **not exempt from the exposure backstop** — refine dispatches the same 1-dispatch
ticket-blind exposure-checker **before `breakdown`**, its findings ratified alongside the split. This
whole branch is **thin by design (only enough to split)**: ticket-boundary sizing has no exact
metric, INVEST is the heuristic, and retro corrects mis-splits. A ratified breakdown is a **living
plan**: if the split changes after the gate (a ticket added/removed, or a ratified decision reversed),
`breakdown` **re-ratifies** — surfacing the delta for an explicit human re-approve rather than letting
it ride in on a child's Gate 1 (this re-ratification behaviour is **Experimental** — see
[Maturity](#maturity)) — and it **commits the epic scaffold** (child stubs + BACKLOG) to a shared ref
**before any child ticket branches**, so a child's edit reads as an edit of a committed file (preserving
the ticket-blind challenger's evidence).

For committed-stub tickets — the child-ticket stubs the epic scaffold commits — prefer
`work_doc_mode: separate` (a distinct `<KEY>.work.md`) over `auto`/`embed`: embedding the mutable
working doc inside a committed, tracked stub leaves its edits as uncommitted changes to a tracked file,
which is fragile to any stray subagent git-state operation. A separate working doc avoids that.
`solve` routes that shape to `separate` **even under `auto`** and records the resolved mode in
`Session status`.

An epic **ends at `breakdown`** and never reaches `finalise`, so `breakdown` also **owns the epic's
durable lesson**: at ratification (and after any re-ratification) it writes the split rationale, the
overlap/boundary rulings, any forced INVEST re-split, and each re-ratification delta to
`config.lessons_path`, emitting the counted line `EPIC LESSON: <n> lesson(s) written to …`.

### Subagent git isolation — refs or a worktree, and the worktree needs the env

A review subagent inspects a branch **read-only and ref-based** (`git diff <base>..<branch>`,
`git show <branch>:<path>`, `git log <base>..<branch>`) or in an **isolated `git worktree`** it removes
afterward. It **never** runs `git checkout` / `git switch` / `git stash` in the shared working tree.

A fresh worktree holds only **tracked** files, so it is **not environment-equivalent**: without the
project's untracked `.env` / local config the app cannot boot and *every* test fails for an
environmental reason. To run a suite, either **run read-only in place** when the tree is already at the
reviewed SHA, or **carry the required untracked env into the worktree** first. A **near-total** failure
inside a fresh worktree is an **env-fault until proven otherwise** — fixed and re-run, never reported as
a finding or a regression. A *partial, targeted* failure inside the change's blast radius is still a real
finding; the rule reclassifies an environment artifact, it never suppresses a finding.

`execute` **commits the change-set before review is dispatched**, so a real committed diff exists for
that ref-based read. If a `<base>..<branch>` range still comes back **empty**, the change may be
**uncommitted**: each critic falls back to `git diff HEAD` + `git status --porcelain -uall` before
concluding no-change.

### Maturity — Stable vs Experimental

Shipped behaviour carries an honest maturity level (defined in [`PRINCIPLES.md`](./PRINCIPLES.md)):
**Stable** = committed, field-tested behaviour, safe to rely on (the default); **Experimental** = works
and is validated, but its exact shape may still change until further real-world use. Two behaviours are
Experimental today: **breakdown re-ratification**, and the **learning loop's classification/promotion
machinery** (where the six-type boundaries fall, which recall key each type gets, how recurrence is
scored) — though the loop's **five invariants are not Experimental**: the classifier proposes and the
human confirms, recall is advisory, falsification precedes ratification, lessons never modify mango, and
everything is project-local. Everything else on the ticket and epic paths is Stable. When an Experimental
behaviour graduates, the CHANGELOG records it (e.g. `re-ratification: Experimental → Stable`).

### Skills are directive-only

Skill text is runtime-loaded and **is** behaviour (prose-IS-behaviour), so every token of a `SKILL.md`
is paid on every ticket run. A skill therefore carries **directives only** — no rationale, no "observed
failure" war-stories, no historical justification. When a lesson motivates a rule, the **rule** goes in
the skill and the **reason** goes in [`CHANGELOG.md`](./CHANGELOG.md), with the incident recorded in
[`RATIONALE.md`](./RATIONALE.md) — a file **no skill loads at runtime**. Enforced by
`scripts/validate.py`; see [`PRINCIPLES.md`](./PRINCIPLES.md) → *Skills are directive-only*.

The four binding principles are in [`PRINCIPLES.md`](./PRINCIPLES.md): think before coding, simplicity
first, surgical changes, goal-driven execution. Per-version changes are recorded in the shipped
[`CHANGELOG.md`](./CHANGELOG.md) — the neutral source an independent field retro reads.

### The learning loop — recall, propose, never self-modify

A durable lesson used to sit in `lessons_path` and be re-read by nobody. The loop makes it act on the
next ticket — **without** mango ever changing itself. Full contract in
[`PRINCIPLES.md`](./PRINCIPLES.md) → *The learning loop*.

```
finalise: lesson → split into atomic CLAIMS → classify (a PROPOSAL, 6 types) → recurrence / supersession
             → FALSIFY (still true? cheaply checkable? checked, or only repeated?) → propose promotion
             → ✋ HUMAN RATIFIES, per claim → a PROJECT file
refine/analysis: advisory RECALL — type 1 by symbol, type 5 by area, type 6 by the re-raised finding
```

- **The unit is the atomic claim, not the entry.** A bundled lesson classified as one thing routes its
  other halves wrong, so `finalise` splits it first and emits `CLAIMS: <c> claim(s) from <e> entr(ies) |
  T1=… T6=… | <u> unclassified`.
- **Six types decide the destination and the recall key:** 1 tool-constraint (stays in `lessons_path`,
  recalled by **symbol**), 2 heuristic (`rulebook_path` for code, `agent_brief_path` for process),
  3 skill-gap **signal** (`skill_gap_path`), 4 world-fact (`gotchas_path`), 5 project ground-truth
  (recalled by **area**; descriptive → `design_doc_path`, normative → a rule-book entry with ID +
  blocking, environment → a `verified-at:` stamp), 6 adjudicated non-defect (`drift_path`, with an
  `expiry:`, recalled by the finding it pre-empts).
- **Recall is advisory, and that is all it is.** It surfaces claims at `refine`/`analysis` with
  `RECALL: <n> surfaced | … — advisory (blocks nothing)`; it never injects a requirement, adds a matrix
  row, blocks a gate, or edits a file. A `retired:` claim is skipped (a human retires it; no auto-retire).
- **Falsification sits in FRONT of the ratification gate.** Recurrence measures how often a claim was
  *restated*, not whether it was ever *checked* — the most-repeated lesson can be the false one. A
  recurring claim that is falsified, or that cannot be cheaply checked, is **blocked from promotion** and
  stays a lesson.
- **Every promotion is human-ratified and lands in a PROJECT file.** The rule goes into
  `rulebook_path` (via `codify`'s provisional→ratify), **never copied into `CLAUDE.md`** — `CLAUDE.md`
  carries only the pointer `init` wrote, and the promotion is not done until `doctor` is green on it.
- **Lessons never modify mango.** No lesson — however recurrent, however ratified — edits a mango skill.
  A type-3 skill-gap is a **signal** for mango's maintainer, who changes mango through a normal version.
  `PROMOTION: … | mango files written: 0` is the falsifiable form of that rule.

### Frontend track — measurable UI gates, composed taste

`config.track` (`backend|frontend|fullstack`, default `backend`) selects the gate set, orthogonal to
TIER, so a ticket may be `track=frontend` + `TIER=lite`. `analysis` emits a counted `TRACK` artifact
the challenger can check. A `track=backend` ticket runs with none of the gates below.

**Own the durable, compose the volatile.** mango embeds only UI knowledge that is durable +
falsifiable — a11y thresholds it can *measure*, token-first it can *grep*, conformance to a
per-project **`DESIGN.md`** contract. It composes, never owns, the aesthetic layer: it calls an
external taste skill if installed, else follows `DESIGN.md`, and never stops because a taste skill is
missing. mango blocks on a missing *number*, never a missing aesthetic. Breakpoint values, the
narrow-width navigation pattern, and which regions collapse vs reflow are *choices* → they live in
`DESIGN.md`.

- **`DESIGN.md` contract** (built by `design` from `templates/design-doc.md`): palette
  domain-meaning-first; a **shell** (character-rich) vs **data-core** (legibility-first, static) split;
  and a **Responsive & touch** section (breakpoints, narrow-width navigation, collapse vs reflow vs
  scroll, thumb-zone, motion).
- **Falsifiable rubric** (`templates/frontend-rubric.md`, injected into the reviewer/challenger
  brief): every item is measurable or greppable and scored **against `DESIGN.md`**; "is it tasteful?"
  is out of scope. Core items (token-first, no hardcoded hex/px, semantic HTML,
  state-not-by-colour-alone, `prefers-reduced-motion`) plus the **M1–M10** responsive/touch gates:

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

  Constants (44/24 px, 16 px, 4.5:1, 320 px) are **standards** → fixed, not config. M10 degrades
  gracefully: its greppable smell (a mouse/hover-only handler with no pointer equivalent) can block,
  but its runtime pointer-dispatch assert runs only when the environment can — otherwise it is a named
  coverage-gap exclusion and never wedges the gate.

#### Surface coverage — the denominator comes from the code

For a universal / app-wide frontend requirement the failure usually hides on a reachable surface the
*ticket* never named. So `analysis` enumerates every reachable surface (route / overlay / modal /
major mounted state) from the **code** (the opt-in `sitemap` if present, else a read-only enumeration)
and emits a counted `SURFACES: N`; the ticket's examples are a hint, never the denominator.

`execute` records, per surface, the **highest available proof tier** in a **proof manifest**:
`PASS(automated)` (tier-1, satisfying the C1–C8 contract by composing the project's runner — mango
bundles none) → `PASS(render@<bp>)` (tier-2, a recorded render at the breakpoint asserting the visible
measurable — a first-class proof, not an exclusion) → `EXCLUDED` (human-approved, only when neither is
reachable). **e2e is optional, a proof is not**, and mango never stops for a missing runner. With `N`
surfaces, `M` proven (any tier), `X` exclusions, **Gate 2 passes iff `N == M + X`**; otherwise
`review` emits `⚠ surfaces proven: k/N` and blocks. Under `TIER=lite` the re-run lightens to
confirming proof presence — coverage stays mandatory.

## Supporting skills

Beyond the gated lifecycle, these skills set up, diagnose, build knowledge about, or describe a
project. They are **not** gated and do not run a ticket.

| Skill | Role | Notes |
|-------|------|-------|
| `/mango:init` | Detect the stack, write `.harness.json`, scaffold a starter rule book | Marks every guessed value `UNVERIFIED`; asks whether `.harness.json` is committed or gitignored. |
| `/mango:doctor` | Setup health-check — ✅/⚠/❌ checklist with remediation | Prints running version + base path as its **first line**; a green doctor does not prove the intended version is loaded. |
| `/mango:codify` | Count the code + DB conventions in use → **you choose** each standard → record it | Recorded **PROVISIONAL until you ratify**; facilitates, never authors, changes no code. |
| `/mango:sitemap` | Generate a code-surface map into `docs_dir` | Opt-in; needs `code_map_cmd`. |
| `/mango:db-map` | Generate a schema map into `docs_dir` | Opt-in, off by default; needs `db_kind` + (`db_introspect_cmd` or `migrations_path`). |
| `/mango:version-check` | Compare running vs latest and print the host `/plugin` commands | Informs only, never updates; needs `update_check_url`. |
| `/mango:budget` | Detect token optimizers, inform per the safety axis, record a human's provisional adoption | Descriptive + human-gated (see [Cost & models](#cost--models)). |
| `/mango:promote` | Cross-ticket promotion of a **recurring** type-2 heuristic into a *proposed* project rule | Opt-in, off the lifecycle; entry condition is **recurrence ≥ 2**, not a schedule. Idempotent: a re-run on an unchanged corpus proposes nothing. Needs `lessons_path` plus `rulebook_path` (code) or `agent_brief_path` (process). |

The `sitemap`/`db-map` outputs are **descriptive** (what the project is); `codify` is **normative**
(what it should be). mango generates the descriptive and facilitates the normative.

## Agents

All review agents are **read-only** — they produce verdicts and findings, never edits.

| Agent | Role | Model |
|-------|------|-------|
| `reviewer` | Rule-book / standards verdict on the diff (BLOCK / CHANGES REQUESTED / LGTM) | Sonnet |
| `reviewer-max` | Same role, for high-stakes diffs under `cost_tier: max` | Opus |
| `challenger` | Ticket-blind requirement reconstruction (met / not met / can't tell, with `path:line`) | Sonnet |
| `onboarder` | Wayfinding / orientation in an unfamiliar codebase | Sonnet |
| `extractor` | Bulk read-and-extract across many files (gathers context; never concludes) | Haiku |

## `.harness.json` config keys

Copy [`config/harness.example.json`](./config/harness.example.json) to your repo root as
`.harness.json`.

**Required**
- `rulebook_path` — your engineering rule book; every phase grounds its rules here. May be a **file or
  a directory** (a directory → every consumer reads all `*.md` inside).
- `repos` — array of `{name, root}` (supports multi-repo porting).
- `test_command` — the command phases use to run the proving test.
- `tracker` — `{base_url, project_key, cli, read_mcp, fields}`. Writes go through `cli`; reads may use
  the optional read-only `read_mcp`.
- `ticket_header_schema` — maps each ticket header to `C` / `R` / `G` / `AC`.

**Optional / defaulted**
- `context_file` — the **host's always-on context file**, the one your coding host auto-loads into every
  session (default `CLAUDE.md`). `init` hoists its `mango:standing-context` **pointer** block into this
  file and `doctor` checks this file. On a host that loads `AGENTS.md` instead (a project may keep a
  `CLAUDE.md` that only imports it), set it to `AGENTS.md` — or leave it unset and `init`/`doctor` will
  detect the import and target the file the host actually loads. Still a pointer, never a copy, never a
  secret.
- `standards_path`, `tickets_dir` (default `docs/tickets`), `work_dir`, `work_doc_mode`
  (`auto|separate|embed`, default `auto`), `pr_checklist_path`, `stuck_threshold` (default `3`),
  `branch_strategy` (default `fix|feat|chore/<KEY>-<slug>`), `lessons_path`, `pr_host`,
  `cause_taxonomy`, `explore_fanout` (default `true`), `cost_tier` (`economy|standard|max`, default
  `standard`).
- `token_optimizer` — the human-gated record of which optimizers mango may assume (set via
  `/mango:budget`). Ships with hard-pinned invariants: `rtk: "expect"`,
  `headroom.output_shaper: false`, `caveman.scope: "non-critic-only"`.
- **Frontend-track keys (optional):** `track` (default `backend`; may be inferred from touched-file
  paths), `breakpoints` (the 320 px reflow floor is always tested regardless), `design_doc_path`
  (default `DESIGN.md`).
- `update_check_url` — raw URL to the published manifest; lets `/mango:version-check` compare versions.
  Unset → no network call.
- **Descriptive-adapter keys (optional, off by default):** `docs_dir`, `code_map_cmd`, and the
  `db-map` trio (`db_kind` + `db_introspect_cmd` or `migrations_path`).
- **Learning-loop destinations (optional; every one a path in YOUR repo):** `skill_gap_path` (type-3
  skill-gap **signals** for mango's maintainer — nothing here edits a mango skill), `gotchas_path`
  (type-4 world-facts), `drift_path` (type-6 adjudicated non-defects, each carrying an `expiry:` — also
  `codify`'s drift list), `agent_brief_path` (a **project-owned** process brief: the destination for a
  process heuristic, which must never be filed in the code rule book — it is *not* one of mango's own
  `agents/*.md`). Unset → the loop reports the destination as not configured and surfaces the claim
  rather than dropping it. See [the learning loop](#the-learning-loop--recall-propose-never-self-modify).

Run `/mango:init` to generate this file for you.

## Cost & models

### Tier weight

The full tier is heavier — rule-book reads, requirement re-derivation, the challenger, and (when
`explore_fanout` is `true`) read-only Explore fan-out. For small, low-stakes, high-volume tickets use
the **lite** tier (`/mango:quick`), which skips fan-out and the challenger. Set `explore_fanout: false`
to disable investigation fan-out on the full tier too.

### Model delegation

mango routes by the **nature of the task**, not the phase: *Opus decides, Sonnet executes, Haiku
gathers — every decision or verdict is produced or ratified by the strong model; a weaker model may
only gather, never conclude.*

| Step | Model |
|------|-------|
| Orchestrator + gates, analysis judgment, design | Opus (the model you drive) |
| Review verdict + challenger reconstruction | Sonnet — `reviewer-max` (Opus) for high-stakes diffs under `cost_tier: max` — **never Haiku** |
| Implement the approved change list; draft PR body; Explore | Sonnet |
| Bulk read-and-extract across many files (`extractor`) | Haiku |
| grep stray refs / run tests / lint | no model — Bash directly |

`cost_tier` shifts the dials within this map: `economy` pushes more bulk retrieval to Haiku and avoids
Opus on review; `standard` is the map above; `max` dispatches `reviewer-max` (Opus) for high-stakes
diffs (security-tagged, or touching auth / data access / schema migration). The full routing map lives
in [`PRINCIPLES.md`](./PRINCIPLES.md).

### Token ledger — measure before you optimize

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

## Operational notes

- **Plugin administration belongs to the host.** Installing, reinstalling, pinning a version, or
  reordering the registry is done from the host with `/plugin` — never from a restricted or remote
  channel. mango detects and informs; it never self-administers.
- **Verify the live version from `doctor`'s first line**, not by assuming — a stale version can run
  silently behind a passing preflight. Use `/mango:version-check` (if configured) to learn whether a
  newer version has been published.
- **`.harness.json` commit policy is resolved at `init`**: it asks whether the config is committed
  (shared) or kept local (gitignored). Either way it writes no secrets.

## Contributing

`scripts/validate.py` is the cheap, always-on guard; `tests/eval/` is the behavioural eval that drives
`claude -p` over fixture tickets — each fixture inside a throwaway clone, with a post-run guard that
asserts the live checkout is untouched. Both are documented in
[CONTRIBUTING.md](../../CONTRIBUTING.md).
