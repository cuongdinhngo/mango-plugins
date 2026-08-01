# PRINCIPLES.md — the binding contract

**A principle stated as prose does not bind; an emitted, counted artifact that blocks a gate
does.** Every mango skill references this file. A phase may not pass its gate until the artifacts
named below exist, are filled, and pass their own count/match checks. Silence is never approval.

The four principles follow. Each lists its **Operating rule**, where it is **Enforced at**, and
exactly when it **Fails the gate**.

---

## 1. Think before coding

**Operating rule.** Understand the ticket completely before proposing any change. Every section is
decomposed; every concrete acceptance value is independently re-derived; every ambiguity is raised,
not guessed.

**Enforced at** (analysis → Gate 1):
- The `CLARIFICATION: <M> raised | <k> self-resolved (cited) | <j> for human decision` tally.
  If `j > 0`, STOP at Gate 0 — do not proceed.
- The `AC validation` table: every concrete acceptance value is recomputed independently. A
  mismatch becomes a Gate-1 question carrying the computed value — **never a silent correction**.
- **Falsifiable-or-excluded acceptance values.** Every acceptance value is either **falsifiable** (a
  measurable/greppable definition — not a vague adjective) **or** a recorded **manual-check
  exclusion** (unmeasurable → human-verified, logged up front as a coverage-gap exclusion). One that
  is **neither** is flagged at Gate 1 and **may not carry a matrix `✅`** — a bare self-reported `✅`
  cannot stand in for an unmeasurable or unbuilt thing.
- `SECTIONS: <n> found = <n> decomposed`. Every ticket section maps to ≥1 matrix row.
- **`RULE SECTIONS` coverage by change type.** analysis derives the applicable rulebook sections
  **from the change type** (migration/schema → the DB-conventions section is mandatory; new UI surface
  → the design-token/a11y section is mandatory; …) and checks **each** — or marks it N/A-with-reason.
  An applicable section left neither checked nor N/A is a finding (silently omitting the section that
  mattered is the miss this removes). Detect-and-surface only — mango never authors the rule.
- A `Rejected alternatives` line at design records what was considered and dropped.

**Fails the gate when** a gate is reached with `j > 0` unresolved, an AC mismatch was silently
changed instead of raised, sections found ≠ sections decomposed, an applicable rulebook section is
neither checked nor N/A-with-reason, or a vague acceptance value carries a `✅` without being pinned to
a measurable or recorded as a manual-check exclusion.

> **Challenger independence is procedural, backed by a path separation — not cryptographic.** The
> working doc lives at `<config.work_dir>/<KEY>.work.md`, a **separate path** from the ticket spec,
> so the orchestrator can build the challenger's input from the re-fetched raw ticket + diff and
> simply leave the `.work.md` out. The "ticket-blind" property still holds only because the
> orchestrator upholds that withhold-and-re-fetch discipline — nothing cryptographically prevents a
> leak. Treat it as a discipline backed by structure, and state the limit honestly rather than
> overclaiming guaranteed independence.

---

## 2. Simplicity first

**Operating rule.** Build the smallest thing that satisfies the requirements. No speculative
abstraction; no indirection that serves a single call site.

**Enforced at** (design → Gate 2; review → Gate 4):
- The **smallest change-list** table plus a declared `SCOPE: S|M|L`.
- Every change-list item traces to a matrix row (the `Ph2 covered by` column, `k/N`).
- The `reviewer` agent flags speculative abstraction and single-use indirection.
- **Blast-radius traces to real producers/consumers, not a name grep.** The design's change-list is
  the smallest **COMPLETE** set: a shared **type/symbol** change enumerates its factory/fixture
  patterns across **all test roots** (not just `src`) and runs `typecheck`; a **value threaded** to a
  downstream consumer enumerates **every builder/producer call site**, not just the owning surface. A
  shallow-grep estimate that misses a known producer/consumer is a Gate-2 finding — so `diff ⊆ approved
  change-list` holds at execute without deviation-recording backfilling it.

**Fails the gate when** a change-list item has no matrix row behind it, an introduced abstraction serves
only one call site, or the blast-radius estimate under-scopes a shared type's factories/test-roots or a
threaded value's producer call sites (a name grep standing in for tracing the real producers/consumers).

---

## 3. Surgical changes

**Operating rule.** Touch only what the approved change list requires. Match surrounding style.
Never reformat lines you are not changing. Run the project's formatter only on the files this change
authored or edited — never over a shared or pre-existing file wholesale; whole-file conformance is a
separate concern (CI or a dedicated chore ticket), never folded into this ticket's diff. Never delete
pre-existing dead code without instruction. **Scope discipline has two axes — the file set AND
conformance to the approved design behaviour; a clean file diff does not certify behavioural
conformance.**

**Enforced at** (execute → Phase 3; review → Gate 4):
- The **verification sweep**: proves zero stray references and that the diff ⊆ approved list.
- The diff ⊆ approved-list check and the "no reformatting untouched lines" review check.
- Each diff hunk maps to a matrix row.
- The **design-conformance self-check** (behaviour axis): execute walks each Gate-2 Approach bullet
  and classifies it `implemented-as-approved | deviated`; any `deviated` bullet is recorded as a
  deviation (traced to the approved bullet) and surfaced to review — **even when the file diff is a
  clean subset of the approved list**. review re-confirms this axis and treats a missed behavioural
  deviation, or a feature self-marked `✅` that was not implemented, as **not clean**.

**Fails the gate when** a changed file is outside the approved list, untouched lines were
reformatted, pre-existing dead code was deleted without instruction, or the implementation diverges
from an approved Gate-2 Approach bullet without that deviation being recorded — a green file diff
sitting over a wrong behaviour.

---

## 4. Goal-driven execution

**Operating rule.** Define how success is proven before writing code, and report that proof at the
end. Multi-surface work is only done when every surface is covered or every exclusion is recorded.

**Enforced at** (design → Gate 2; review → Gate 4; finalise → final gate):
- A named **proving test** is required at Gate 2: the assertion that fails pre-change, passes
  post-change, runnable via `config.test_command`.
- **Gate 2 is blocked when an integration/runtime AC is backed only by a logic-layer proof; the
  layer-match is enforced, not advisory.** Gate 2 carries a per-AC **verification plan** (risk layer
  vs proof artifact, with a binding layer-match check). A layer-match `❌` blocks Gate 2 and passes
  only when the proof is upgraded to the matching layer **or** the row is recorded as a
  human-approved coverage-gap exclusion — never a silent pass.
- **Baseline-aware Definition of Done (project-supplied, detect-not-assume).** `analysis` captures a
  `BASELINE: green | red | flaky` by running the verification command once on the untouched checkout
  (a clean checkout is **not** assumed green — a pre-existing or flaky failure is real). When
  `baseline ≠ green`, the DoD is **prove the delta is green**: the change introduces no new failure
  and fixes any it claims to; a pre-existing failure outside the change is a **recorded baseline
  exclusion**, neither a blocker nor a silent pass. `execute` proves against this baseline;
  `review`/`finalise` compare against it, never against a blanket "all green". mango **detects and
  records** the baseline; it never decides which pre-existing failures are acceptable — that is a
  human/rulebook call, logged.
- **Verify-only re-review after a conditional LGTM.** A round-1 `CHANGES REQUESTED` may be qualified
  as a **conditional LGTM** ("LGTM once findings 1–N land as described"); the re-review is then a
  **verify-only pass** (confirm the N named fixes + a regression scan) rather than a full requirement
  re-derivation. The ticket-blind `challenger`'s full re-derivation runs **once** and is not repeated
  on a verify-only round unless a fix changed scope — its independence is preserved, its cost is not
  paid twice for pure re-confirmation.
- The test result is reported at review, including "would it fail without the change?".
- The **stale-review guard** at finalise is **mechanical**: it diffs the live tree against the
  `Reviewed at <sha>` marker, exempts the working-doc / bookkeeping paths, and is stale **iff a source
  file changed beyond the reviewed set** — never a commit-*count* test, so the marker/bookkeeping bump
  alone cannot dead-lock it. A bare "go" never clears it; only a fresh review covering the current tree
  does.
- The `N · k/N` denominator rule for every universal ("all/every/no") requirement: `k` surfaces
  covered out of total `N`.

**Fails the gate when** Gate 2 has no proving test, a proving artifact sits below the layer where
its requirement can fail (a layer-match `❌`), finalise records the test "not run" with no command,
or `k < N` with no recorded decision.

> **Lessons are repo artifacts, not personal memory.** A durable lesson — a constraint discovered,
> a wrong assumption, or a process gap — belongs in `config.lessons_path` (a committed repo file),
> never only in an assistant's personal memory. `finalise` asks for one on **every** run,
> independent of whether any matrix row was deferred.

> **The shipped CHANGELOG is the retro's neutral source.** An independent field retro reads
> `${CLAUDE_PLUGIN_ROOT}/CHANGELOG.md` (shipped *inside* the plugin, alongside `plugin.json`) as the
> neutral record of "what changed this version" — never a prior retro's write-up, which would compound
> one reviewer's framing. `scripts/validate.py` requires that CHANGELOG to ship and to carry an entry
> matching the manifest version.

---

## Subagent git isolation — never mutate shared git state

> **A subagent inspecting a branch works from refs or an isolated worktree; it NEVER mutates the
> shared working tree's git state.**

Branch/diff inspection is **ref-based** — `git diff <base>..<branch>`, `git show <branch>:<path>`,
`git log <base>..<branch>` — or **worktree-isolated** — `git worktree add <scratch> <branch>`, removed
afterward. A subagent — the `reviewer`, the `challenger`, or any review-phase worker — **MUST NOT** run
`git checkout`, `git switch`, `git stash`, or any HEAD/index-mutating git in the **shared working
tree**: that switches the live checkout off the in-progress branch, strips the in-progress source files
from disk, and strands the working doc — a real corruption + recovery detour. If a subagent must
**run** the suite against a branch (not just read it), it does so in an isolated `git worktree` / clone,
never the live checkout.

**Worktree ≠ environment-equivalence — carry the untracked env, or run in place.** A fresh worktree
holds only **tracked** files, so it has none of the project's required **untracked** environment (`.env`
/ local config, local certs, installed deps, built assets) and the app cannot boot. Before running a
suite in one, either **run read-only in place** when the tree is already at the reviewed SHA (preferred),
or **carry the required untracked env into the worktree**. **Sanity rule:** a **near-total** suite
failure inside a fresh worktree is an **env-fault** (missing untracked files) **until proven otherwise**
— it is **never** reported as a review finding or a regression. This reclassifies an environment
artifact only; it never suppresses a real finding — a *partial, targeted* failure inside the change's
blast radius still counts, and once env parity holds the same result is reportable.

This is the **same root cause** the v1.6.1 eval-isolation invariant fixed for the eval path (a process
running stateful git in a shared cwd) — **one principle, two surfaces** (review and eval). Enforced at
`review` and the `reviewer` / `challenger` briefs; guarded by `scripts/validate.py` (the review
git-isolation + env-parity tokens) and, on the eval surface, the `assert_checkout_clean` guard in
`tests/eval/run.sh`.

---

## Maturity — Stable vs Experimental

Every shipped behaviour carries an honest maturity level so a reader knows what is settled:

- **Stable** — committed behaviour, field-tested, safe to rely on. This is the default for everything
  not marked otherwise.
- **Experimental** — works and has been validated, but its exact shape may still change until further
  real-world use. Marked explicitly at the behaviour.

Two behaviours are **Experimental** today:

- **breakdown re-ratification** (surfacing a post-gate split delta for an explicit human re-approve):
  validated once in the field, its re-ratification trigger and granularity may change until a second
  epic exercises it.
- **the learning loop's classification and promotion machinery** — where the six-type boundaries fall,
  which recall key each type gets, and how a recurrence is scored. It is built on three probe rounds over
  real lesson files, but its *shape* will move as more lesson files run through it. **Its five invariants
  are NOT Experimental** and never will be: the classifier proposes and the human confirms, recall is
  advisory, falsification precedes ratification, lessons never modify mango, and everything is
  project-local. Those are safety boundaries, not a shape to be tuned.

Everything else on the ticket and epic paths is **Stable** — ticket-path classification (want-decision /
how-decision), `ASSUMED` handling, the 1-dispatch exposure-checker, epic detection, the enumerated
six-letter INVEST self-check, and the design blast-radius trace-to-real-producers.

When an Experimental behaviour **graduates**, the CHANGELOG records it explicitly, e.g.
`re-ratification: Experimental → Stable`.

---

## Skills are directive-only — no rationale in a SKILL.md

> **Skill text is runtime-loaded and IS behaviour (prose-IS-behaviour). A `SKILL.md` contains
> DIRECTIVES ONLY — no rationale, no "observed failure" war-stories, no historical justification, no
> why-this-exists commentary. The "why" belongs in the CHANGELOG or `RATIONALE.md`, never in a
> `SKILL.md`.**

Every token of a `SKILL.md` is paid on **every ticket run** that loads it, so non-behavioural text is
a permanent tax that instructs nothing. Concretely:

- **When a lesson motivates a new rule, add the RULE to the skill and the REASON to the CHANGELOG**
  (and, if a future maintainer needs the incident itself, to `${CLAUDE_PLUGIN_ROOT}/RATIONALE.md` —
  which is **not** loaded at runtime).
- **Keep, always:** every instruction, gate, STOP condition, MUST/NEVER, counted artifact line,
  threshold, escalation, conditional, output-format spec, and anything marked binding.
- **Never trade a directive for brevity.** Trimming a skill is a behaviour change unless the removed
  text is *provably* non-behavioural — the test is *"if I delete this, does any instruction, gate,
  condition, count, format, or escalation disappear?"* If yes or unsure, **keep it**.

Guarded by `scripts/validate.py` (`validate_no_rationale_in_skills`): the build **fails** if a
rationale marker appears in any `plugins/mango/skills/*/SKILL.md`.

---

## Descriptive vs normative — observe, facilitate, never author

> **mango generates the descriptive and facilitates the normative, but never authors the normative.**

A **descriptive** artifact is a *fact* about what the code or schema **is** — regenerable and
falsifiable (a code sitemap, a database schema map). mango may generate these freely; they are
opt-in, stack-specific adapters (`sitemap`, `db-map`), never core to the lifecycle and never on by
default.

A **normative** artifact is a *rule* — what the code **should** do (the engineering rule book,
database conventions). mango may **facilitate** defining these by **counting the observed patterns
and asking the human to choose** (the `codify` skill), but it must:
- **NEVER author a rule itself**, and never pick, recommend, or default to the majority. Presenting
  "pattern A: 12 files, B: 5" is **data**; concluding "so A is the rule" is **authoring — forbidden**.
- **Never treat "what the code does" as "what the rule should be."** Consistency observed is not
  consent given.
- Tag every recorded standard **`PROVISIONAL (awaiting ratification)`** and keep it provisional until
  a human **explicitly ratifies** it. A provisional draft is a draft for the team — not one person's
  preference frozen as law.

Enforced at `codify` (the counted report + the per-dimension human choice + the ratification gate)
and guarded by `scripts/validate.py` (the boundary tokens). The descriptive adapters change no source
and no schema.

---

## The learning loop — recall, propose, never self-modify

> **A lesson becomes an atomic CLAIM; a claim is recalled ADVISORILY; and only a claim that RECURRED
> and then SURVIVED FALSIFICATION is PROPOSED for promotion — into a PROJECT file, at a human
> ratification gate. No lesson, however ratified, ever edits mango.**

The loop is the descriptive/normative boundary above applied to what a run *learned*: mango
**describes** what it observed (the claim, its type, its evidence), **facilitates** the human deciding
whether it becomes a rule, and **never authors** the rule itself.

**The unit is the atomic claim, not the lesson entry.** `finalise` splits every captured lesson into
atomic claims first; classification, recall, recurrence, falsification, and promotion all operate on
**claims**. A bundled entry classified as one thing routes its other halves to the wrong destination.

### The six claim types — the type decides the destination and the recall key

| # | Type | Destination (all PROJECT-owned) | Recalled by |
|---|------|---------------------------------|-------------|
| 1 | **tool-constraint** — a named library/tool at a named API behaves unexpectedly | stays in `config.lessons_path` | **symbol** (the import / API) |
| 2 | **generalisable heuristic** — a principle that holds across tools | **routed by subject:** code → `config.rulebook_path`; process → `config.agent_brief_path` | — (proposed as a rule) |
| 3 | **skill-gap SIGNAL** — a mango phase demonstrably skipped a check it could have made in that run | `config.skill_gap_path` — **never a mango skill** | — (a signal for mango's maintainer) |
| 4 | **irreducible world-fact** — no gate could pre-empt it | `config.gotchas_path` | — |
| 5 | **project/domain ground-truth** — a hard-won fact about THIS system or domain | **split by sub-shape:** descriptive → `config.design_doc_path`; normative (a MUST) → `config.rulebook_path` as an entry with an **ID + blocking status**; environment (it rots) → carries a **`verified-at:`** stamp | **area** (not symbol) |
| 6 | **adjudicated non-defect** — a deviation examined and ACCEPTED, recorded so it is not re-litigated | `config.drift_path`, carrying an **`expiry:`** condition | **the finding that would otherwise be re-raised** |

**Two tiebreaks, applied during classification — not after:**
- **1 vs 4** — if a mango gate can be *imagined* that would have caught it → **type 1**. Only when
  **no** gate could ever pre-empt it → **type 4**. Type 4 is rare; do not over-build for it.
- **2 vs 3** — **type 3** only when a phase **demonstrably skipped a doable check in that run**;
  otherwise the general principle is **type 2**. A **preventive** process-lesson learned with nothing
  skipped fits neither — route it to `config.agent_brief_path`, **not** a rule.

**A process claim never lands in the code rule book.** `config.agent_brief_path` is a **project-owned**
process brief; it is **not** one of mango's own `agents/*.md` briefs, which no loop output may touch.

### The five invariants (binding — none is optional)

1. **The classifier PROPOSES; the human confirms.** A type, a destination, and a promotion are each a
   **proposal**. mango never classifies-and-acts, never promotes on its own, and never auto-applies or
   self-patches a rule.
2. **Recall is advisory.** It **SURFACES** matching claims at `refine`/`analysis` and does nothing
   else: it never injects a requirement, never adds an acceptance criterion, never blocks a gate, and
   never edits a file. A claim marked `retired:` is **SKIPPED** by recall — a human marks it retired,
   there is no auto-retire — and its history stays in the file.
3. **Falsification precedes ratification.** Recurrence measures how often a belief was **restated**,
   not whether it was ever **CHECKED**, so a recurring claim faces a falsification check — *is it still
   true? is it cheaply verifiable? was it checked, or only repeated?* — **before** it reaches the human
   ratification gate. A claim that fails, or that cannot be cheaply checked, is **BLOCKED from
   promotion** and stays a recorded lesson.
4. **Lessons never modify mango.** No lesson — however recurrent, however ratified — edits a mango
   skill, agent brief, template, or this file. A **type-3 skill-gap is a SIGNAL** recorded in the
   project's `config.skill_gap_path` for mango's maintainer; mango changes only through a normal
   version (build + `validate.py` + the behavioural eval + retro). A lesson flowing into a skill would
   make mango carry one project's context — breaking *harness, not rules* — and would destroy
   provenance, since mango's own design could no longer be told apart from an injected check.
5. **Everything is project-local.** Every loop output — claims, promoted rules, skill-gap signals,
   drift entries — lives in the **PROJECT's** repo. mango reads them in-project and **carries nothing
   home**: project A's claims never reach project B, and nothing is ever written into mango-plugins.

### Rules live in the rule book; `CLAUDE.md` only points at it

A promoted rule is written into `config.rulebook_path` (the rule book is created there if absent) and
is **never copied into `CLAUDE.md`** — a copy goes stale and competes with its source. `init` already
scaffolds the rule book and hoists a **pointer** to it into `CLAUDE.md`, and `doctor` already checks
both; the loop **REUSES** that and rebuilds none of it. A promotion is **not done** until the rule is
in the rule book **and** `doctor` is green on the `CLAUDE.md` → rule-book pointer.

Enforced at `finalise` (split → classify → recurrence/supersession → falsification → the per-action
ratification gate), `refine`/`analysis` (advisory recall), and `codify` (the rule-book write stays
`PROVISIONAL (awaiting ratification)`); guarded by `scripts/validate.py` and the behavioural eval.

---

## The refine phase — expose the decisions, never author the intent

> **refine (Phase 0, the FIRST phase) turns a raw request into a refined ticket by EXPOSING the
> product-decisions for the human to decide — it never authors intent. This is the same
> descriptive/normative boundary `codify` holds for rules, applied to a ticket: derivable = refine may
> resolve + cite; intent = the human's alone.**

The lifecycle now begins with `refine`:

```
refine → analysis → design → execute → review → finalize                        (ticket path)
refine → analysis(epic) → design(epic) → breakdown → N× ticket-lifecycles        (epic path)
```

- **Scan, don't ask what the scan can answer.** refine first scans the project (reusing
  `sitemap`/`db-map`); depth of exposure comes from the scan, not from asking the user what convention
  or code already answers.
- **Premise before investigation — `PREMISE FALSIFIED` halts, it does not dig.** The first thing the
  scan does is resolve every source the ticket references **as already existing** (path, file, symbol,
  config key, table). Only a **resolvable identifier** counts — something a grep can decide; a
  **prose noun** describing behaviour ("the dashboard banner") is **ambiguous**, never a falsified
  premise. A
  reference the ticket frames as **to-be-created** never counts as missing, and an **ambiguous** one is
  **surfaced, never blocking**. A referenced-as-existing source that does not
  resolve (and is not declared synthetic) emits the counted
  `PREMISE FALSIFIED: <n> … missing — <ref>` and **STOPS for the human immediately** — no hunting for a
  renamed equivalent, no history reconstruction, no guessing what the ticket meant. Every run emits
  `PREMISE: <r> checked | <m> missing | <a> ambiguous`, zero included, so the check cannot silently
  not-happen. Enforced at `refine` (Step 0) and `analysis` (step 1, when refine did not run).
- **The readiness gate is the count itself.** refine TRIES to expose the unresolved product-decisions;
  **0 → skip → analysis** (recorded), **≥1 → refine works**, **when in doubt → run**. refine
  **self-skips on a clear ticket** so it is never a tax on every ticket — the skip is a counted
  decision.
- **The derivable/intent boundary — classify before asking.** Every surfaced decision is either
  a **how-decision (HOW)** — answerable from convention / code / the rule book / the ticket text, or a
  tool choice → refine **resolves it and CITES** the source, and **does not ask**; asking a
  HOW-question launders a decision (an **uncited** how-decision resolution is itself a finding) — or a
  **want-decision (WANT)** — intent/priority/stakes/a genuinely new choice → refine **asks the user** in
  want-language (`AskUserQuestion` typed fork). **Tie-breaker: a decision about the acceptance BAR
  itself (what counts as done / a threshold / a sourcing standard) is a want-decision by default, even
  when it looks derivable — the user owns the bar.** A handed-back want-decision **must** be marked
  **`ASSUMED (awaiting ratification)`** (reusing `codify`'s provisional→ratify; recording it as settled
  prose is a finding) and requires an **explicit next-gate confirm** before it counts as ratified —
  never silent-adopted; a tripwire fires if it would reverse a prior human decision.
- **Direction, not tool.** refine stops at solution DIRECTIONS a non-technical user can feel; the
  specific tool/library is analysis's job.
- **Every decision is a counted artifact.** The refined ticket (settled wants / cited / ASSUMED / constraints)
  and the `REFINE:` counting line are emitted, not prose — visible and challengeable at Gate 1.
- **Backstop = 1-dispatch exposure-checker, NOT a debate — on BOTH paths.** The completeness-of-exposure
  check the newbie can't self-run reuses the **ticket-blind `challenger`** as an exposure-checker with
  **one** dispatch — never a Council or multi-advisor debate. **The epic path is not exempt:** refine
  dispatches the same 1-dispatch exposure-checker **before `breakdown`**, its findings surfaced for the
  human alongside the breakdown — an un-exposed decision is costliest at epic scale, so the epic path
  may never be the one that skips the backstop.

**Epic path — thin by design (only enough to split).** On an epic, `analysis(epic)`/`design(epic)` stay thin
(architecture-level, only enough to split) and `breakdown` emits a **counted** ticket list with a
per-ticket **INVEST** self-check, **human-approved before any ticket executes** (the human holds the
gate). Ticket-boundary sizing has no exact metric; INVEST is the heuristic and **retro corrects
mis-splits**. Two epic-path invariants back the split gate: (1) a **ratified breakdown is a living
plan** — if the ticket list changes after the split-gate (a ticket added/removed, or a ratified
decision reversed/re-pointed), `breakdown` **re-ratifies** by surfacing the **delta** as a counted
artifact for an explicit human **re-approve**, never letting the change ride in on a child's Gate 1
(**Experimental** — refined by retro; see the Maturity section above); (2) after the split ratifies, the epic **scaffold**
(child stubs + BACKLOG) is **committed to a shared ref before any child ticket branches**, so a child's
edit reads as an edit of a committed file — preserving the ticket-blind challenger's net-new-vs-edit
evidence.

Enforced at `refine` (the scan, the want-decision/how-decision classification + the acceptance-bar
tie-breaker + citation, the mandatory `ASSUMED` marking with an explicit next-gate confirm, the
`REFINE:` count, the 1-dispatch exposure-checker) and `breakdown` (the counted ticket list + INVEST +
the human split-gate + the **scaffold-committed-before-child** commit + the **re-ratification** delta on
a changed split); guarded by `scripts/validate.py` (the refine + breakdown boundary tokens). refine
writes no code and no tracker entry.

---

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

## Model delegation (strong model decides, weak model gathers)

> **"Opus decides, Sonnet executes, Haiku gathers — and every decision or verdict must be produced
> or ratified by the strong model; a weaker model may only gather, never conclude."**

Route work by the **nature of the task (judgment vs retrieval)** — NOT by phase position
(early/late) or role label (main/sub). The trap to avoid: review and the challenger *look* like
"heavy checking", but finding unmet requirements is the **highest-judgment** step in the flow. Never
demote it to a weak model — a weak model misses items yet asserts confidently, which is exactly the
silent under-delivery mango exists to prevent. A high-stakes diff warrants a *stronger* reviewer,
not a weaker one.

| Step | Nature | Model |
|------|--------|-------|
| Orchestrator + gates (decide) | judgment | the strong model the user drives (Opus) |
| Analysis: root cause/gap, requirements decomposition, AC validation, clarification, scope | judgment | Opus |
| Design: smallest change list, proving test | judgment | Opus |
| Review verdict + challenger requirement reconstruction | judgment (highest) | Sonnet — the `reviewer-max` agent (Opus) for high-stakes diffs under `cost_tier: max` — **never Haiku** |
| Implement the approved change list; draft PR body | execute | Sonnet |
| Explore: locate handler, callers, blast radius | retrieval + light judgment | Sonnet |
| Bulk read-and-extract / summarise across many files | heavy tokens, low judgment | Haiku |
| grep stray refs / run tests / lint | pure shell | no model — call the Bash tool directly |

`config.cost_tier` (`economy | standard | max`, default `standard`) shifts the dials within this
map — never against it. `economy` pushes more retrieval to Haiku and avoids Opus on review;
`standard` is the map above; `max` dispatches the **`reviewer-max`** agent (Opus) for high-stakes
diffs (security-tagged, or touching auth / data access / schema migration). Because a skill cannot
re-pin a subagent's model at runtime, the Opus upgrade is a **choice of agent** (`reviewer-max` vs
`reviewer`), not a runtime setting — `review` selects it explicitly. `reviewer` and `reviewer-max`
are never Haiku, and `challenger` is never pinned to Haiku. The **lite** tier runs on a single
model — no delegation overhead. Never spawn a model for a one-line shell command (grep/test/lint) —
run the Bash tool.

## Token cost — measure before you optimize (descriptive ledger + human-gated optimizers)

> **mango measures its own token cost as a counted, descriptive artifact, and adopts a token
> optimizer only through a human gate with the safety trade-offs made explicit — it never installs
> one, never depends on one, and never lets one weaken a check, a gate, a critic, or the evidence a
> critic emits.**

- **The Cost ledger is descriptive.** The run records token usage **per subagent dispatch** (reviewer,
  challenger, extractor, Explore fan-out, each review round) into the working doc as a **facts-only**
  counted artifact — **one row emitted per dispatch return as a mechanical by-product of dispatching**
  (N dispatches → N rows), not bookkeeping the model is asked to remember; `finalise` surfaces a
  one-line summary (total + top cost driver). It **never** auto-cuts anything — it makes cost **visible**
  so a *human* can decide. Cost was always an **estimate**, never measured per-phase; `context ≠
  correctness` applied to optimization means **don't optimize what you haven't measured** — the ledger
  is that measurement, and the data a later middle-tier sizing decision needs. The ledger is
  **dispatch-scoped**: it measures subagent dispatch only — main-loop output noise is **not measured by
  mango**, so it implies no dispatch-vs-noise split; the optimizer reports its **own** savings (`rtk
  gain`) for that domain. **Ledger completeness is gate-checked at finalise** (the ledger's teeth):
  the ledger is complete only when **every dispatch row is present AND its token cell carries a value** —
  a real count or the explicit `unmeasured (blocking retrieval)` marker; a missing row **or** a blank
  token cell is incomplete and blocks like an unfilled matrix column. It checks the **presence** of a
  value or an honest marker — it never inspects, ranks, judges, invents, or auto-cuts a value — so the
  ledger stays descriptive.
- **Emit deltas into the response, not full artifacts.** The working doc on disk is the **single source
  of truth** and is written **complete on disk**; the conversation gets only the **delta** on a partial
  update — the changed row/cell, "ledger **unchanged except** row N" — never a full reprint of the
  ledger / matrix / proof-manifest / working doc each time. This is a **representation-redundancy** cut
  on the safety axis (below): it changes only *how much of an unchanged artifact is re-pasted into the
  response*, never a check, a gate, a critic, or the artifact **written to disk**. The content-
  completeness gate still reads the artifact complete on disk — emit-less-into-the-response is not
  store-less-on-disk, and a delta references the rest, it never deletes it.
- **The safety axis (governs every optimizer choice).** An optimizer is **safe** only if it removes
  **representation redundancy** — *how* output is phrased — and **never** a check, a gate, a critic,
  or the **evidence detail** a critic relies on (`path:line`, measured values, per-clause verdicts,
  diffs). **RTK** (compresses Bash-command output before it enters context) is safe and sits **below**
  mango. **Headroom** input compression is safe, but its `OUTPUT_SHAPER` / effort-routing changes what
  the model writes and how hard it thinks → it **must stay OFF** for mango. **Caveman** (terse agent
  output) optimizes exactly what mango refuses for critics.
- **RTK default-expect + degrade cleanly.** The default `token_optimizer.rtk: "expect"` means mango
  **tolerates** RTK rewriting Bash output into a compact form; it does **not** install RTK and does
  **not** require it. If RTK is absent, everything runs **identically** — only the saving is lost.
  mango must never fail, block, or change a decision on RTK presence/absence, and no mango logic may
  parse an RTK-specific format in a way that breaks without RTK.
- **Caveman critic guardrail (HARD — invariant).** Caveman-style output compression **must never** be
  applied to critic output — the `reviewer`, the `challenger`, and any gate-blocking artifact — which
  **must retain full evidence detail** (`path:line`, measured values, per-clause verdicts). Terse
  critic output loses the evidence that **is** the review's value; **brevity is never applied where a
  false-green could hide** — the retro-#5 class, where a self-reported ✅ stood in for an unproven
  thing. Caveman, if enabled, is **scoped to non-critic output only** (`caveman.scope:
  "non-critic-only"`) and mango enforces it.

Adoption of any optimizer is a **recorded, PROVISIONAL decision** (via `/mango:budget`, ratified like
`codify`), never a silent toggle. Enforced at `budget` (detect + inform + the recorded human choice),
the `reviewer`/`reviewer-max`/`challenger` briefs (the critic guardrail), and `scripts/validate.py`
(the `budget` contract, the `token_optimizer` schema, and the critic-guardrail token).
