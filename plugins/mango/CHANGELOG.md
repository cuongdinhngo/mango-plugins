# Changelog

All notable changes to the mango plugin are documented here. This project adheres to
[Semantic Versioning](https://semver.org/). This file **ships inside the plugin**
(`plugins/mango/CHANGELOG.md`, alongside `plugin.json` / `README.md`) and is the **neutral source** an
independent field retro reads for "what changed this version" — read it, not a prior retro.

## [1.10.1] — 2026-08-15

**The rule-first recall path: a rule promoted from a lesson can now actually be reached, the lite lane
reads the corpus it writes to, and a promoted claim can be retired.** 1.10.0 joined the learning loop
end to end, and the join exposed the next break. `RECALL:` keys a type-2 claim by its `handle:` — matched
on the shape of the change. `RULE SECTIONS` derived the applicable rule-book sections from the change
TYPE. Those are two taxonomies with no bridge between them, so a rule that `/mango:promote` wrote from a
handle could never enter the applicable list: no change type maps to it. The rule sat inert in the rule
book while the lesson it came from was recalled forever, which is the same "written down but never
reaches the next ticket" failure 1.10.0 set out to fix, one step further along the pipe.

Three field observations, three fixes, and the constraint that governed all of them.

**Every mechanism here closes with zeros on a freshly `init`-ed project.** A new project has no lessons
file, a rule book that is the `init` template of `TODO`s, zero claims and zero handles. Four greenfield
negative controls (`greenfield-full-run`, `greenfield-quick-direct`, `greenfield-promote-zeros`,
`recall-handles-none-match`) exist for exactly that: `RECALL: 0`, zero handle-matched sections, `promote`
proposing nothing, and **no extra step, no warning, no block**. A change that made a new project do more
work would have been the wrong change.

### The rule-first path

- **A recalled handle makes its rule-book section applicable** (`analysis` step 11). The applicable list
  is now the **union of two sources**: sections derived from the change TYPE (unchanged), **and** any
  section carrying a `handle:` that this run's `RECALL:` line surfaced. The line records **which source**
  made each section applicable, so a reader can tell them apart. **`<h> = 0` recalled handles adds
  exactly zero sections** — the source cannot become a tax on a project that has learned nothing.
- **Answering a section is adequacy, not presence.** A section is answered by **naming what in *this*
  change the rule constrains**, or by the literal `N/A because <reason>`. A bare `✅` with nothing named
  behind it is **not an answer** and is a finding — the same empty-tick failure a bare matrix `✅` on an
  unfalsifiable acceptance value is.
- **An unratified `PROVISIONAL` section is surfaced, never enforced.** It is listed and accounted for
  like any other applicable section, because the accounting is what the step gates on; but its *content*
  is an uncodified standard, so a change that does not satisfy it routes to `codify`'s provisional→ratify
  nudge for the human — it is never a Gate-1 block on its own. Ratified rules block; provisional ones
  surface.

### The lite-lane bypass

- **A direct `/mango:quick <KEY>` no longer skips the two reads.** There were two ways into the lite
  lane and only one kept them: routed from `solve`, `analysis` had already emitted `RECALL:` and
  `RULE SECTIONS:`; invoked directly, neither ran. `quick` still hands off to `finalise`, whose learning
  loop writes — so a directly-invoked lite ticket **wrote lessons and never read one**, a one-way
  contributor to a file that only grows. `quick` now runs the advisory recall and the rule-section
  coverage, **reusing `refine`'s and `analysis`'s mechanisms rather than inventing parallel ones**, and
  carries the lines forward verbatim on the routed path. Both close with zeros on an empty corpus.
  **The lane stays lite:** no challenger, no requirements matrix, no fan-out, no baseline capture, two
  human gates. Two reads, two lines, no extra step.

### Retiring a claim whose rule has landed

- **`retired: promoted to <rule-ID>` is a recognised retirement reason.** Promotion is a **copy**, not a
  hand-off: with no such reason, a promoted claim kept being recalled beside the inert rule it produced.
- **`/mango:promote` OFFERS the retirement after a ratify; the human's per-claim answer applies it.**
  There is no auto-retire anywhere in this loop and this did not become the first one. The record
  **stays** in the lessons file — retirement is not deletion — and recall's existing retired-claim skip
  is reused unchanged. A second counted line reports it:
  `RETIRE: <o> offered | <a> retired on the human's answer | <s> declined/unanswered | records deleted: 0`.
- **The ordering is binding and is stated in the shipped text.** Retirement is safe **only because** a
  `handle:`-carrying rule now becomes an applicable `RULE SECTIONS` entry. Retiring a claim before that
  bridge exists **removes** coverage rather than moving it, so the sequence cannot be reversed by a later
  edit.

### Fixes

- **The plugin-root fallback selects the newest version, not the first `find` hit.** Step 3 of the
  resolution order is a read-only search; in the field it returned **eight** candidate directories with
  `1.8.0` first, so a host that sets no `${CLAUDE_PLUGIN_ROOT}` could silently load a two-minor-version-old
  contract while `doctor` printed the newer number. The search now **counts** its candidates and selects
  the **highest manifest version by semver compare** — never `find` order, never a lexicographic sort
  (which puts `1.8.0` above `1.10.0`) — and reports both. The tie-break lives in each skill's inline
  `<mango>` definition as well as in `PRINCIPLES.md`, because the core cannot be read before the root is
  resolved. This is a correctness bug on every host that does not set the variable, not a cosmetic one.
- **The `challenger` may not read the PR body while ticket-blind.** Field evidence: it ran `gh pr view`
  during a review. The brief forbade the working doc, the design, the matrix and the rationale and said
  nothing about the PR body — which routinely restates the design and the requirements, so reading it
  launders the authored design back into the check that exists to be independent of it. The hard
  constraint now names the PR body, PR comments, review conversations, and the commands that fetch them
  (`gh pr view` and any host equivalent), while stating what remains allowed: `git diff` / `git show` /
  `git log` over the refs, commit messages in the range included. The existing honesty note now lists the
  PR body among the inputs whose presence means independence has been compromised.
- **`refine`'s hand-off self-check reads as one sentence again.** A `every surfaced` fragment was left
  dangling when 1.9.0 inserted the recall clause mid-sentence, and it read as a lost directive. Git
  history shows nothing was lost — the 1.8.0 text ran the clause across a line break — so the orphan is
  removed and a check now fails if a future insertion splits it again. The same self-check now enumerates
  **type 2 by handle** alongside the other recall keys; the type the rule-first path depends on was the
  one it omitted.
- **The `FRESH_RUNS` counter needed no change.** The subshell loss it describes was already repaired in
  1.10.0 by the `tally_add`/`tally_count` side-channel ledger, which survives command substitution. No
  edit was made for it.

### Verification

`scripts/validate.py` went from 1,436 to 1,580 checks; **no check was removed and no gate loosened**.
Every new static check was tamper-tested by removing **every** occurrence of its subject and confirming
the check — that specific check, not merely some check — fails: **58 run, 58 caught, 0 vacuous**. Thirteen
fixtures were added (nine teeth tests, four greenfield negative controls), each dispatched by `run.sh` and
keyed in `FIXTURE_SKILLS`; registration was confirmed dispatch-free. **The behavioural eval has not been
run for this version** — it is scheduled, and until it is green these fixtures are authored coverage, not
demonstrated coverage.

## [1.10.0] — 2026-08-13

**The learning-loop pipe joined end to end, a cross-ticket `promote` skill, host-independent path
resolution, and an on-demand preload split.** Two field retros on another host recorded the same class of
lesson on three separate tickets, and it never reached the next ticket. The loop had been executed
correctly each time. Three independent breaks sat on the path a lesson must travel —
`write → classify → promote → recall → the next design answers it` — and repairing any one of them alone
carries nothing, because a pipe with three breaks passes nothing when one is fixed. All three are repaired
here, in one version, together with the reorder that decides whether the loop's steps run at all.

**No CHECK was removed and no gate loosened.** Where a section moved to a new file, every check that
asserted a token in the old location now asserts it across the whole surface (core + companions), so
relocation cannot be how a check stops applying. `validate.py` went from 1,186 to 1,427 checks.

### Fixed — the three breaks on the recall path

- **A type-2 heuristic now has a recall key.** Recall keyed types 1, 5 and 6 only; type 2 — the
  *generalisable heuristic*, the one type that is a candidate to become a rule — had no key at all, so a
  correctly classified type-2 claim could never surface again. A heuristic holds across tools, so neither a
  symbol (type 1's key) nor an area (type 5's key) can key it: it now carries a **`handle:`**, a short
  kebab-case class slug. `refine`/`analysis` surface a handle on the **shape of the change** — a shared
  vocabulary, a new core module, or a value threaded through callers — and the `RECALL:` line counts
  `<h> by handle`.
- **A recurring type-2 claim may no longer resolve to `stays in lessons_path`.** A claim whose `seen:` list
  holds ≥ 2 ticket keys recurred *despite* being written down, so recording it again is the treatment that
  already failed. It now resolves to `config.rulebook_path` (code subject) or `config.agent_brief_path`
  (process subject), or records the explicit `cannot promote: <reason>` naming the unset key or the
  falsification block. The counted `RECURRING-T2:` line's trailing `<l> left in lessons_path` must be `0`.
  This **reuses the v1.6 cost-ledger content-completeness shape** — a real value or an explicit honest
  marker, never the silent default — rather than inventing a parallel mechanism. **Type 5 is deliberately
  untouched:** every existing claim record is a type-5 project fact, and sweeping those into a rule book
  would rot it.
- **Every mango-shipped path resolves through a documented order, not one host variable.**
  `${CLAUDE_PLUGIN_ROOT}` is unset on some hosts, which made `templates/*.md` unreachable there and let a
  step that reads a template degrade quietly to prose. The order — the variable when set, else the plugin
  root located from the loaded skill file, else a read-only search, else an explicit UNREACHABLE branch
  naming the inline fallback — lives once in the always-loaded `PRINCIPLES.md` core, and every skill defines
  the `<mango>` notation before using it. Never a hardcoded or guessed path. `doctor` now reports **how**
  the root resolved and continues its checklist when it cannot resolve at all.
- **`finalise`'s claim steps run before the outward-action list.** They were steps `8a`–`8e`, after the PR
  body and the outward actions the human is waiting on; the artefacts that blocked shipped and the ones
  that did not were dropped. They are now steps `3a`–`3e`, ahead of the PR body, with an explicit directive
  forbidding any part of them being deferred past it — position alone is not a directive, so both the
  ordering and the prohibition are asserted.

### Added — `/mango:promote`, cross-ticket by construction

- Promotion's trigger is **recurrence across tickets**, which a step at the tail of one ticket's `finalise`
  structurally cannot see — which is why it fired zero times across 67 lessons. It is now its own skill:
  it groups **type-2** claims by `handle:`, and for each class seen on **≥ 2 tickets** proposes **one**
  candidate rule citing every instance, then **stops with a question requiring a per-candidate answer**.
- It **proposes only** — `PROMOTE: … | rules written: 0` is the falsifiable form. It is **idempotent** (a
  class already recorded at its destination proposes nothing, checked *before* drafting), **type-2 only**,
  and routes to a **configured** destination, never a guessed one. Three self-tests run on each draft: a
  **restatement test** (a sentence that merely paraphrases the lesson, adding no trigger, action and
  observable, is rejected), a **traceability test** (every clause quotes the lesson text it came from; an
  unquoted clause is invented policy and is deleted), and a **falsifiability test**.
- `solve` names it and states it does **not** invoke it (one ticket per run; a cross-ticket pass is not a
  lifecycle phase). `finalise` hands a class across once `seen:` reaches 2. `doctor` reports its two
  prerequisites, never as a ❌.

### Added — `design` must ANSWER every recalled handle by name

Surfacing was already advisory and stayed so; what was missing was **accounting for what was surfaced**.
`design`'s blast-radius step now emits one row per recalled handle and answers each with either a **trace
carrying the command and its actual output** — a filled cell with no command is explicitly not a trace — or
the literal **`does not apply because <reason>`**, which is a fully legal answer that **closes** the handle.
`HANDLES: <h> recalled | <t> traced | <x> does not apply | <u> unanswered` must satisfy `h == t + x` with
`u == 0`; any unanswered handle blocks Gate 2. `h = 0` closes the line with zeros and adds no work.

### Changed — the preload split (text relocated, never reworded)

`PRINCIPLES.md` was 27% of what loads before any ticket work begins. It is now an **always-loaded core**
(the four principles, the resolution order, the model-delegation map) plus **eight on-demand companions**
under `plugins/mango/principles/`, and each skill's frontend-only block moved to `skills/<name>/frontend.md`,
read when `config.track` includes frontend. **Every moved block is byte-identical to its source**; the
`<mango>` notation swap on top of it is a mechanical, greppable token substitution, not a reword. Lazy
loading fails when content that is needed never gets read, so **every companion carries an explicit,
unconditional READ instruction at its point of use** — never "consult X if relevant" — and each read states
what the phase still does when the path cannot be resolved. The measured always-loaded total falls from
2,074 to 1,715 lines on a backend ticket.

### Verification

`python3 scripts/validate.py` — 1,427 checks, 0 failed. Twelve new fixtures, each shown to catch something,
with the four negative controls that keep the new gates from becoming a tax: an explicit `does not apply`
**closes** the handle; a recurring **type-5** claim legitimately stays in `lessons_path`; a recall that
matches nothing closes with zeros and adds no step; and `promote` at recurrence 1 proposes nothing. Sixteen
tamper tests confirm each new static check fails when its subject is removed. The behavioural eval was
**not** run for this version.

## [1.9.1] — 2026-08-02

**Host-adaptation, plus four output-discipline directives.** Two things of the same low-risk class, both
additive. **(a)** mango degrades gracefully on hosts that lack a Claude-Code-only mechanism — proven on
Cursor by two field retros — while staying **ONE mango, not a fork**: every change is a fallback that also
holds unchanged on Claude Code. **(b)** Four directives from the same retros tighten what gets *written*.
**No reviewer or challenger behaviour changed, no gate's decision logic changed, no CHECK removed** — 1–3
below change *which file or which mechanism*, 4–7 add a directive. The heavier fixes those retros surfaced
(execution duty, a mutation check, the guardrail-spirit clause, a silent-loss inventory) change review
behaviour or add dynamic checking; they are a separate future big-idea still gathering evidence and are
deliberately **not** here.

### Added — host-adaptation (one mango, made host-aware)
- **⭐ The always-on context file is RESOLVED, never hardcoded.** `init`'s standing-context hoist and
  `doctor`'s check no longer assume `CLAUDE.md` is the file the host auto-loads. Both walk the same
  three-step resolution — `config.context_file` if set → an `AGENTS.md` that a `CLAUDE.md` merely
  **imports** (e.g. a one-line `@AGENTS.md`) → `CLAUDE.md` — and `init` **records the answer** in
  `config.context_file` so every later phase reads the same one. `doctor` **prints the resolved path** and
  ⚠ when the block sits only in a file the host does not auto-load: a pointer block in an unloaded file is
  invisible, which is the same outcome as never writing it. Everything else is unchanged — it stays a
  **pointer, never a copy**, never holds a secret, and the check remains **informational and can never
  gate the lifecycle**. **On a plain `CLAUDE.md` project nothing moves**; the new
  `host-context-file-default` fixture is the negative control that proves it.
- **New optional config key `context_file`** (default `CLAUDE.md`), shipped in `harness.example.json` and
  documented in the plugin README. Unset behaves exactly as before, with detection as the fallback.
- **`unmeasured` is the honest, CORRECT value where usage is not surfaced.** Some hosts return no
  `<usage>` block for a subagent at all. `solve`'s ledger rule and `finalise`'s completeness gate now say
  so explicitly: the marker names its **condition, not a host** — `unmeasured (host does not surface
  usage)` — a ledger whose rows all carry it is **complete and passes**, and **inventing, estimating, or
  back-filling a plausible number is a false-green and forbidden**. The gate still checks the *presence*
  of a value or an honest marker in every row; it never checked that a number was obtainable, and it does
  not start now. The marker generalises to `unmeasured (<reason>)`, with `unmeasured (blocking retrieval)`
  unchanged as its first case.
- **No single ask-the-human tool is assumed.** `refine`'s want-decision step (and the matching clause in
  `PRINCIPLES.md`) now reads "the **host's typed question UI** if it has one — `AskUserQuestion`'s typed,
  required-selection fork on Claude Code — else **numbered options in plain chat**". A missing host tool
  changes the mechanism, never cancels the question, and the **required selection holds either way**.

### Added — four output-discipline directives (additive; no gate decision changed)
- **Empirical output is PASTED, not described (`execute` step 5, `finalise` step 3).** Every claim that
  rests on having run something records the **actual command and its actual output**, verbatim and trimmed
  to the relevant lines — into the working doc, and from there into the PR body. "Tests pass" as prose is
  not a record. A **failing** command is pasted verbatim too, and a command that was **not run** is said
  so and its claim marked **unproven**. Prose can promise more than the code delivered; a real paste
  cannot.
- **A changed golden is a BEHAVIOUR CHANGE, not a number to bump (`execute` step 4).** A red
  golden/snapshot is never reflexively re-recorded. Either the change altered that output **intentionally**
  — then the old→new delta is a behaviour change to state, trace to the approved change list, and have
  **ratified at the next gate** before the golden moves — or **unintentionally**, and it is a **defect in
  the change** whose fix is the code, never the golden. Silently re-recording makes the test agree with
  whatever the code now does, retiring the one assertion that would have caught the regression.
- **A docstring describes DELIVERED behaviour — it IS the interface contract (`execute` step 3).** For any
  surface whose description a *caller* reads — a public API/SDK docstring, a CLI `--help`, above all an
  **MCP tool description a client LLM reads to decide when and how to call it** — write what the code
  **actually does after this change**, not what the ticket intended: real arguments, real return shape,
  real failure/empty cases, updated **in the same diff**. The caller cannot see the code, so the
  description is the only thing that can be wrong about it.
- **A blast-radius cell per change-list row (`design` step 4).** The Gate-2 change-list table gains a
  **blast radius** column naming each change's **side-effect surface** — callers, shared types,
  tests/goldens, tool/API descriptions, config, migrations, downstream consumers — so a reviewer knows
  **where to look** beyond the touched file. `none identified` is allowed; blank is not.

### Added — coverage
- Two eval fixtures for the resolution, both directions: `host-context-file-default` (a plain `CLAUDE.md`
  project still targets `CLAUDE.md` — the default is unchanged) and `host-context-file-agents` (an
  AGENTS-first project targets `AGENTS.md`, and a block left in the unloaded `CLAUDE.md` is surfaced as a
  ⚠, never a ❌).
- Two new validator functions — `validate_host_adaptation` and `validate_output_discipline` — plus new
  load-bearing tokens in the `init` / `doctor` / `refine` / `execute` / `design` / `solve` / `finalise`
  skill contracts. `scripts/validate.py`: **1071 checks, 0 failed** (up from 982).

## [1.9.0] — 2026-08-01

The **learning loop**: a durable lesson stops being a line nobody re-reads and starts acting on the next
ticket — **without mango ever changing itself**. Lessons are split into **atomic claims**, classified as a
**proposal**, surfaced **advisorily** at design time, deduped for **recurrence and supersession**, and —
decisively — put through a **falsification check that sits in front of every human ratification gate**.
**No CHECK is removed and no gate is loosened**; every piece is additive, and recall adds a *surfaced
section*, never a gate. Grounded on three probe rounds over real project lessons rather than reasoning in
the abstract.

**The one finding that shaped the design:** in a real lessons file, the **most-repeated claim was false the
whole time**. Recurrence measures how often a belief was **restated**, not whether it was ever **checked** —
so a promotion pipeline keyed on recurrence alone would efficiently turn confident mistakes into binding
rules. Hence the falsification gate, and hence its position: **in front of** the ratification gate, never
after it.

### Added — the loop, in `finalise` (steps 8a–8e) and `refine`/`analysis` (recall)
- **Claim-splitter (8a).** A captured lesson is frequently bundled — a tool fact, a principle, and a
  project fact in one paragraph — so `finalise` splits it into **atomic claims** first, in the shape of
  the new `templates/claim-record.md`. Everything downstream operates on the **claim**, never the entry,
  because a bundled entry classified as one thing routes its other halves to the wrong destination. Counted
  artifact: `CLAIMS: <c> claim(s) from <e> lesson entr(ies) | T1=… T6=… | <u> unclassified`, with `<u>`
  required to reach 0 before the gate.
- **Classifier (8b) — a PROPOSAL, never a decision.** Each claim is tagged **type + evidence + its recall
  handle** against a six-type taxonomy, with both tiebreaks applied *during* classification: **1 vs 4** (an
  imaginable gate makes it type 1; only a claim no gate could ever pre-empt is type 4) and **2 vs 3** (type
  3 only when a phase demonstrably skipped a **doable** check **in that run**; otherwise the general
  principle is type 2). Every classification carries `status: proposed (awaiting human confirm)` until the
  human confirms it at the final gate. Classify-and-act is forbidden.
- **Advisory recall (`refine` Step 0, `analysis` step 1).** Past claims are **surfaced** on the key their
  type dictates: **type 1 by SYMBOL** (its `handle: symbol:<import/API>`), **type 5 by AREA** — not by
  symbol, which is what makes it its own type — and **type 6 by the finding that would otherwise be
  re-raised**, carrying its `expiry:`. A `retired:` claim is **skipped**; a human retires a claim and the
  record stays, so there is **no auto-retire**. Counted artifact: `RECALL: <n> claim(s) surfaced | <s> by
  symbol | <a> by area | <f> by finding | <r> retired skipped — advisory (blocks nothing)`, emitted every
  run including zero. Recall **surfaces and stops there**: it injects no requirement, adds no acceptance
  criterion, adds no matrix row, blocks no gate, and edits no file. A recalled claim becomes a matrix row
  only if the human or the phase decides so on its merits — recorded as that decision.
- **Recurrence + supersession (8c).** Claims are deduped against those already recorded: one seen **again**
  gets this ticket appended to its `seen:` list and is flagged a **promotion candidate** — it recurred
  *despite* being written down, so recording it was not enough. A claim that **narrows or falsifies** an
  earlier one **REPLACES** it (`supersedes:`), and the earlier one is marked `retired: … superseded by …`.
  Retiring **never deletes**: recall skips the record, history keeps it. Counted artifact:
  `RECURRENCE: <n> recurring | <s> superseded (<r> retired) | <p> promotion candidate(s)`.
- **⭐ Falsification gate (8d) — before ratification, never after.** Every promotion candidate faces three
  questions: **is it still true?** (checked against the current checkout/tool, never against the claim's own
  restatements), **is it cheaply verifiable?** (name the grep, command, or test that would disprove it), and
  **was it CHECKED, or only repeated?** (count the sightings carrying real evidence, not the sightings). A
  candidate that is falsified, or that cannot be cheaply checked, is **BLOCKED from promotion** and stays a
  recorded claim. Counted artifact: `FALSIFY: <c> candidate(s) checked | <t> still-true (proceed) | <f>
  falsified (BLOCKED) | <u> not cheaply checkable (BLOCKED)`. `validate.py` asserts the **ordering**: the
  `FALSIFY:` step is documented before the `PROMOTION:` step, so the gate cannot drift to the wrong side of
  the human.
- **Promotion (8e) — proposed, human-ratified, PROJECT-owned.** A surviving candidate's destination is
  **proposed** from its type: type 2 (code) and type-5-normative → `config.rulebook_path` through `codify`'s
  existing provisional→ratify flow (type-5-normative carrying an **ID + blocking status**); type 2 (process)
  and any preventive process-lesson → `config.agent_brief_path`; type 4 → `config.gotchas_path`;
  type-5-descriptive → `config.design_doc_path`; type 6 → `config.drift_path` **with its mandatory
  `expiry:`**. The write happens **only after an explicit per-claim ratify** at the final gate — a blanket
  "go" on the outward actions ratifies no claim. Counted artifact: `PROMOTION: <p> proposed | <k>
  human-ratified | destinations: … | mango files written: 0`.
- **⭐ Lessons never modify mango.** No lesson — however recurrent, however ratified — edits a mango skill,
  agent brief, template, or `PRINCIPLES.md`. A **type-3 skill-gap is a SIGNAL** recorded in the project's
  `config.skill_gap_path` for mango's maintainer, who changes mango only through a normal version (build +
  `validate.py` + the behavioural eval + retro). A lesson flowing into a skill would make mango carry one
  project's context — breaking *harness, not rules* — and would destroy provenance, since mango's own design
  could no longer be told apart from an injected check; auto-apply and self-patch are self-modification
  wearing a ratification badge. `mango files written: 0` on the `PROMOTION:` line is the **falsifiable** form
  of this rule: a non-zero value means the run is wrong.
- **⭐ Everything is project-local.** Every loop output — claims, promoted rules, skill-gap signals, drift
  entries — lives in the **project's** repo. mango reads them in-project and **carries nothing home**: one
  project's claims never reach another, and nothing is ever written into mango-plugins.
- **⭐ Rules live in the rule book; `CLAUDE.md` only points at it.** A promoted rule is written into
  `config.rulebook_path` (created there if absent) and is **never copied into `CLAUDE.md`** — a copy goes
  stale and competes with its source. `init` already scaffolds the rule book and hoists the **pointer**;
  `doctor` already checks both. The loop **reuses** that wiring and rebuilds none of it, and a promotion is
  **not done** until the rule is in the rule book **and** `doctor` is green on the pointer.
- **`templates/claim-record.md`** — the single claim shape the writer (`finalise`) and the reader (recall)
  share, defining `type` / `evidence` / `handle: symbol:` / `area` / `sub-shape` / `re-raise` / `expiry` /
  `verified-at` / `seen` / `supersedes` / `retired` / `status`. A writer and reader that disagree on the
  fields make recall silently miss.
- **Type 5's sub-shapes are split, not lumped.** Descriptive → a design doc; **normative** (a MUST) → a
  rule-book entry with an ID and blocking status; **environment** → the same record carrying a
  **`verified-at:`** stamp, because an environment fact rots and an unstamped one is indistinguishable from
  a current one.
- **Four PROJECT-owned destination keys** in `.harness.json` (all optional; unset → the loop reports the
  destination as not configured and **surfaces** the claim rather than silently dropping it):
  `skill_gap_path`, `gotchas_path`, `drift_path`, `agent_brief_path`. `agent_brief_path` is a **project**
  file — explicitly **not** one of mango's own `agents/*.md` briefs, which no loop output may touch.
- **`doctor` check 9 — the loop's destinations, informational.** Prints one line per configured destination
  and ⚠ when a key is set but the file is absent; never ❌ on absence, since every destination is created on
  first write. Two things it does assert: every configured destination path is **inside the project repo**
  (a path outside it, or any path under a mango plugin directory, is a ❌), and `rulebook_path` stays
  reachable from `CLAUDE.md` per check 8.

### Changed
- **`solve`'s process-correction non-negotiable is scoped, and gains an artifact.** "Log it to
  `config.lessons_path` AND fix the offending skill/doc in the same session" now names what "the offending
  skill/doc" is: a **project-owned** file. A mango phase that demonstrably skipped a doable check is a
  **type-3 signal** in `config.skill_gap_path`, never an in-session mango edit. The correction is still
  logged and still lands as a repo artifact — in the project. Nothing is dropped; a redirect with a
  recorded artifact replaces an instruction that pointed at mango.
- **`breakdown`'s epic lesson runs the same loop.** The epic path already owned the durable-lesson write
  (`EPIC LESSON:`); it now splits and classifies it with the identical machinery and emits `CLAIMS:`, with
  recurrence, falsification, and promotion exactly as `finalise` defines them. No parallel mechanism.
- **`codify` step 3b accepts a promoted claim** into its existing provisional→ratify flow, tagged
  `PROVISIONAL (awaiting ratification)` and carrying its **claim ID + evidence** so a rule is traceable to
  what produced it. Its drift list gains a configured home (`config.drift_path`) and is also where a type-6
  adjudicated non-defect lands, each entry carrying its `expiry:` so an accepted deviation is never a
  permanent exemption nobody chose.
- **Templates.** `templates/ticket.md` gains a Phase-0 **recalled-claims** table plus the `RECALL:` line,
  and a Phase-5 **learning-loop** block with the four counting lines and a per-claim table; `templates/pr.md`
  reports the loop's lines alongside the durable lesson.

### Maturity
- **The loop's classification/promotion machinery ships Experimental** — where the six-type boundaries
  fall, which recall key each type gets, and how recurrence is scored will move as more real lesson files
  run through it. It is built on three probe rounds over real lesson files, not on abstract reasoning, but
  one version of field use is not a settled shape.
- **Its five invariants are NOT Experimental and never will be:** the classifier proposes and the human
  confirms; recall is advisory; falsification precedes ratification; lessons never modify mango;
  everything is project-local. Those are safety boundaries, not a shape to be tuned.

### Verification
- `scripts/validate.py`: **981 checks, 0 failed.** The new `validate_learning_loop()` asserts each piece
  against the shipped text — the six types and both tiebreaks in `PRINCIPLES.md`, every claim-record field,
  the four counting lines with their literal shapes, `type + evidence +` on the classifier, the
  proposal-not-decision wording, supersession-without-deletion, all three falsification questions,
  `BLOCKED from promotion`, the **FALSIFY-before-PROMOTION ordering**, every named PROJECT destination key,
  type 3 not promoting into mango, type 5's sub-shape split, type 6's `expiry:`, the process-claim/code-rule-book
  separation, `mango files written: 0`, recall's advisory + retired-skip + per-type keys in **both** `refine`
  and `analysis`, `codify`'s rule-book-not-`CLAUDE.md` landing with its doctor-pointer requirement, the four
  shipped config keys, and — for each of the eleven fixtures — that the file exists, that `run.sh`
  **dispatches** it, and that `FIXTURE_SKILLS` keys it (an unregistered fixture is not coverage).
- **Eleven new eval fixtures**, each injecting the state it judges and each carrying its non-vacuity in the
  other direction: `lesson-claim-split` (a bundled entry → four claims, each typed, as a proposal),
  `recall-symbol-type1` (fires on the matching symbol, **not** on the non-matching one),
  `recall-area-type5` (fires by area; the symbol-keyed claim stays silent, and the `RECALL:` line records
  zero by-symbol matches), `recall-type6-expiry` (recalled by the re-raised finding, carries its expiry,
  closes nothing), `recall-retired-skipped` (the retired claim skipped **and** its superseder surfaced —
  proving recall is not simply silent — record kept, nothing auto-retired), `recurrence-supersession`
  (twice-seen flagged; a measured claim replaces an inferred one and retires it without deleting it),
  `falsify-blocks-promotion` (**the decisive case** — the most-repeated claim is the false one and is
  blocked, as is one with no cheap check, with the gate in front of the ratification gate),
  `falsify-true-claim-promotes` (**the control** — the same gate passes a still-true, cheaply-checkable,
  actually-measured claim, which is still not in effect until the human ratifies),
  `promotion-human-gated` (proposes only; the skill-gap is a project signal editing no mango skill; a
  process heuristic goes to the agent brief, not the code rule book), `promotion-rulebook-wiring` (the rule
  lands in `rulebook_path`, never in `CLAUDE.md`, and is not done until `doctor` is green on the pointer),
  and `loop-project-local` (all six destinations inside the project, none under a mango directory, an unset
  key surfaced rather than redirected, nothing carried home).
- Assertions follow the standing convention: decision-level (outcome **+** its reasoning token), emphasis-
  agnostic, no bare glyph, separators written as character classes.

## [1.8.0] — 2026-08-01

An **infrastructure + wasted-turn** version in two halves. **(A)** the behavioural eval dispatches in
**parallel**, and five assertions that were failing on demonstrably **correct** behaviour are fixed.
**(B)** a **`PREMISE FALSIFIED` preflight** stops a run whose ticket references sources that do not
exist, and `init` **hoists** the harness basics into a project's `CLAUDE.md`. **No CHECK is removed and
no gate is loosened** — every change adds or strengthens one. The **six lifecycle phases' existing
behaviour is unchanged**: A touches only the eval runner and its assertion regexes; B **adds** a new
halt condition to `refine`/`analysis` and a new step to `init`, and alters no existing gate, count line,
STOP condition, or output format.

### Changed — (A) eval runner: parallel dispatch with per-worker isolation
- **The suite dispatches concurrently (`--workers N`).** A full instrumented run measured harness
  overhead at **~3 s of 10 590 s — 0.03%**: the suite is 100% `claude -p` latency and was 100%
  sequential. **Measured after the change: 998 s – 1201 s (16.6 – 20 min) across five full runs at
  `--workers 8`, against 10 587 s sequential — 8.8× to 10.6×.** That is an order of magnitude more than
  every available fixture merge combined (~9.5 min), which is why this version parallelises instead of
  cutting. `--workers 1` is a genuinely sequential mode for debugging.
  What parallelism guarantees is only that: **the same fixtures, the same assertions, the same counts,
  in less wall-time.** It proves nothing new about behaviour.
- **The runner is two-pass, so a prompt cannot drift from its assertions.** The suite body runs once to
  **register** each dispatch (with the `.harness.json` `test_command` in force at that line) and once to
  **judge** the transcripts, at the same call sites. Assertions are judged in script order, so a
  parallel run's output reads exactly like a sequential one. An assertion whose dispatch was never
  registered now **FAILS loudly** (`NO TRANSCRIPT`) instead of reading as coverage.
- **Per-worker isolation, asserted.** Every worker gets its own `git clone --local --no-hardlinks` and
  writes its own `.harness.json` **per job**. This removes two real hazards of concurrency: fixtures
  whose `execute` branches and commits would race inside one shared clone, and `red-baseline` repointing
  `config.test_command` — which under concurrency would flip the harness under another in-flight
  dispatch. A new counted assertion proves every worker tree was disposed, proven **non-vacuous**
  against an undisposed tree, alongside the existing live-checkout guard (both kept).
- **`--only <regex>`** filters dispatch *and* judging for the dev loop. It reports the run as
  **PARTIAL**, counts its skipped assertions, and **writes no cache entry** — a cache green may only be
  minted by a run that proved the whole suite. CI passes no arguments, so CI is always a full run.
- The transcript cache is unchanged and still hits. Note that editing `run.sh` invalidates the whole
  cache via the runner fingerprint, so the first run after this version re-runs every fixture fresh.
- **The per-job harness write is self-tested.** Two dispatch-free assertions prove the write carries the
  command it is handed (green default, and `red-baseline`'s override on top of it). This version's own
  first parallel run caught a stray positional there that put the repo *path* into `test_command` —
  which broke the `red-baseline` fixture's premise while its assertions still passed, because the model
  located the committed failing check by itself. The bug never shipped; the guard is permanent.

### Fixed — (A) nine assertions that failed on CORRECT behaviour
Five were named by the profile; the other four surfaced in this version's own first full parallel run,
on transcripts whose behaviour is correct in every case. Each was widened over **wording only** and
still requires the load-bearing outcome. The six shared tokens are proven **both ways** by a new
dispatch-free self-test — each must match the correct wording that used to fail **and** still miss the
wrong behaviour:
- `breakdown-invest` — `**S**mall` / `**I**ndependent`: markdown emphasis *inside* a word broke a
  contiguous substring match. Now emphasis-agnostic (`RE_INVEST_LETTERS`, `RE_INVEST_SMALL`).
- `refine-consistency` — the skill states the negative as a **count** (`0 want-decisions asked`) where
  the regex demanded a negation phrase. The zero-count form is now accepted (`RE_ZERO_WANTS`).
- `invest-force-resplit` — the right-sized control is reported "unsplit" / "untouched" / "carried
  through", none of which the alternation listed (`RE_NOT_SPLIT`).
- `frontend-layer` and `design-layer` — an assertion pinned to the single glyph `❌`, which a correct run
  may write into the working-doc verification table rather than the response text. Both now assert the
  layer-match **failure** as a decision (`RE_LAYER_SUBJECT` + `RE_LAYER_MISMATCH`).
- `epic-scaffold-committed` — a bold `**before**` broke a `before ` + space match (`RE_BEFORE_CHILD`).

Four more, from the first parallel run:
- `verify-only-scoped` — the correct run states the negative as "**No** full build, no whole-suite run"
  where the alternation demanded "not …".
- `verify-only-main-loop` — "zero subagents dispatched" / "dispatch**es** no reviewer" where the
  alternation matched only "dispatch no" / "no subagent".
- `refine-classify-A-vs-B` — the discrimination step named by its **mechanism** (the tie-breaker;
  refusing to "launder" a convention-answerable question into a want-decision) rather than the words
  "self-check".
- `codify-drift-count` — the run **emits** the prefixed `DRIFT: 5 entries | 2 tickets` line and says
  both numbers were counted from the list, without also discussing "counting lines" in the abstract.
  Emitting the artifact is stronger evidence than narrating the rule, so the emitted line is accepted as
  the subject; the "counted from the list, not narrated" half of the assertion is unchanged.

**The single root cause, now written down as convention.** Nearly every one of these is the same defect:
a **bare literal separator** between two load-bearing words. A space cannot match `**not** split` or
`**before** the gate`, and a space cannot match a hyphen (`no change` vs `no-change`). `tests/eval/README.md`
rule 6 now requires a separator *class* (`not[*_ ]{1,6}split`, `no[ -]change`) instead. Every widening in
this version is an instance of that rule, not a loosening of an outcome.

Two more of the same emphasis class surfaced on the re-runs and are now shared tokens as well:
`invest-force-resplit`'s "re-split it **before** the gate" (`RE_BEFORE_GATE`) and `verify-only-scoped`'s
cost-contrast form of the negative — "round 2 costs **zero dispatches** … re-deriving them would re-pay
for facts already proven" (`RE_NO_BLANKET_RERUN`).

`scripts/validate.py` now fails the build if an assertion regex is a bare glyph again, and
`tests/eval/README.md` records both shapes as standing convention. All **eight** shared `RE_*` tokens
are covered by the self-test, each with a correct and a wrong transcript; the two inline widenings
(`refine-classify-A-vs-B`, `codify-drift-count`) are evidenced by their transcripts and by 3× fresh
re-runs. **No fixture was cut or merged**:
the three candidate merges were left in place — parallelism makes their ~9.5 min irrelevant, and each
would have traded a distinct non-vacuity proof for seconds.

### Added — (B1) `PREMISE FALSIFIED` preflight (a new halt, before the archaeology)
- A phase pointed at a ticket whose referenced sources **do not exist** used to spend turns hunting for
  a renamed or moved equivalent before anyone concluded the ticket was wrong. `refine` now resolves,
  as the **first** act of its scan, every source the ticket references **as already existing** (path,
  file, symbol, config key, table). A miss emits the counted
  `PREMISE FALSIFIED: <n> referenced-as-existing source(s) missing — <ref> (<ticket line>)` and **STOPS
  for the human immediately** — no rename hunt, no history reconstruction, no guessing.
- **What it catches, precisely:** a **resolvable identifier** — a path, file, module, symbol, config
  key, table, route or command, i.e. something a grep can decide — that the ticket frames as already
  existing, does not resolve in the checkout, and is not declared synthetic. **What it never fires on:**
  a path the ticket frames as **to be created** (it is not expected to exist); an **ambiguous** framing,
  which is **surfaced as an item, never blocking**; and a **prose noun** describing behaviour or a
  surface ("the dashboard banner", "the existing hashing algorithm") — locating a described thing is
  ordinary analysis work, so it is classified ambiguous. That last scope limit came from this version's
  own eval: the first full run with the check enabled halted three existing analysis fixtures whose
  tickets name only prose nouns, which is a false halt in any repo, not just the eval sandbox.
- **The eval environment declares its tickets synthetic.** The suite's sandbox is a clone of the plugin
  repo, which ships no application source, so a fixture ticket about a hypothetical app names sources that
  can never resolve. The generated throwaway rule book now declares the project's tickets **synthetic** —
  the check's own carve-out, stated once for the environment rather than in 59 fixtures — and the two
  `premise-*` fixtures opt back in by stating their references are claims about that checkout, which is a
  real ticket's default. The check is therefore still exercised both ways, and what the fixtures prove is
  the behaviour: classify each reference, emit both counted lines, halt, skip the archaeology, and stay
  silent on a to-be-created path. Every run emits `PREMISE: <r> checked | <m> missing | <a> ambiguous`, zero
  included, so the check cannot silently not-happen.
- `analysis` carries the same check (for a direct invocation where `refine` did not run) and reuses
  refine's classification and counting line rather than a parallel mechanism; `solve` stops the
  lifecycle on the halt. Both lines are emitted **verbatim, prefix included, before any table or
  prose** — a narrated count is an addition, never a substitute, exactly as for `REFINE:` / `SECTIONS:`
  / `DRIFT:`. (The first run of the new fixture produced the right behaviour — halted, named all five
  missing references, ran no archaeology — but reported the count as a table, so the format directive is
  now explicit.) Guarded across `refine`, `analysis`, and `PRINCIPLES.md` by
  `validate_premise_preflight`, and proven by **two** fixtures: `premise-falsified` (it fires, names the
  missing refs, halts, skips the archaeology) and `premise-to-be-created` (the negative control — a
  guard that fired on a to-be-created path would block every net-new ticket).

### Shipped knowingly — the additive STOP, and the residual
- **B1 adds a STOP condition to `refine` and `analysis`, so this version is not literally
  "lifecycle behaviour unchanged".** It is **purely additive**: no existing gate, count line, STOP
  condition or output format is altered, and the new halt carries two carve-outs — a **to-be-created**
  path never fires it, an **ambiguous** framing is surfaced rather than blocking — plus a **prose noun**
  scope limit and a **negative-control fixture** (`premise-to-be-created`) that fails if the guard ever
  fires on a file the ticket exists to create. Shipped in this version by decision rather than split out.
- **The milestone run is 222/224 at `--workers 8`, shipped as-is.** The two residuals are **per-run
  wording flaps**: they rotate between assertions run to run, the behaviour in every transcript is
  correct, and each mechanism was fixed at its root cause and re-verified **3× fresh**. Across five full
  runs there were **zero behavioural regressions** and the isolation guards passed every time. The
  residual rate is roughly 1% per assertion per run — a phrasing variance, not a coverage gap, and
  chasing a literal 224/224 buys no coverage.

### Added — (B2) `CLAUDE.md` standing-context hoist (a pointer, never a copy)
- The harness basics were re-derived from scratch nearly every session and re-read at every phase
  boundary. `init` now writes a fenced, regenerable `mango:standing-context` block into the project's
  `CLAUDE.md`: which config governs, the few values a phase needs before it can act, the standing
  constraints (the human holds every gate; no outward action without a per-action approval; tracker
  writes via `config.tracker.cli`; stay inside the approved change list), and a **pointer to
  `config.rulebook_path`** — never a copy of the rules, which would go stale and compete with the
  source. An existing `CLAUDE.md` is only touched between the markers, and only after asking.
- **No secret, token, or credential is ever written into `CLAUDE.md`** — it is committed context, so the
  same no-secrets rule as `.harness.json` applies. `doctor` reports the block's presence as
  **informational only** (✅ / ⚠, never ❌): it is persistent context, not a prerequisite, so it can
  never gate the lifecycle. This repo's own `CLAUDE.md` carries the same block and joins the shipped
  operational-text jargon scan.

## [1.7.6] — 2026-07-31

A **token-runtime** version, **not a behaviour change**. It removes non-behavioural "why" text
(rationale, `Observed failure:` / `Field-observed:` war-stories, historical justification) from the
skills and agent briefs that load into the main loop on every ticket run, and installs a **permanent
rule + validator check** so the bloat cannot creep back. **No CHECK is removed** — every gate, STOP
condition, MUST/NEVER, conditional, counted-artifact line, threshold, escalation, and output format is
intact and unchanged; the only new enforcement **ADDS** a guard.

**Why this is safe.** In mango, prose **IS** behaviour — a skill's text is its behaviour, with no code
behind it. So the trim was scoped to text that provably cannot change behaviour and was verified
mechanically: a word-level diff of every deleted segment was scanned for behavioural markers, and the
counted-artifact lines were counted before and after (`SECTIONS:`, `CLARIFICATION:`, `REFINE:`,
`BREAKDOWN:`, `DRIFT:`, `EPIC LESSON:`, `RE-RATIFY:`, `BASELINE:`, `SURFACES:`, `TRACK:`,
`RULE SECTIONS:`, `LEDGER TOTAL:`, `DOCTOR:`, `⚠ surfaces proven`, `: <n>`) along with every `MUST`,
`NEVER`, and `STOP` — **all identical before and after**. **Zero** deleted segment contained a
`MUST` / `NEVER` / `STOP` / count-line / output-format token. Every edit is a **pure deletion or a
re-wrap**: **no directive was reworded**, so `scripts/validate.py` (green) plus the marker audit is the
full proof and no eval fixture needed a fresh run.

### Changed
- **Rationale removed from 12 runtime files (21 passages, −38 lines, −632 words ≈ 2.7 % of the skill +
  agent text loaded per run).** Per file: `design` −10, `breakdown` −8, `execute` −5, `refine` −4,
  `finalise` −3, `budget` −2, `codify` −2, `analysis` −1, `db-map` −1, `review` −1, `agents/reviewer`
  −1, `agents/challenger` ±0 (re-wrapped). What went: every `(Observed failure: …)` / `*(Field-observed:
  …)*` war-story; the `This skill exists because …` justifications in `codify`, `budget`, and `db-map`;
  the `v0.3` / `v1.6.1` / `retro-#5` historical anchors in `analysis`, `review`, `budget`, and both
  critic briefs; and `breakdown`'s trailing blockquote, a verbatim duplicate of its opening one.
- **One directive was moved, not changed.** `design`'s *"A shallow-grep-only estimate that misses a known
  consumer is a **Gate-2 finding**"* was **promoted verbatim** out of the war-story parenthetical it was
  buried in, so deleting the war-story could not take the finding with it.
- **`skills/solve/SKILL.md` deliberately untouched.** Its *"Why this is a skill, not an agent"* section
  reads as rationale, but *"orchestration must live here, in-conversation"* is arguably a directive
  against delegating the orchestrator to a subagent. Unsure → kept. Same call for `analysis`'s
  committed-stub fragility note, `design`'s *"execute's deviation-recording remains the backstop (it is
  **not** removed)"*, and `analysis`'s *"an aggregate k/N is not enough for a 'for each' requirement"* —
  each states a rule as well as a reason.

### Added
- **Permanent rule: skills are directive-only (`PRINCIPLES.md` → *Skills are directive-only*).** Skill
  text is runtime-loaded and IS behaviour, so a `SKILL.md` carries **DIRECTIVES ONLY** — no rationale, no
  war-stories, no historical justification. When a lesson motivates a new rule, the **RULE** goes in the
  skill and the **REASON** goes in the CHANGELOG. Mirrored in the plugin README and `CONTRIBUTING.md`.
- **`plugins/mango/RATIONALE.md`** — the non-runtime home for the "why". It ships beside `CHANGELOG.md`,
  records every incident this version removed from a skill (with the rule each one motivated and the file
  that still enforces it), and is **loaded by no skill**.
- **Validator: `validate_no_rationale_in_skills`.** Fails the build if any `plugins/mango/skills/*/SKILL.md`
  carries `observed failure`, `field-observed`, `exists because`, `the reason …`, `historically`,
  `war-story`, or `retro-#N`. **Proven non-vacuous:** injecting `(Observed failure: …)` into
  `skills/quick/SKILL.md` turned the run red with exactly that finding; removing it restored green.
- **Validator: `validate_rationale_doc`.** Requires `RATIONALE.md` to exist, to state it is not loaded at
  runtime, to actually carry the observed-failure records the skills no longer hold, and to name each of
  the six core skills — **and fails if any `SKILL.md` ever references `RATIONALE.md`**, which would put
  the why back on the runtime path. Also proven non-vacuous against an injected reference.
- **Eval: a dispatch-less `validator no-rationale-guard self-test`** in `tests/eval/run.sh`, the same
  injection discipline as v1.7.5's jargon guard and equally free (no `claude -p`). It injects each
  rationale marker into a runtime `SKILL.md` and asserts `validate.py` **FAILS**, asserts a `SKILL.md`
  referencing `RATIONALE.md` **FAILS**, then that removal restores green — so the guard can never pass
  vacuously. The dispatch-less self-test count goes **2 → 3**.
- **Release checklist in `CONTRIBUTING.md`.** A release touches four places but only two are
  validator-enforced; the root README's **version badge** and **status paragraph** are not, and the badge
  had drifted two versions behind the status line beneath it. Both are now itemised, with the rule that
  every status claim maps to a repo source.
- Validator total: **591 → 728 checks**, 0 failed.

### Docs
- Root `README.md` status refreshed: correct version, `Stable`/`Experimental` vocabulary only (a
  surviving `— v1` label removed — it slipped the v1.7.5 grep, whose pattern requires the dash *after*
  `v1`), an honest real-world-usage note naming no third party, and one factual fix — the ticket-blind
  challenger rebuilds requirements from the **raw ticket**, not "from the diff alone".
- `RATIONALE.md` is deliberately **excluded** from the eval's skills-hash (documented in `run.sh` and
  `tests/eval/README.md`): no skill loads it, so it cannot change behaviour and must never invalidate a
  transcript cache.
- `tests/eval/README.md` records that a **pure deletion of non-behavioural text** — no directive
  reworded — is proven by `validate.py` plus a marker audit of the deleted segments and needs no fresh
  fixture run, since the existing fixtures already cover every gate it left untouched.
- Retired the last internal shorthand from `CONTRIBUTING.md`'s retro convention (`n=`), which sat outside
  the validator's operational-text scan set.

## [1.7.5] — 2026-07-25

A **fix-only** version closing the verify-layer gaps a v1.7.4 field test surfaced. **No new lifecycle
phase, no new idea.** Nothing removes a CHECK — every change **ADDS** a guard, **COMPLETES** an
incomplete one, or **FIXES** one that silently passed; no gate is loosened. refine still **exposes, never
authors**; every decision stays a counted artifact; the human holds every gate. Generic and
stack-agnostic throughout (fixtures use `PROJ-*`); all plugin text is English-only.

### Fixed
- **⭐ The validator passed while its own claim was false — the false-green fixed (Fix 1).** v1.7.4's
  entry claimed `scripts/validate.py` enforced a zero-jargon grep over shipped operational text. It did
  not. Two independent causes, both now closed:
  - **Pattern gap.** The grep held only `v1-learning` and `n=1`/`n=2`. The actual pre-relabel framing —
    `v1 — "enough to run and learn"` — matched **neither**, so it survived in `skills/solve/SKILL.md`,
    `skills/breakdown/SKILL.md`, `skills/refine/SKILL.md`, `PRINCIPLES.md` and the plugin `README.md`
    while the validator reported OK. Because `solve/SKILL.md` is the orchestrator skill loaded into
    context, the deprecated label then leaked into a committed, merged project artifact.
  - **Scope gap.** The scan set covered the **plugin** README but never the **repo-root** `README.md`,
    which carried both `v1 —` and `n=1`.

  **What the validator now enforces, exactly:** every pattern in `BANNED_JARGON` — `v1-learning`,
  `n=1`/`n=2` (case-**sensitive**, so the `N=1`/`N>1` matrix denominator in `analysis/SKILL.md` is
  untouched), `enough to run and learn`, and `v1 —`/`v1 –` — must be **absent from every file** in the
  operational set defined by `operational_text_files()`: `plugins/mango/skills/*/SKILL.md`,
  `plugins/mango/agents/*.md`, `plugins/mango/templates/*.md`, `plugins/mango/PRINCIPLES.md`, the plugin
  `README.md`, **and the repo-root `README.md`**. `CHANGELOG.md` is deliberately **excluded** — a
  changelog documenting past versions is a historical record, not operational text, so the historical
  entries below are allowed and unaffected. All shipped operational text is relabelled to the
  Stable/Experimental vocabulary. The guard is proven **non-vacuous** by a free, dispatch-less runner
  self-test (below) — a validator whose claim is false is the worst defect class mango can ship, so this
  one is checked by injection, not by assertion.
- **Worktree ≠ environment-equivalence (Fix 2).** v1.7.4 told a review subagent to use an isolated `git
  worktree` to **run** a suite. A fresh worktree holds only **tracked** files, so it has none of the
  project's required **untracked** environment (`.env` / local config, local certs, installed deps, built
  assets): the app cannot boot and **every** test fails for an environmental reason that reads exactly
  like a catastrophic regression. Two parties hit this independently in one session — a review subagent
  reported "1 failing test file" for a file that passes 5/5, and the operator hit 12/12 phantom failures
  until `.env` was copied in. The isolation was correct; the guidance was incomplete. A subagent must now
  either **run read-only in place** when the tree is already at the reviewed SHA (the cheaper, safer
  path) **or carry the required untracked environment into the run-worktree** first. **Sanity rule:** a
  **near-total** suite failure inside a fresh worktree is an **env-fault until proven otherwise** — it is
  fixed and re-run, and **never** reported as a review finding or a regression. This **reclassifies an
  environment artifact only**: a *partial, targeted* failure inside the change's blast radius is still a
  real finding, and once env parity holds the same result is reportable. Stated in `review/SKILL.md`, the
  `reviewer`/`challenger` briefs, and `PRINCIPLES.md` (Subagent git isolation).
- **`work_doc_mode` wiring at `solve`'s auto-path (Fix 3a).** v1.7.3's committed-stub → `separate`
  guidance lived in `breakdown` and `analysis`, but `solve`'s `auto` mode still embedded regardless.
  `solve` now classifies the ticket where it actually sets the working-doc mode and routes a **committed,
  tracked scaffold stub** to **`separate` even under `auto`**, recording the resolved mode in
  `Session status` so every later phase (and review's challenger-payload construction) reads the same
  answer. Guidance + a sensible default, not a behavioural gate.
- **execute commits before review is dispatched + an empty-diff fallback (Fix 3b).** Review-before-commit
  plus a ref-based `<base>..<branch>` inspection produced an **empty** diff and very nearly rubber-stamped
  "no changes" over a real change-set. Two guards, not one: `execute` now **commits the change-set BEFORE
  dispatching review** so a real committed diff exists for the ref-based read; and the
  `reviewer`/`challenger` briefs (plus `review/SKILL.md`) carry the fallback — *if a `<base>..<branch>`
  diff is empty the change may be **uncommitted**; check `git diff HEAD` + `git status --porcelain -uall`
  before concluding no-change.* An empty range is a reason to look harder, never a no-change verdict.
- **The epic path had no lesson-capture owner (Fix 3c).** An epic **ends at `breakdown`** and never
  reaches `finalise`, so mango's *"always capture a durable lesson"* rule had **no owner** on that path —
  the split rationale and the overlap rulings reached no `config.lessons_path` and died with the run.
  `breakdown` now owns it at ratification and after any re-ratification, reusing `finalise`'s durable-lesson
  machinery and recording the split rationale, every overlap/boundary ruling, any forced INVEST re-split,
  and each re-ratification delta with its human decision — emitted as the counted line
  `EPIC LESSON: <n> lesson(s) written to <config.lessons_path>` so it cannot silently not-happen.
- **codify's drift count is a counted line, not prose (Fix 3d).** A prose count drove a near-miss where
  "6" should have been "5". `codify` now emits `DRIFT: <n> entries | <m> tickets`, both numbers counted
  from the list itself — the same prefixed counting-line shape as `REFINE:` / `BREAKDOWN:` / `SECTIONS:`,
  which is what makes a count resist fudging.
- **A multi-clause want-decision gets one row per clause at Gate 1 (Fix 3e).** A ratified want-decision
  joined by *and* — *"place the rows under the summary AND make each row tappable through to detail"* — is
  two clauses. Decomposed as one aggregate matrix row, the design-conformance self-check certified the
  placement half `✅` while the navigation half shipped unproven. `analysis` now **enumerates the clauses
  at Gate 1** and gives each its **own matrix row and its own verification-plan / proof-manifest row**; a
  clause with no row of its own is a **finding**. Same per-item-inventory discipline as the "for each of
  N" rule and `execute`'s one-assertion-per-clause M-gate rule — no parallel mechanism.

### Changed
- **Eval runner — the cache tallies survive their subshell (housekeeping).** Every fixture is invoked as
  `t="$(run_fixture …)"`, a command substitution, so the `CACHE_HITS`/`FRESH_RUNS`/`FRESH_FIXTURES`
  assignments inside `run_fixture` were discarded when that subshell exited. The visible symptom was
  cosmetic ("0 fixtures ran fresh" when they all did), but the same bug also emptied `FRESH_FIXTURES` —
  the list the end-of-run **cache WRITE** iterates — so the transcript cache was **never populated and
  could never hit**. The tallies now go to side-channel ledger files that outlive the subshell; the
  counters print truthfully and the cache actually persists.
- **`refine-direction-not-tool` assertion widened over WORDING only.** The old alternation missed correct
  runs phrased "left to analysis" or "analysis’s job" (a typographic apostrophe is multi-byte, so
  `analysis.?s` could not match it). Per the standing eval-variance convention the widening is over
  phrasing, **never over outcome** — the outcome guard is unchanged and nothing that pins a tool can pass.

### Tests / validation
- **`validator jargon-guard` runner self-test (the teeth of Fix 1).** Eight injections — each banned
  phrase into `skills/solve/SKILL.md` **and** into the repo-root `README.md` (the file v1.7.4's scan scope
  omitted) — must each make `validate.py` **FAIL**, and removal must restore green. Runs entirely inside
  the throwaway sandbox clone with **no `claude -p` dispatch**: deterministic, free, and non-vacuous.
- **Six new behavioural fixtures (generic `PROJ-*`), each non-vacuous:** `worktree-env-fault` (a
  near-total fresh-worktree failure is an env-fault, not a finding — while a *partial, targeted* failure
  still is one), `execute-commit-before-review` (commit precedes dispatch; an empty range triggers the
  `git diff HEAD` + `--porcelain -uall` fallback), `workdoc-solve-autopath` (committed stub → `separate`
  under `auto`), `epic-lesson-capture` (breakdown writes the epic lesson + the `EPIC LESSON:` line),
  `codify-drift-count` (the `DRIFT:` line, 5 entries / 2 tickets counted from the list), and
  `multi-clause-want` (a 2-clause want yields 2 rows; the injected single-row `✅` certification is
  flagged).
- **`scripts/validate.py`** adds six guard groups locking these fixes: `validate_worktree_env_parity`
  (env-parity / untracked / `.env` / in-place-at-reviewed-SHA / near-total / env-fault / *until proven
  otherwise* / the partial-failure carve-out, across `review` + both critic briefs + `PRINCIPLES.md`),
  `validate_empty_diff_fallback` (execute commits before review; `git diff HEAD` + `porcelain` +
  `uncommitted` in both briefs and `review`), `validate_epic_lesson_owner`, `validate_drift_count_line`,
  `validate_multi_clause_want`, `validate_solve_workdoc_route`, plus the rewritten
  `validate_maturity_labels`. Both READMEs and `PRINCIPLES.md` are updated; the v0.5 doc-consistency check
  stays green.

> **Evidence note.** Fix 1 was found in two projects; Fix 2 was hit independently by a review subagent
> and by the operator in one session. The Fix-3 items are single-observation but each has a clear shape,
> gathered here because one retro pass covers them. This version hardens the verify layer that later work
> will lean on; it adds no new surface of its own.

## [1.7.4] — 2026-07-19

Review-phase git isolation + maturity labels (Stable/Experimental) + a `work_doc_mode` guidance for
committed-stub tickets. **No new lifecycle phase.** Nothing removes a CHECK — review git-isolation
**ADDS** safety, maturity labels **ADD** honesty, and no gate is loosened. refine still **exposes, never
authors**; every decision stays a counted artifact; the human holds every gate. Generic and
stack-agnostic throughout (fixtures use `PROJ-*`); all plugin text is English-only.

### Fixed
- **Review subagents must never run stateful git in the shared working tree (Fix 1).** In a field run,
  the `reviewer` and `challenger` each ran stateful git (`git checkout <branch>`, `git stash`) in the
  **shared** working tree to run the suite against the branch — switching the main worktree off the
  feature branch onto `main`, removing the in-progress source files from disk, and leaving the working
  doc untracked. No commits were lost, but it was a real corruption + recovery detour. A review subagent
  now inspects a branch **ref-based** (`git diff <base>..<branch>`, `git show <branch>:<path>`, `git log
  <base>..<branch>`) **or** in an **isolated `git worktree`** it removes afterward, and **MUST NOT** run
  `git checkout` / `git switch` / `git stash` or any HEAD/index-mutating git in the shared working tree;
  to *run* the suite against a branch it uses an isolated worktree/clone, never the live checkout. Stated
  once in `PRINCIPLES.md` (Subagent git isolation) and in the `reviewer`/`challenger` briefs +
  `review/SKILL.md`. **Same root cause** as the shipped **v1.6.1** eval-isolation fix (a process running
  stateful git in a shared cwd) — one principle, two surfaces.
- **`work_doc_mode` guidance for committed-stub tickets (Fix 3).** For a local-file ticket that is ALSO a
  committed scaffold stub (an epic child-ticket stub committed by `breakdown`), `work_doc_mode: separate`
  (a distinct `<KEY>.work.md`) is now recommended over `auto`/`embed`: embedding the mutable working doc
  in a committed, **tracked** file leaves its edits as uncommitted changes to a tracked file, fragile to
  a stray subagent git-state op. Documented in `config/harness.example.json`, `breakdown`/`analysis`, and
  the README — **guidance + a sensible default on the epic-scaffold path, not a behavioural gate.**

### Changed
- **Maturity labels — Stable / Experimental replace the internal `v1-learning` jargon (Fix 2).** Shipped
  plugin text now uses standard maturity vocabulary. **Breakdown re-ratification is `Experimental`** —
  validated once in the field, its re-ratification trigger and granularity may change until a second epic
  exercises it; it graduates to `Stable` (recorded here as `re-ratification: Experimental → Stable`) once
  a second epic validates the trigger. Everything else on the ticket and epic paths — ticket-path
  classification (want/how), `ASSUMED` handling, the exposure-checker, epic detection, the enumerated
  INVEST self-check, and the design blast-radius trace — is **Stable**. A **Maturity** section in
  `PRINCIPLES.md` (and the README) defines both terms. The internal `v1-learning` label and `n=1`/`n=2`
  evidence jargon are removed from shipped plugin text (the evidence detail lives in the project backlog,
  not in public-facing docs).

### Tests / validation
- **`review-git-isolation` eval fixture (generic `PROJ-*`).** A review subagent inspecting a branch must
  use ref-based / worktree-isolated git and leave the shared HEAD unchanged; an injected shared-cwd
  `git checkout` / `git stash` is FLAGGED (non-vacuous) and the live checkout stays on the original
  branch.
- **`scripts/validate.py`** adds tokens locking each fix: review `ref-based` / `worktree` /
  no-`checkout`/`switch`/`stash`-in-shared-cwd across `review`/`reviewer`/`challenger`/`PRINCIPLES`;
  maturity `Stable` / `Experimental` / `graduation` + a **zero-`v1-learning`, zero-`n=1`/`n=2`** grep over
  shipped operational text; the committed-stub → `separate` work-doc guidance on the scaffold path. Both
  READMEs and `PRINCIPLES.md` are updated; the v0.5 doc-consistency check stays green.

> **Evidence note.** Fix 1 is first-field-evidence but the **same class** as the already-shipped v1.6.1
> eval-isolation fix, so its shape is not speculative. Fix 3 is a low-risk config-guidance change. Both
> are accepted at their current evidence level (the project has exhausted fresh epics that would produce a
> second data point) and their limits are recorded in the project backlog rather than held open. Fix 2 is
> a professional-labelling change for this public repo. This is the first version since the eval
> transcript-cache shipped where unchanged-skill fixtures can be reused; a `--no-cache` full run remains
> the milestone bar.

## [1.7.3] — 2026-07-18

Breakdown re-ratification + epic scaffold handoff + INVEST re-split test + a shipped CHANGELOG + an eval
transcript-cache. **No new lifecycle phase.** Nothing removes a CHECK — each change ADDS a gate/action
or accelerates the dev loop without dropping coverage. refine still **exposes, never authors**; every
decision stays a counted artifact; the human holds every gate incl. the new re-ratification. Generic and
stack-agnostic throughout (fixtures use `PROJ-*`); all plugin text is English-only.

### Fixed
- **Breakdown re-ratification when a ratified split changes (Fix A — v1, first-evidence, n=1, epic 013).**
  After the split-gate ratified, the epic gained a 7th ticket and reversed a previously-ratified decision
  — both rode in on a **child ticket's Gate 1** with no breakdown-level re-approval. `breakdown` now
  treats a ratified split as a **living plan**: a ticket added/removed or a ratified decision
  reversed/re-pointed **after** the gate triggers a **re-ratification** — surface the **delta** vs the
  ratified split as a counted artifact and get an explicit human **re-approve** at the breakdown level,
  never a silent ride-in on a child's Gate 1 (`RE-RATIFY:` counting line). Shipped at **v1 depth (n=1)**;
  the exact trigger + granularity are expected to be refined by a future epic retro — a delta-surface +
  human re-approve, not a rigid contract.
- **Commit the epic scaffold before a child ticket branches (Fix C — n=1, epic 013).** The epic
  bookkeeping (child-ticket stubs + BACKLOG/roadmap) was **created but not committed**, so a later
  child's ticket-blind `challenger` could not tell a genuine retarget-edit from net-new authorship and
  had to caveat its verdict. `breakdown` now **commits the epic scaffold to a shared ref before any
  child ticket branches**, so a child's diff reads as a real **edit of a committed file**, preserving the
  challenger's evidence.

### Tests / validation
- **INVEST "flag → re-split" ACT half now proven (Fix B — fixture).** The v1.7.2 enumerated INVEST check
  could DETECT a borderline ticket, but no run had a ticket bad enough to FORCE a re-split — the ACT half
  was untested. New `invest-force-resplit` fixture injects a genuinely oversized ticket (bundles four
  independent deliverables → fails **Small**) and asserts breakdown **flags it AND drives the re-split
  before ratification**; a right-sized control ticket is **not** split (non-vacuous).
- **Two more eval fixtures added** (generic `PROJ-*`, decision-level, emphasis-agnostic):
  `breakdown-reratify` (after a ratified split, an injected ticket-addition / ratified-decision reversal
  → breakdown surfaces the delta + requires explicit human re-approve; a change riding in on a child
  Gate 1 without breakdown re-ratify is flagged — non-vacuous) and `epic-scaffold-committed` (epic path
  → scaffold committed before any child branch; a child edit of a committed stub reads as an edit, not
  net-new).
- **Eval transcript-cache (Fix E — eval-speed).** `tests/eval/run.sh` now caches each fixture's last
  GREEN transcript keyed on `(fixture-id + skills-hash)`: a fixture whose exercised skill files are
  provably unchanged is a **cache-hit** (no `claude -p` dispatch); a changed hash (or any uncertainty)
  runs **fresh** — **fail-safe to run**, the cache only ever avoids a re-run it can prove unnecessary.
  A **`--no-cache`** flag forces a full fresh run (the milestone/release bar); the cache is git-ignored
  and stored outside the committed tree. A cheap runner self-test covers hash-match→skip /
  hash-change→run / `--no-cache`→all-run.
- **A shipped CHANGELOG (Fix D).** This `CHANGELOG.md` now ships **inside the plugin dir** (the retro
  convention's neutral source pointed at a file that did not exist there). `scripts/validate.py` requires
  it to exist under the plugin dir and carry an entry matching `plugin.json`'s version.
- **`scripts/validate.py`** adds tokens locking each fix (breakdown `re-ratification` / `delta` /
  `re-approve` / `scaffold committed before child`; run.sh `skills-hash` / `cache-hit` / `--no-cache` /
  `fail-safe to run`; the plugin-dir CHANGELOG present + version-match). Both READMEs and `PRINCIPLES.md`
  are updated; the v0.5 doc-consistency check stays green.

> Fix A (re-ratification) is **v1 / first-evidence depth (n=1, epic 013)** — expect a future epic retro
> to refine its trigger + granularity. Fixes B–E are mechanical / coverage / tooling and fully specified.
> The eval cache accelerates the dev loop only; a `--no-cache` full run remains the milestone bar.

## [1.7.2] — 2026-07-18

A three-fix patch from field-test evidence. **No new lifecycle phase.** Nothing removes a CHECK — each
change ADDS coverage (an exposure-checker on the epic path; a stricter enumerated INVEST; a wider
blast-radius). refine still **exposes, never authors**; every decision stays a counted artifact; the
human holds every gate. Generic and stack-agnostic throughout (fixtures use `PROJ-*`); all plugin text
is English-only.

### Fixed
- **Epic path must dispatch the exposure-checker (Fix A — first epic-run evidence, n=1).** On the first
  epic-path field run, refine went from surfacing wants straight to `breakdown` with **zero**
  exposure-checker dispatch — while the ticket path correctly dispatches one ticket-blind
  exposure-checker. This was backwards: an epic is where an un-exposed decision is *most* costly, yet it
  was the one path skipping the backstop. The epic path now dispatches the **SAME 1-dispatch
  ticket-blind exposure-checker** the ticket path uses, **before `breakdown`**, over the epic's exposed
  set; its findings surface for the human to ratify alongside the breakdown. One dispatch, not a debate.
- **breakdown INVEST self-check must be ENUMERATED (Fix B — first epic-run evidence, n=1).** breakdown
  emitted a single descriptive sentence per ticket labelled "INVEST", not an actual check of the six
  criteria — INVEST theatre that cannot catch a boundary problem. The self-check now **enumerates all
  six letters** (Independent / Negotiable / Valuable / Estimable / Small / Testable) per ticket, each
  affirmed with a one-clause reason or marked N/A-with-reason (mirroring analysis's rulebook-section
  coverage discipline). A ticket that **fails a letter** (e.g. not Small, not Independent) is a
  breakdown finding — **re-split before ratification**.
- **design blast-radius must trace to REAL producers/consumers (Fix C — n=2, convergent).** Two
  independent runs (a migration/type change and a data-fan-in change) both had design **under-scope**
  the change-list because its blast-radius estimate used a shallow grep (a table-name string in
  `src/**/*.test.*`; the owning page) and missed the real producers/consumers — type factories across
  all test roots, and the actual builder call sites. In both, the diff exceeded the approved change-list
  and execute's deviation-recording had to backfill it. The blast-radius step now traces to real
  producers/consumers: a shared **type/symbol** change greps by the exported name **and its
  factory/fixture patterns**, enumerates **every test root** (not just `src` — including e2e/integration
  roots), and runs **`typecheck`** as part of the design-time estimate; a **value threaded** to a
  downstream builder enumerates **every builder call site**, not just the owning surface. This tightens
  the estimate — execute's deviation-recording remains the backstop (not removed), but should rarely
  fire for a blast-radius miss.

### Tests / validation
- **Four eval fixtures added** (generic `PROJ-*`, decision-level, emphasis-agnostic): `epic-exposure-checker`
  (epic path → exactly one ticket-blind exposure-checker before breakdown, can surface an un-exposed
  decision — non-vacuous), `breakdown-invest-enumerated` (six-letter enumerated INVEST per ticket; a
  ticket failing "Small" flagged for re-split — non-vacuous), `design-blastradius-shared-type` (a shared
  type with factories in a non-`src` test root → enumerate every test root + factories + typecheck;
  shallow src-only grep missing a factory root is a finding — non-vacuous), `design-blastradius-value-threading`
  (a value threaded to a builder called from multiple sites → all builder call sites enumerated, not
  just the owning surface).
- **`scripts/validate.py`** adds tokens locking each fix (refine `epic … exposure-checker`; breakdown
  `enumerate` + the six INVEST letters + `re-split`; design `real producers` / `test root` / `typecheck`
  / `builder call site`). Both READMEs and `PRINCIPLES.md` are updated; the v0.5 doc-consistency check
  stays green.

> Fix A & B are first-epic-run evidence (n=1) — the epic path is still young; expect a follow-up epic
> retro. Fix C is n=2 convergent (two projects, two shapes, one root).

## [1.7.1] — 2026-07-17

A refine + analysis patch from the v1.7 field test (n=3, three field runs). **No new lifecycle phase**;
this tightens refine's classifier and analysis's rule coverage, and cleans up terminology. Nothing
removes a CHECK — each change makes classification/coverage more correct, not looser. refine still
**exposes, never authors**: the tie-breaker changes *which bucket* a question lands in, not whether the
human owns intent. Generic and stack-agnostic throughout (fixtures use `PROJ-*`); all plugin text is
English-only.

### Changed
- **Terminology — the classifier buckets are renamed to self-explaining English.** The two buckets
  shipped in v1.7.0 under mixed-language names are renamed **everywhere** in the plugin to
  **`want-decision`** (intent-question — the user is the sole source; refine ASKS in want-language) and
  **`how-decision`** (derivable-question — answerable from convention/code/rulebook/ticket text; refine
  RESOLVES and CITES, does not ask). Behaviour is unchanged by the rename itself.

### Fixed
- **refine classifier — a two-way tie-breaker, applied DURING classification (the n=3 finding).** All
  three field runs hit the SAME want/how boundary in three different directions, so the classifier was
  under-specified (one root cause). refine now applies, before filing a decision:
  **(a) acceptance-bar → want-decision by default, even if it looks derivable** — if the decision is
  about WHAT COUNTS AS satisfying an AC (a sourcing standard, a threshold, an evidence type), the user
  owns the bar; refine ASKS or marks it `ASSUMED`, and must NOT silently resolve it as a cited
  how-decision (Run A: settling an acceptance-bar sourcing standard as a how-decision leaked to a later
  gate). **(b) consistency/scope answerable-from-convention → how-decision, resolve-by-citation, don't
  ask** — a documented shared recipe means "apply to all consumers", a ticket's literal "insert" leans
  the answer (Runs B, C). **Guard:** an **uncited how-decision resolution is itself a gate finding** — a
  HOW settled with no source is almost always a mis-classified want-decision.
- **ASSUMED enforcement — mandatory tag + mandatory explicit next-gate confirm (recurring n=2).** A
  handed-back want-decision was sometimes tagged `ASSUMED` and sometimes recorded as settled prose and
  ratified by gate-luck. It is now **mechanically enforced**: any handed-back (or refine-assumed)
  decision **MUST** carry the `ASSUMED (awaiting ratification)` tag (settled prose is a finding) and the
  next gate **MUST** get an **explicit human confirm** before it counts as ratified — not "the gate
  happened to re-mention it."
- **analysis rule-compliance — enumerate the applicable rulebook sections by change type (n=1, a
  production-breaker).** analysis's rule-compliance step once enumerated an ad-hoc subset of rulebook
  sections and silently omitted the DB-conventions section, so a migration shipped with no GRANT
  (permission-denied in prod) and a missing soft-delete. analysis now **derives the applicable sections
  from the change type** and checks each (or marks it N/A-with-reason), emitting a counted
  `RULE SECTIONS` artifact: a migration/schema change makes the DB-conventions section mandatory, a new
  UI surface makes the design-token/a11y section mandatory, etc. Omitting an applicable section is a
  finding.

### Tests / validation
- **Four eval fixtures added/extended** (generic `PROJ-*`, decision-level, emphasis-agnostic):
  `refine-acceptance-bar-is-want` (an acceptance-bar/sourcing standard filed as want-decision/ASSUMED,
  not a silent cited how-decision; a mis-classification as an uncited how-decision is flagged —
  non-vacuous), `refine-consistency-is-how` (a scope question answerable from a documented recipe is
  resolved-by-citation, not asked), `refine-assumed-on-handback` (extended: ASSUMED tag mandatory +
  explicit next-gate confirm; settled prose flagged), `analysis-section-coverage` (a migration →
  DB-conventions section enumerated + grants/soft-delete checked; omitting an applicable section is a
  finding — non-vacuous).
- **`scripts/validate.py`** drops the old mixed-language bucket tokens and adds `want-decision`/`how-decision`
  plus tokens locking each fix (`acceptance-bar`, `want-decision by default`, `resolve-by-citation`,
  `uncited how-decision`, `next-gate confirm`; analysis `applicable …section`, `change-type`,
  `enumerate`). Both READMEs and `PRINCIPLES.md` are updated to the English bucket names; the v0.5
  doc-consistency check stays green.

## [1.7.0] — 2026-07-17

Adds a **new first phase — `refine` (Phase 0)** — to the front of the lifecycle, and an epic-path
`breakdown` phase. This is the largest change since v1.0, so right-sizing and invariant-preservation
mattered more than usual: the four existing gated phases (`analysis`→`finalise`) are **unchanged and not
renumbered** — refine slots in front as Phase 0 and holds no gate of its own. Generic and stack-agnostic
throughout — no project, ticket, library, framework, or brand is named (fixtures use `PROJ-*`).

The lifecycle is now:

```
refine → analysis → design → execute → review → finalize                       (ticket path)
refine → analysis(epic) → design(epic) → breakdown → N× ticket-lifecycles       (epic path)
```

**Depth (explicit, honest).** The **ticket-path** refine is **fully specified** (3 dry-runs). The
**epic-path** is **v1 — "enough to run and learn"**, designed to run and be corrected by retro. Field-
test both branches across projects; a retro on the epic-path is expected to refine the epic-level
analysis/design boundaries and breakdown sizing.

### Added
- **`refine` (Phase 0) — turn a raw request into a refined ticket without authoring intent.** New
  `skills/refine/SKILL.md`. It **scans the project** first (reusing `sitemap`/`db-map`) so exposure
  depth comes from the scan, not from asking what convention/code already answers. It then **tries to
  expose** the unresolved product-decisions and **the count IS the gate**: **0 → self-skip → analysis**
  (recorded `refine skipped: 0 unresolved product-decisions`), **≥1 → refine works**, **when in doubt →
  run**. Every decision is a **counted artifact** (a `REFINE:` line + the refined-ticket tables), never
  prose. refine holds **no gate of its own** — its want-decision questions are its interaction, and its
  output is challenged at Gate 1. *(refine must never become a tax on a clear ticket — the self-skip is
  the first-class behaviour.)*
- **The derivable/intent boundary — classify EVERY decision before asking.** Each surfaced decision is a
  **how-decision (HOW)** — answerable from convention/code/the rule book or a tool choice → refine
  **resolves it and CITES** the source, **does not ask** (asking a HOW-question launders a decision) — or
  a **want-decision (WANT)** — intent/priority/stakes/a genuinely new choice → refine **asks the user**
  in want-language (`AskUserQuestion` typed fork; `(Recommended)` only here). A **self-check** precedes
  every question ("can convention/code answer this? → how-decision → cite, don't ask"). This is the same
  descriptive/normative boundary `codify` holds for rules, applied to a ticket: **refine exposes for the
  human to decide and never authors intent.**
- **`ASSUMED (awaiting ratification)` on a handed-back want-decision.** "your call" is **not** silently adopted:
  refine picks per its recommendation but marks the choice `ASSUMED (awaiting ratification)` (reusing
  `codify`'s provisional→ratify), and it **re-surfaces at a later gate** to confirm once concrete. A
  **tripwire** fires if a recommendation would **reverse a prior human decision** — flag ASSUMED, never
  silent-settle.
- **Direction, not tool.** refine exposes solution DIRECTIONS a non-technical user can feel (wrap vs
  rebuild); the specific tool/library is **analysis's** job. It **splits mixed input** (an open
  brainstorm bundled with a targeted task → refine refines only the targeted part).
- **Backstop — 1-dispatch exposure-checker, not a debate.** The completeness-of-exposure check a newbie
  can't self-run reuses the **ticket-blind `challenger`** as an exposure-checker with **one** dispatch,
  asked only "is any product-decision still un-exposed?" — **not** a Council or multi-advisor debate.
- **`breakdown` (epic path, v1) — split an epic into tickets.** New `skills/breakdown/SKILL.md`,
  activated **only on the epic path, after `design(epic)`**. It draws **ticket boundaries** from the thin
  epic-level architecture, emits a **counted** ticket list with a **per-ticket INVEST self-check**, and
  **holds a ✋ human gate — the human ratifies the split before any ticket executes.** Each ratified
  ticket then runs its own full lifecycle (one ticket per run). Marked **Experimental**: ticket-boundary
  sizing has no exact metric; INVEST is the heuristic and retro corrects mis-splits (SPIDR is a
  later-if-needed, not now).

### Changed
- **`solve` wires refine as Phase 0.** The orchestrator runs `refine` FIRST and branches on what it
  finds — **skip** (0 unresolved → straight to analysis), **ticket-refine** (≥1 unresolved, single
  deliverable → refined ticket → analysis), or **epic-path** (multiple independent deliverables →
  thin analysis(epic)/design(epic) → breakdown's human split-gate → N× ticket-lifecycles). Epic-path is
  labelled Experimental in the skill.
- **`templates/ticket.md` carries the refined-ticket shape.** A new **Phase 0 — Refine** block: the
  `REFINE:` count line, and counted tables for **settled wants** (want-decision → AC constraints),
  **cited** (how-decision → starting premise), **ASSUMED (awaiting ratification)**, and **constraints surfaced from the scan**,
  plus the exposure-checker result — all above the requirements matrix, so the challenger stays blind to
  the working doc.
- **`PRINCIPLES.md`** adds "The refine phase — expose the decisions, never author the intent": the new
  lifecycle diagram, the derivable/intent (want-decision ask / how-decision cite) boundary, and the
  "refine exposes, never authors" invariant, plus the epic-path v1 note.

### Tests / validation
- **Six new eval fixtures — one per behaviour** (generic `PROJ-*`, decision-level, emphasis-agnostic):
  `refine-skip-clear-ticket` (self-skips a convention-covered ticket, no over-trigger),
  `refine-classify-A-vs-B` (how-decision resolved+cited not asked, want-decision asked in want-language,
  self-check catches a convention-answerable question as a how-decision), `refine-assumed-on-handback` (ASSUMED recorded +
  surfaced, never silent-adopt, tripwire on prior-decision reversal), `refine-direction-not-tool`
  (stops at direction, does not pin a tool), `refine-epic-detect-breakdown` (epic detected → epic path,
  breakdown emits a counted ticket list + INVEST, human-approved before execute),
  `refine-backstop-challenger` (1-dispatch ticket-blind exposure-checker, not a multi-advisor debate).
- **`scripts/validate.py`** locks each behaviour with contract tokens (`refine`
  `scan`/`want-decision`/`how-decision`/`cite`/`ASSUMED`/`skip`/`exposure-checker`; `breakdown`
  `INVEST`/`ticket boundary`/`counted`). Both READMEs and `PRINCIPLES.md` document refine + breakdown and
  the updated lifecycle diagram; the v0.5 doc-consistency check stays green.

## [1.6.1] — 2026-07-16

A safety + token patch, **no new lifecycle behaviour** (no gate, check, or phase added or removed). Three
fixes: isolate the eval from the live checkout, cut artifact re-emission into the response, and document
verify-incremental. Generic and stack-agnostic throughout — no project, ticket, library, framework, or
brand is named (fixtures use `PROJ-*`).

### Fixed
- **Eval isolation — the live checkout can never be mutated (safety).** The behavioural eval already ran
  every fixture inside a throwaway local clone (`git clone --local` into a temp sandbox, `cd` there for
  every `claude -p`, `rm -rf` on exit), so isolation was **structural** — but **unverified**. `run.sh`
  now carries a post-run **`assert_checkout_clean`** guard that asserts the **live checkout** is pristine
  after the whole eval (HEAD on `main`, no stray `*PROJ-*` branch, no `docs/tickets/*.work.md` or
  `docs/EVAL_RULES.md`); on any leak it prints the recovery commands and **fails loudly** so a leak can
  never pass silently. The guard is proven **non-vacuous** — self-tested against an injected leak in a
  throwaway repo, never risking the live checkout. Root cause of the original leak: `execute` is designed
  to mutate a project, so running it headless against the plugin's own repo made the plugin repo the
  "project" (it once stranded a commit on a `feat/PROJ-*` branch). (`tests/eval/run.sh`, eval README,
  `CONTRIBUTING.md`.)
- **Artifact delta-emission — emit the change, not the whole artifact (token).** mango re-printed large
  artifacts (working doc, ledger, matrix, proof manifest) in full into the response on each partial
  update — the dominant output-vs-input cost (a field run showed output ~50× input). On a partial update,
  the skills now emit **only the changed portion** (the new ledger row, the just-filled matrix cell) and
  **reference the unchanged rest** ("ledger **unchanged except** row N"); the full artifact is still
  written **complete on disk** to the working doc (single source of truth). This changes only what is
  re-printed into the response, never what is stored: the v1.6 **content-completeness gate** still runs
  unchanged and still blocks an incomplete on-disk ledger. (`solve`, `execute`, `finalise`, `PRINCIPLES`.)
- **Verify-incremental — affected fixture during build, full suite once at end (token).** Documented the
  build discipline: run only the **affected fixture(s)** while building a fix; run the **full suite once**
  at the end before push. Coverage is unchanged — the v1.0 bar (full suite green + each new fixture 3×
  fresh) is intact; only redundant mid-build re-runs of the whole suite are removed. (eval README,
  `CONTRIBUTING.md`.)

### Eval + validator
- New coverage: **eval-isolation-guard** (the live checkout is untouched after the full eval; the guard
  catches an injected leak — non-vacuous) and **artifact-delta-emission** (a partial update carries the
  delta, not a full reprint, while the on-disk artifact stays complete and the content gate passes).
- `scripts/validate.py`: new `validate_eval_isolation` (run.sh carries the throwaway isolation + the
  `assert_checkout_clean` guard + a non-vacuous self-test) and `validate_verify_incremental` (README +
  CONTRIBUTING document affected-fixture / full-suite-once / 3-fresh); skill-contract tokens lock the
  delta-emission discipline (`delta` / `unchanged except` / `complete on disk`) in `solve`/`execute`/
  `finalise`. 284 checks, up from 264.

## [1.6.0] — 2026-07-13

Makes the Cost ledger **honest** — surfacing usage for blocked dispatches and giving the finalise gate
**real teeth** — plus two small n≥2 fixes, from three independent v1.5 field-test retros (n=3). No new
architecture: the ledger stays **descriptive** (the gate checks *presence of a value*, never inspects,
ranks, or auto-cuts a row), critic output stays uncompressed/full-evidence, and nothing auto-installs or
auto-cuts. Generic and stack-agnostic throughout — no project, ticket, library, framework, formatter, or
brand is named (fixtures use `PROJ-*`). Each behavioural fix ships with its own eval fixture. **Scope
(explicit):** v1.6 does **not** measure main-loop tokens and does **not** pre-scope review input — the
ledger stays **dispatch-scoped by design**; this release only makes the dispatch numbers it *does*
report complete and honest, and makes the gate's teeth real.

### Changed
- **Usage-surfacing — recover tokens for blocked dispatches, or record them honestly.** A dispatch
  retrieved by **blocking** (a synchronous `TaskOutput`-style retrieval) returns **no `<usage>` block**,
  while one landing as a `task-notification` carries it — and the orchestrator **blocks on its first
  dispatch**, so that row reliably lost its tokens (a silent blank cell). `solve` now, in priority
  order: **(a)** prefers a usage-carrying retrieval path (let the dispatch land as a `task-notification`,
  or **re-query the completed task's usage record** after a blocking return); **(b)** only if usage truly
  cannot be surfaced, records the cell as the explicit **`unmeasured (blocking retrieval)`** marker —
  never a fabricated number, never a silent blank. Every dispatch row ends with a real count or that
  explicit marker. (`solve`, `templates/ticket.md`.)
- **Ledger gate — content check, not just row count (real teeth).** The finalise gate counted rows vs
  dispatches; it never checked a row actually **had** a token value, so a "complete" ledger could be
  half-blank in the data it exists to provide (it passed **vacuously 3/3** in field runs — dispatch
  count == row count every time — and its teeth had never been tested). The gate is now a
  **completeness check on content**: it blocks unless **every** dispatch row is present **and** each
  carries a **token value** — a real count or the explicit `unmeasured (blocking retrieval)` marker. A
  blank/absent token cell is incomplete and blocks exactly as an unfilled matrix column does. Still
  descriptive — it checks *presence* of a value or an honest marker, never inspects, ranks, judges,
  invents, or auto-cuts. (`finalise`, `PRINCIPLES.md`.)
- **Verify-only re-dispatch trigger — docs/bookkeeping carve-out.** The verify-only rule reverted to a
  full re-dispatch when a fix touched "any file outside the approved set" — but a fix that only edits
  bookkeeping (working doc / `config.lessons_path` / the rule-book drift-list — zero runtime surface)
  then wastefully forced a full re-review, so operators bypassed the rule. The trigger now reuses
  `finalise`'s **staleness exemption set**: a verify-only fix touching **only** exempt bookkeeping files
  stays **main-loop** (verify by inspection + the affected proof + a regression scan, no re-dispatch); a
  fix touching **any non-exempt** file outside the approved set still triggers a full re-dispatch
  (unchanged). The carve-out narrows the trigger; it never widens what a real scope change is. (`review`,
  `agents/reviewer.md`, `agents/reviewer-max.md`.)
- **Finalise — push the bookkeeping commit that carries the durable lesson.** A lesson/BACKLOG write rode
  a branch never pushed before the human merged the PR → the lesson was orphaned and never reached
  `main`. The durable-lesson / bookkeeping write must now land on a **shared ref**: either folded into a
  commit the approved **branch-push** carries before PR-open, or pushed via an explicit **"push
  bookkeeping" outward action** at the final gate — under the **same per-action approval + idempotency
  check** as every other outward action. The lesson never depends on a commit finalise never offered to
  push. (`finalise`, `templates/ticket.md`.)

### Tests / validation
- **Four new eval fixtures — one per behavioural fix** (generic `PROJ-*`, decision-level assertions):
  `ledger-content-gate` (all rows present but one token cell blank → finalise **blocks**; a value-or-marker
  in every cell proceeds — the injected, first non-vacuous test of the gate's teeth), `usage-unmeasured-marker`
  (a blocked dispatch's row shows a recovered count or the explicit `unmeasured (blocking retrieval)`
  marker, never a silent blank), `verify-only-bookkeeping-carveout` (an exempt-bookkeeping-only verify-only
  fix stays main-loop; a non-exempt out-of-scope fix re-dispatches), `finalise-lesson-pushed` (the durable
  lesson lands on a shared/pushed ref, not an orphaned local-only branch).
- **`scripts/validate.py`** locks each fix with contract tokens (`finalise` `content` / `token value` /
  `unmeasured` / `shared ref`; `solve` `unmeasured (blocking retrieval)`; `review` `bookkeeping` /
  `exempt` / `carve-out`). The build fails if any is dropped.

## [1.5.0] — 2026-07-13

Enforces the descriptive Cost ledger and fixes the verify-only lane's cost variance — two
evidence-backed levers from two independent v1.4 field-test retros (n=2) — plus two small backlog
items. No new architecture: the ledger stays **descriptive** (the new gate checks *completeness*, not
content, and never auto-cuts), critic output stays uncompressed and full-evidence, and mango still
never depends on an optimizer. Generic and stack-agnostic throughout — no project, ticket, library,
framework, or brand is named. Each behavioural fix ships with its own eval fixture.

### Changed
- **Ledger dispatch-count gate — the ledger's real teeth.** The Cost-ledger append was model-executed
  narration nothing gated on; it stayed complete in the v1.4 runs only because dispatch counts were low
  and the operator was careful — the discipline that evaporates under load. `finalise` now runs a
  **dispatch-count check** and **refuses to proceed if the ledger has fewer rows than the run's dispatch
  count** — an incomplete ledger blocks exactly as an unfilled matrix column does. It checks
  **completeness, not content**: it never inspects, ranks, or auto-cuts a row, so the ledger stays
  descriptive. (`finalise`, `PRINCIPLES.md`.)
- **Verify-only re-review is main-loop-by-default (remove the re-dispatch coin flip).** The same
  verify-only lane cost **0** tokens in one field run (main-loop re-check) and **~46,700** in another
  (it re-dispatched a reviewer) — pure operator choice, because the lane never prescribed *how* to
  verify. It now **prescribes main-loop verification** when the fixes stay inside the already-named
  findings (confirm by inspection + re-run only the affected proof + a regression scan, dispatching no
  subagent). A reviewer/challenger is **re-dispatched only when a fix changed scope** (touched a file
  outside the approved set, or introduced a new surface) — the one trigger, reverting the round to a
  full re-review. The challenger is still not repeated on a verify-only round unless scope changed.
  (`review`, `agents/reviewer.md`, `agents/reviewer-max.md`, `templates/ticket.md`.)
- **Uncodified-standard → codify nudge.** A standard applied at a gate but not codified in the rule book
  created gate-block ambiguity (unclear whether it blocks). `analysis` now **detects and surfaces** such
  a standard as an **uncodified-standard item** and nudges the human to **ratify** it via `codify`'s
  provisional→ratify flow, rather than silently enforcing or silently ignoring it — the human ratifies,
  mango never authors the rule. (`analysis`, `codify`.)

### Docs
- **Codified the multi-run eval-variance convention** (practised since v1.0, now written down in a new
  `tests/eval/README.md`): every new assertion matches the decision (not one phrasing), tolerates
  markdown emphasis, and passes 3× fresh before it counts green; widen over wording/emphasis, never over
  outcome. Documentation of existing practice, not a behaviour change. Guarded by `validate.py`.

### Tests / validation
- **Three new eval fixtures — one per behavioural fix** (generic `PROJ-*`, decision-level assertions):
  `ledger-gate` (an incomplete ledger blocks finalise; a complete ledger proceeds), `verify-only-main-loop`
  (an in-scope verify-only round runs in the main loop with no re-dispatch; a scope-changing fix is the
  only re-dispatch trigger), `uncodified-standard-nudge` (a standard applied without a codified rule is
  surfaced for ratification, not silently enforced).
- **`scripts/validate.py`** locks each fix with contract tokens (`finalise` `dispatch-count` /
  `ledger complet`; `review` `main-loop` / `re-dispatch` / `changed scope`; `analysis`+`codify`
  `uncodified` / `ratif`) plus a new `validate_eval_convention` check that the convention text exists.
- **Applied the newly-documented convention to one existing assertion:** the `red-baseline`
  "recorded exclusion" guard was widened to tolerate markdown emphasis around "not"
  (`does **not** block`) — over emphasis only, never over outcome (a wrong outcome still fails).

## [1.4.0] — 2026-07-12

Makes the descriptive **Cost ledger** honest and mechanical, and closes two ledger/review gaps found
by two independent budget-ledger field retros (n=2 on the core findings). No new architecture — five
fixes sharpen the v1.3 ledger and the v1.2 review lane; the ledger stays **descriptive** and `budget`
stays **detect-not-administer** (no auto-install, no optimizer dependency, no critic-output
compression). Generic and stack-agnostic throughout — no project, ticket, library, or brand is named;
the optimizer names (RTK / Headroom / Caveman) are the generic classes the safety axis reasons about.
With `token_optimizer` at its defaults a run is otherwise identical to v1.3.

### Changed
- **Ledger auto-append — one row per dispatch return (stop the coin flip).** The Cost ledger was
  narration the model was asked to maintain "as you go", so it could silently not-happen (an unenforced
  artifact is a coin flip). It is now a **mechanical by-product of dispatching**: a ledger row is
  **emitted per subagent-dispatch return**, transcribed from that return's usage block — a run that
  dispatched N subagents ends with N rows. (`solve`, `templates/ticket.md`, `PRINCIPLES.md`.)
- **Dispatch-only honesty — no fabricated dispatch-vs-noise split.** The ledger measures **subagent
  dispatch only**; main-loop output noise (verbose lint/test/build dumps, file reads) is **not measured
  by mango**. The finalise summary now declares this plainly and does **not** present a
  dispatch-vs-noise percentage as if both were counted (that split is an instrumentation artifact, not
  a finding); for the output-noise side it points at the optimizer's own analytics (`rtk gain`). Each
  layer measures its own domain. (`finalise`, `budget`, `PRINCIPLES.md`.)
- **Verify-only re-review is consistently cheap (not a coin flip).** A conditional-LGTM verify-only
  round must **carry forward round-1's verified facts** (requirement reconstruction, the passing
  proving test, layer-match verdicts, baseline) and **re-run only the proof affected by the named
  fixes** plus a regression scan — never re-derive requirements or blanket-re-run the full
  build/lint/tsc/test suite unless a fix changed scope. The cheap path is now the default, not luck.
  (`review`, `agents/reviewer.md`, `agents/reviewer-max.md`.)
- **Drop the false-precision ledger label.** A dispatch return surfaces a single figure with no in/out
  split, so the ledger column is labelled plainly **`Tokens`** — not `Tokens (out)` or `(in / out)`.
  (`templates/ticket.md`; guarded by a new `validate_ledger_label` check.)
- **`budget` prints how to wire RTK (inform, still don't administer).** When RTK is present but
  **unwired**, `budget` now additionally **prints the exact wiring command** (its canonical `rtk
  init`-style hook setup) with an explicit note that **the user must run it** — it edits their global
  Claude Code config, and mango will not. Detect + inform usefully; never execute, install, or edit the
  global config. (`budget`.)

### Tests / validation
- **Five new eval fixtures — one per fix** (generic `PROJ-*`, decision-level assertions): `ledger-auto-append`
  (one row per dispatch return, emitted mechanically), `ledger-dispatch-only-honesty` (dispatch-only,
  no fabricated split, points at `rtk gain`), `verify-only-scoped` (reuse round-1 facts + re-run only
  the affected proof), `ledger-label` (no `(out)` over an unsplit metric), `budget-rtk-wire-guidance`
  (prints the wiring command + "you run this, not mango", administers nothing).
- **`scripts/validate.py`** locks each fix with contract tokens (`solve` `per dispatch`; `finalise`
  `dispatch-only` / `not measured` / `rtk gain`; `review` `reuse` / `only the proof affected`; `budget`
  `wire` / `you must run this` / `dispatch-scoped` / `rtk gain`) plus a new label-sanity check.
- The `ledger-descriptive` fixture's sample table is aligned to the single-`Tokens` label.

## [1.3.1] — 2026-07-12

Eval-truth patch — no skill behaviour changes. The `red-baseline` fixture previously narrated a red
baseline in prose while the sandbox's `config.test_command` was `true` (always green), so a correct
detect-not-assume run *measured* green and the assertion missed, while any pass came from the model
**narrating** "red" off the ticket rather than measuring it — green for the wrong reason. This release
makes the baseline **genuinely** red so Fix #3 is actually exercised.

### Changed
- **`red-baseline` fixture now measures a genuinely red baseline.** `tests/eval/run.sh` parameterizes
  the sandbox harness on `test_command` (`write_harness`) and, for the `red-baseline` fixture only,
  points it at a **committed pre-existing failing check** (`tests/baseline/verify.sh`, exits non-zero
  on a clean checkout on an item outside the ticket's area), then restores the green default. The
  fixture ticket no longer carries any fabricated command output, and the failing-item detail
  (`pdf_snapshot_spec` / snapshot drift / sub-pixel / "1 failed") lives **only** in the command output
  — so its presence in a transcript proves the baseline was **measured, not narrated**.
- **Decision-level assertions for `red-baseline`:** detects `baseline: red` **by measuring** (observed
  failing item appears) + DoD is delta-green + the pre-existing failure is a recorded exclusion that
  neither blocks forever nor silently passes. A run that reads "red" off the ticket without running the
  command now fails.

## [1.3.0] — 2026-07-11

Makes mango's token cost **visible and measurable** and adds a human-gated way to adopt an external
token optimizer with its safety trade-offs explicit — without mango ever installing one, depending on
one, or letting one weaken a critic. Cost was always an **estimate**, never measured per-phase; this
release measures first (`context ≠ correctness` applied to optimization: don't optimize what you
haven't measured), then gates adoption behind a human choice exactly as `codify` gates the rule book.
Generic and stack-agnostic throughout — no project, ticket, library, or brand is named; the optimizer
names (RTK / Headroom / Caveman) are the generic classes the safety axis reasons about. Backend
behaviour is otherwise unchanged, and with `token_optimizer` at its defaults a run is identical to
v1.2.

### Added / Changed
- **Cost ledger (descriptive measurement).** The run records token usage **per phase and per subagent
  dispatch** (reviewer, challenger, extractor, Explore fan-out, each review round) into the working
  doc as a **facts-only** counted artifact (new *Cost ledger* block in the working-doc template);
  `solve` records rows as it goes and `finalise` surfaces a one-line summary (total + top cost driver).
  It is **descriptive, never normative** — it makes cost visible so a *human* can decide where to trim;
  it never itself cuts a check, a gate, a critic, or evidence detail. It is also the data a later
  middle-tier sizing decision needs — measure before you size. `PRINCIPLES.md` documents it.
- **`budget` skill (detect + inform + human-gate optimizer adoption).** New `skills/budget/SKILL.md`,
  mirroring `codify`'s descriptive + human-gated shape: it **detects** which optimizers are present
  (installs nothing), **informs** per a fixed **safety axis** (an optimizer is safe only if it removes
  representation redundancy — how output is phrased — never a check, gate, critic, or the evidence a
  critic relies on), **human-gates adoption** into a `token_optimizer` block in `.harness.json` as a
  **recorded provisional decision** (ratified like `codify`), and **reports** each enabled optimizer's
  estimated/measured saving in the ledger (measure the optimizer, don't trust its claim). It never
  installs, never makes mango depend on an optimizer, and never silently changes what a critic emits.
- **RTK default-expect (below mango; degrade cleanly).** The default `token_optimizer.rtk: "expect"`
  means mango **tolerates** RTK rewriting Bash-command output (git/test/lint/ls) into a compact form —
  it does **not** install RTK and does **not** require it. RTK absent → everything runs **identically**
  (only the saving is lost); mango never fails, blocks, or changes a decision on RTK presence/absence,
  and no mango logic parses an RTK-specific format in a way that breaks without it. `doctor` may note
  RTK presence as one **informational** line (never a gating ✅/⚠/❌).
- **Caveman critic guardrail (HARD — invariant).** Caveman-style output compression **must never** be
  applied to critic output — the `reviewer`, `reviewer-max`, `challenger`, and any gate-blocking
  artifact — which **must retain full evidence detail** (`path:line`, measured values, per-clause
  verdicts). The three critic agent briefs carry the guardrail; Caveman, if enabled, is **scoped to
  non-critic output only** (`caveman.scope: "non-critic-only"`, enforced). `PRINCIPLES.md` states the
  rationale: terse critic output loses the evidence that *is* the review's value; brevity is never
  applied where a false-green could hide (the retro-#5 class).
- **Config, validator & docs.** New `token_optimizer` block in `config/harness.example.json` (with the
  two hard-pinned invariants). `scripts/validate.py` adds the `budget` skill contract (detect / inform
  / recorded / never-install / degrade-clean / non-critic-only tokens), a `token_optimizer` schema
  check (rtk expect, `output_shaper` false, caveman non-critic-only), and a critic-guardrail token
  check across the three critic agents (build fails if the Caveman-critic prohibition is dropped). Both
  READMEs and `PRINCIPLES.md` document `budget`, the safety axis, the RTK expectation, and the ledger;
  the v0.5 doc-consistency check stays green.
- **Eval coverage (one fixture per guarantee).** Four generic fixtures (`ledger-descriptive`,
  `rtk-degrade`, `caveman-critic-guard`, `optimizer-adoption-gated`) assert: a run records a
  facts-only per-phase/subagent ledger and surfaces a finalise summary without auto-cutting; an
  RTK-absent run completes identically with no changed decision; critic output keeps `path:line`
  evidence and the guardrail forbids terse critic output; enabling an optimizer lands in `.harness.json`
  as a recorded provisional choice. Fixtures are generic (`PROJ-*`); the eval coverage header is updated.

## [1.2.0] — 2026-07-11

Four evidence-backed fixes from field retros #4 and #5, gathered into one minor. No new architecture
— all four refine existing mechanisms. Each ships with its **own** generic eval fixture so a red run
pinpoints which fix regressed. Generic and stack-agnostic throughout — no project, library,
framework, formatter, or device is named. Backend behaviour is otherwise unchanged.

### Added / Changed
- **`execute` — design-conformance self-check (scope discipline on BOTH axes).** The verification
  sweep now measures scope on **two axes**: the **file set** (the existing `diff ⊆ approved list`
  sweep) **and** conformance to the **approved design behaviour**. `execute` walks **each Gate-2
  Approach bullet**, classifies it `implemented-as-approved | deviated`, and any `deviated` bullet is
  **recorded as a deviation** (reusing the Phase-3 deviation record) traced to its approved bullet and
  surfaced to `review` — **even when every touched file is inside the change-list**, so the file-set
  sweep passes clean. `review`'s scope reconciliation re-confirms the behaviour axis and treats a
  missed behavioural deviation (or a feature self-marked `✅` that was not implemented) as **not
  clean**. `PRINCIPLES.md` §3 states the two axes. *(Observed, retro #5: Gate 2 approved a behaviour
  in writing, execute implemented something different and recorded no deviation because no file left
  the change-list — a green counted artifact sitting over a wrong behaviour; only the reviewer,
  re-reading the design, caught it.)*
- **`analysis` — vague acceptance value → falsifiable at Gate 1.** Each acceptance value must be
  either **falsifiable** (a measurable/greppable definition, not a vague adjective) **or** recorded as
  an explicit **manual-check exclusion** (unmeasurable → human-verified, logged up front as a
  coverage-gap exclusion). One that is **neither** is flagged by the AC-validation step and **may not
  carry a matrix `✅`** — a bare self-reported `✅` can no longer stand in for an unmeasurable or
  unbuilt thing. Ties into the existing AC-validation + coverage-gap-exclusion machinery; no parallel
  mechanism. `PRINCIPLES.md` §1 documents it. *(Observed, retro #5: a vaguely-worded requirement was
  self-marked `✅` without being implemented, because nothing forced the vague word to a testable
  form.)*
- **Red/flaky baseline vocabulary (`analysis` + `execute` + `review`).** A first-class,
  **project-supplied** baseline: `analysis` runs the verification command once on the untouched
  checkout and records `BASELINE: green | red | flaky` (with the specific failing items). A clean
  checkout is **not** assumed green. When `baseline ≠ green`, the Definition of Done becomes **prove
  the delta is green** — the change introduces no new failure and fixes any it claims to; a
  pre-existing failure outside the change is a **recorded baseline exclusion**, neither a blocker nor
  a silent pass. `execute` proves against the baseline; `review`/`finalise` compare against it, never
  against a blanket "all green". mango **detects and records** the baseline; it never decides which
  pre-existing failures are acceptable (a human/rulebook call, logged). New `BASELINE` field in the
  working-doc template; `PRINCIPLES.md` §4 documents it. *(Observed, n=2: the verification command was
  unsatisfiable on a clean checkout — a pre-existing/flaky failure — and mango had no vocabulary for a
  red/flaky baseline, so the operator improvised "baseline red, my delta green" in every phase.)*
- **`review` — conditional LGTM + verify-only re-review.** Round 1 may return a **conditional LGTM**
  ("LGTM once findings 1–N land as described"); the re-review is then a **verify-only pass** — confirm
  the N named fixes are present + a regression scan — **without** a full requirement re-derivation. The
  ticket-blind `challenger`'s full re-derivation runs **once** and is **not repeated** on a verify-only
  round unless a fix changed scope (its independence is the value; its cost is not paid twice for pure
  re-confirmation). A reviewer may still demand a full re-review if a fix touched something material.
  The `reviewer`/`reviewer-max` briefs describe the conditional-LGTM option. *(Observed, n=2: a round-2
  review after CHANGES REQUESTED was ~100% re-confirmation yet cost a full reviewer+challenger
  re-derivation.)*
- **Eval coverage + validator lock.** Four generic fixtures (`behavioural-drift`, `vague-requirement`,
  `red-baseline`, `conditional-LGTM`) — one per fix, so a red run is diagnosable — assert: a
  behavioural deviation is recorded despite a clean file diff; a vague AC is pinned to a measurable or
  logged as a manual-check exclusion and cannot carry a bare `✅`; a pre-existing failure yields
  `baseline: red` with a delta-green DoD; a conditional LGTM leads to a verify-only re-review.
  `scripts/validate.py` now requires the `analysis` `falsifiable`/`manual-check`/`baseline`, `execute`
  `approved design`/`both axes`/`baseline`, and `review` `conditional`/`verify-only`/`baseline`
  tokens, so none can silently regress. Both READMEs and `PRINCIPLES.md` document all four; the v0.5
  doc-consistency check stays green.

## [1.1.0] — 2026-07-10

One evidence-backed refinement from field retro #4 — the **format-scope rule** — plus the
previously-unreleased eval assertion-robustness work, shipped together. No new architecture; the fix
is one proven refinement to the existing surgical discipline. Generic and stack-agnostic — **no
formatter is named**. Backend and non-frontend behaviour is otherwise unchanged.

### Added
- **`execute` — the format-scope rule, stated explicitly.** `execute` now states it: run the
  project's formatter **only on the files this change authored or edited**; **never** reformat a
  shared or pre-existing file wholesale. A whole-file format pass rewrites lines outside the change
  and reads as scope creep at review; whole-file conformance is a **separate concern** — CI, or a
  dedicated chore ticket — never folded into this ticket's diff. It is the existing untouched-lines /
  surgical discipline (Principle 3) applied to the formatter, not a parallel rule. `review`'s scope
  reconciliation now names a wholesale reformat of a shared file as **not clean**; `PRINCIPLES.md`
  (Principle 3) and both READMEs document it. *(Observed, retro #4: a whole-file format pass over a
  shared file reformatted untouched lines → review flagged scope creep → the reformat was reverted →
  the next whole-file pass re-collapsed it — a real, recurring loop. The by-hand resolution — format
  only the authored/edited files — was not stated as a rule, so it recurred.)*
- **Eval coverage + validator lock.** A generic `format-scope` fixture asserts `execute` scopes the
  formatter to the authored/edited file and does **not** wholesale-reformat the shared file present
  beside it. `scripts/validate.py` requires the `execute` `format[ -]scope` token so the rule cannot
  silently regress.

### Changed
- **Eval assertions hardened to decision-level + emphasis-agnostic.** Assertions now match the
  *decision* (outcome token + reasoning token both required) and tolerate markdown emphasis (`**`/`_`)
  and phrasing variants around the load-bearing token, so a correct behaviour passes under any wording
  while a wrong *outcome* still fails. The `lite: TIER lite` regex was the last brittle instance
  (`TIER:[[:space:]]*lite` → `TIER:[[:space:]*_]*lite`); the stale-review assertions were widened the
  same way earlier. Widening is over *wording/emphasis only*, never over outcome — every assertion
  still fails on a wrong tier / a missed exemption / an honoured bare "go".
- **Certified stable across independent fresh runs.** `tests/eval/run.sh` was run **6 consecutive
  times end-to-end**, each regenerating transcripts — all **33/33**, no assertion failing on any run.
  Green now reflects run-to-run stability, not a regex tuned to a single already-produced transcript.
- **READMEs document the assertion-robustness property** in their eval sections (both the root and
  plugin READMEs).

## [1.0.0] — 2026-07-08

The **official 1.0 release**. Three evidence-backed sharpening fixes from the latest field retro —
all refinements to existing mechanisms, no new architecture — plus the stable-API milestone. Generic
and stack-agnostic throughout; backend and non-frontend behaviour is unchanged.

**Release status (honest).** The public skill/config API is **stable**. mango has been proven
end-to-end across multiple real projects and two stacks **by its author**, with a green behavioural
eval suite and fault-injected escalation paths. **Independent-operator validation is ongoing** and
its results will be folded into later releases.

### Fixed
- **`execute` frontend track — one assertion PER CLAUSE of a multi-clause M-gate.** A multi-clause
  rubric gate (M4 = touch-target `size ≥ 44×44 px` **and** `spacing ≥ 8 px`; M7 = focus indicator
  `visible` **and** `contrast ≥ 3:1`) is only proven when **every clause** carries its own assertion.
  `execute` now enumerates **one assertion per clause** and the proof manifest carries **one row per
  clause**; a clause with no assertion makes the gate **incomplete → it blocks, exactly as a missing
  surface does**. This generalizes the per-item-inventory rule (which prevents aggregate-count hiding)
  from surfaces to the clauses of a gate. `templates/frontend-rubric.md` names the clauses of each
  multi-clause gate; `execute` enumerates them and invents none. *(Observed: an M4 proof asserting
  only the size clause shipped green while a real 0 px-gap spacing failure went unproven.)*
- **`design` — mechanical test blast-radius sub-step in the Gate-2 plan.** Before closing the change
  list, `design` now **mechanically enumerates the existing assertions the change will invalidate** —
  grepping for the copy keys, headings, route shapes, or exports being changed — and **folds each hit
  into the approved change list as up-front proof collateral**. This converts a predictable execute
  deviation (an existing test asserting an old string) into a planned Gate-2 item. *(Observed: a
  change reworded a heading an existing shell test asserted; the change list never mentioned that
  test, so it surfaced only as an execute deviation.)*
- **`version-check` — follow `source` to the plugin's own `plugin.json` when the manifest has no
  `version`.** A marketplace manifest often carries no `version` field — the version lives in the
  plugin's `plugin.json`. Step 2 now follows the plugin's `source` path to its `plugin.json` and reads
  the version there instead of dead-ending at "not specified". Still **detect-and-inform only** — a
  read, never a self-update. *(Observed: the skill dead-ended on a version-less manifest and the
  operator had to fetch the published `plugin.json` by hand.)*
- **Validator + eval locked to the new semantics.** `scripts/validate.py` now requires the `execute`
  per-clause token (`(per|each) clause`), the `design` `blast[ -]radius` token, and the `version-check`
  `plugin.json` fallback token, so none can silently regress. Two generic fixtures added
  (`per-clause`, `blast-radius`): an M4 proof asserting only size marks the spacing clause unproven and
  **blocks Gate 2** while a both-clause proof passes; a string-altering change lists the affected
  existing test in the Gate-2 change list as collateral.

## [0.9.1] — 2026-07-07

Test-infra / docs only — **no skill behaviour changes**; the 27 behavioural assertions stay green,
now runnable by anyone in one command. Closes the "eval repeatable-by-others" gate.

### Added / Changed
- **"Running the eval" note in the README.** Documents the local one-command run
  (`bash tests/eval/run.sh`) for a second person cloning the repo: it works with **either** an
  exported `ANTHROPIC_API_KEY` **or** an OAuth/subscription login, sets up and tears down its own
  throwaway environment, runs against the shipped skills via `--plugin-dir`, and prints
  `N/N assertions pass`. The auth-agnostic guard and self-scaffolding runner themselves shipped in
  0.8.1; this makes the hands-free, any-auth path explicit for local operators, not just CI.

## [0.9.0] — 2026-07-07

Makes the finalise **stale-review guard** mechanical. The guard already *behaved* correctly — it lets
a working-doc bump through, refuses on a source change, and resists a bare "go" — but only because the
model **reinterpreted** the step-1 prose. Read literally, that prose dead-locked every full-tier run:
its "if commits landed after the reviewed SHA" clause always matches, because the commit that records
`Reviewed at <sha>` necessarily lands *after* the SHA it names. This replaces judgment-dependent prose
with a deterministic rule. No change to what fires — only to how the rule is stated.

### Fixed
- **Stale-review guard is now a file-set test, never a commit-count test.** `finalise` step 1 computes
  the changed set (`git diff --name-only <Reviewed-at-sha>..HEAD` ∪ working-tree diff), **exempts** the
  working-doc / bookkeeping path(s) — derived deterministically from `work_doc_mode`/`work_dir` and the
  path now recorded with the marker — and is **stale iff any remaining source file is beyond the
  reviewed set**. The "any commit after the SHA" criterion is deleted, so the marker/bookkeeping bump
  can no longer dead-lock the guard. A bare "go" still never clears it; only a fresh `Reviewed at`
  marker covering the current tree does.
- **Marker now records the working-doc path.** `review` writes the working-doc path alongside the
  `Reviewed at <sha>` marker + reviewed-file set, making finalise's exemption unambiguous.
- **Docs + validator synced.** `solve` and `PRINCIPLES.md` describe the guard mechanically (source
  beyond the reviewed set = stale; working doc exempt). `scripts/validate.py`'s `finalise` contract now
  also requires the `beyond the reviewed set` and `exempt` tokens, so the rule cannot regress to a
  commit-count phrasing.
- **Eval coverage (both directions).** Two generic fixtures added: a working-doc/marker-only bump must
  **proceed** (the regression test for the literal dead-lock, which occurred on every full-tier run),
  and a source file changed beyond the reviewed set must **refuse**, route back to `review`, and resist
  a bare "go".

## [0.8.1] — 2026-06-28

Test-infra only — **no skill behaviour changes**. Makes the behavioural eval
(`tests/eval/run.sh`) runnable by anyone with one command, regardless of how they authenticate.

### Fixed
- **Eval runnable via OAuth or API key.** The runner required `ANTHROPIC_API_KEY` and rejected a
  perfectly capable OAuth/subscription session. The guard now verifies the *capability* to run
  `claude -p` — API key, else a non-interactive `claude auth status` check, else a minimal capability
  probe — and only fails (naming **both** options) when none works. Never rejects an OAuth session.
- **Hands-free self-scaffolding.** `run.sh` now sets up its own throwaway environment (an isolated
  local clone + a temp gitignored `.harness.json` + a minimal rule book) and runs the fixtures against
  the **shipped** skills via `--plugin-dir`, so a fresh clone exercises what the repo ships rather than
  whatever the operator has installed. Everything is removed on exit (`trap`), and fixtures that
  `execute` can only mutate the throwaway clone — the live checkout is never touched.
- **CI uses the same single code path.** `eval.yml` still just runs `bash tests/eval/run.sh` (API key
  from the secret in CI, OAuth locally) — no CI-only branch.

All fixtures and assertions are unchanged.

## [0.8.0] — 2026-06-27

Surface-coverage + tiered UI proof, built **on top of** the v0.7 frontend gates (reusing `track`,
`TIER`, the layer-match hard gate, the per-AC verification plan, the counted-artifact pattern, the
opt-in `sitemap`, and the existing exclusion record — no parallel mechanism). On two real frontend
field tests the full pipeline went **green and still shipped broken UI** — under *opposite* harness
conditions (one with full e2e, one with none). The shared root cause was **not** weak proofs: it was a
**wrong denominator on the surface axis** — the verification counted the surfaces the *ticket* named,
while the failures lived on reachable surfaces the ticket never mentioned. A green gate proved the
wrong N. Generic and stack-agnostic throughout — no framework, library, test-runner, product, or
device specifics ship. Backend is untouched, and a frontend ticket with no integration/runtime AC runs
exactly as in v0.7.

### Added / Changed
- **S1 — Surface coverage: N comes from the CODE, not the ticket (the fix).** For a universal /
  app-wide frontend requirement (no horizontal scroll, reflow, focus-visible, contrast — anything
  phrased all/every/no or inherently page-wide), `analysis` enumerates **every reachable surface**
  (route / full-window overlay / modal / major mounted state) from the code surface — the opt-in
  `sitemap` (`config.docs_dir/sitemap.md`) if present, else a read-only "enumerate reachable views"
  sub-step — and emits a counted, challenger-checkable `SURFACES: N`. The ticket's examples are a
  **hint, never the denominator**. New surface-inventory slot in the working-doc template; validator
  requires the `analysis` `SURFACES` token. *(Observed: "I tested the surfaces the ticket named" passed
  the gate while reachable surfaces the ticket never mentioned shipped broken.)*
- **S2 — Elastic proof tier: e2e optional, a proof not.** A frontend AC's risk-layer proof is
  satisfied by the **highest available tier**, recorded per surface in a **proof manifest** beside the
  verification plan: `PASS(automated)` (tier-1, satisfying the **C1–C8** automated-proof contract by
  composing the *project's* declared runner — detected from declared test scripts / `config.test_command`,
  **mango bundles none**) → `PASS(render@<bp>)` (tier-2, a recorded render of the real surface at the
  breakpoint asserting the visible measurable — a **first-class proof, NOT an exclusion**, the cheap
  reality-facing check both field tests were missing) → `EXCLUDED(approver, reason)` (only when neither
  tier is reachable; reuses the v0.6/T2 exclusion record). `execute` **never stops for a missing
  runner** — it scaffolds tier-1 per the new runner-agnostic `templates/ui-proof-scaffold.md`, else
  records a tier-2 render proof, else an exclusion. Dropping a tier because there is no runner is fine;
  dropping to *nothing* blocks the gate. Validator requires the `execute` `render` / `proof-manifest` /
  `ui-proof-scaffold` tokens. *(Observed: with no test runner, the proving-test gate degraded to a
  silent exclusion instead of demanding the one cheap proof that exists — render the surface and look.)*
- **S3 — Counted `N == M + X` gate + loud banner.** `design` lays out the verification plan / manifest
  **one row per (AC × affected surface)**; `review`'s challenger scores each entry (tier-1 vs C1–C8,
  tier-2 vs the render-proof contract) and **re-runs ≥1** tier-1 `proof-cmd` (or confirms a tier-2
  render artifact) to defeat fabricated entries. With `N` = |surfaces|, `M` = surfaces with a valid
  PASS (any tier), `X` = recorded EXCLUDED, **the gate passes iff `N == M + X`** — otherwise
  `design`/`review` emit `⚠ surfaces proven: k/N — <uncovered> have no proof; cover or record an
  exclusion` and block, as unmissable as an unfilled matrix column. The challenger keeps its
  ticket-blindness: it re-enumerates surfaces from the branch code rather than reading the working-doc
  manifest. Under `TIER=lite` the re-run lightens to confirming command/artifact presence — coverage,
  the manifest, and a proof per surface stay mandatory. New generic eval fixtures assert the `k<N`
  block and the no-runner `PASS(render@<bp>)`. Validator requires the `review` `proof-manifest` /
  `surfaces proven` tokens. mango **owns** the coverage rule, tier ladder, manifest schema, and
  scaffold spec; it **composes** the runner and bundles none.

## [0.7.0] — 2026-06-27

A new **frontend track**: an opt-in gate set for UI work, riding the v0.6 layer-match hard gate
rather than forking it. The design boundary throughout is **own the durable, compose the volatile** —
mango embeds only UI knowledge that is **measurable or greppable** (a11y thresholds, token-first,
conformance to a per-project `DESIGN.md`) and **composes, never owns,** the aesthetic-generation
layer: it calls an external taste skill if one is installed, else follows `DESIGN.md`, and **never
stops because a taste skill is missing.** mango blocks on a missing *number*, never on a missing
aesthetic. The backend path is unchanged: a `track=backend` ticket runs exactly as in v0.6. Generic
and stack-agnostic throughout — no framework, library, product, or device specifics ship.

### Added / Changed
- **F1 — `track` config + TRACK artifact (orthogonal to TIER).** New `track`
  (`backend|frontend|fullstack`, default `backend`) selects which gate set applies; `analysis` emits
  `TRACK: … — k/N touched files under UI paths` as a **counted artifact** the challenger can check,
  using `config.track` or inferring from touched-file paths. `track` is **orthogonal to TIER** (TIER
  = process weight, track = which gates), so a ticket may be `track=frontend` + `TIER=lite`;
  `fullstack` applies both gate sets. When a declared `breakpoints` width is a small viewport, the
  width-parametric gates (M2/M3) are noted in scope. New optional `breakpoints` and `design_doc_path`
  keys. New `TRACK` field in the working-doc template; validator requires the `analysis` `TRACK`
  token.
- **F2 — per-project `DESIGN.md` contract.** On the frontend track, `design` creates/updates a
  `DESIGN.md` (at `config.design_doc_path`) from a new `templates/design-doc.md`: palette derives
  from **domain meaning first, general rules second** (a blanket "ban colour X" yields to a domain
  term that denotes that colour); a **shell** (character-rich) vs **data-core** (tables/grids/charts,
  legibility-first, static) split; and a generic **Responsive & touch** section (declared
  breakpoints, narrow-width navigation pattern, which regions collapse vs reflow vs
  scroll-in-container, thumb-zone, motion). These are project **choices** the gates are scored
  against — they live in `DESIGN.md`, never gated by mango. Validator requires the `design`
  `DESIGN.md` / `data-core` / `responsive` tokens.
- **F3 — falsifiable a11y/token + M1–M10 responsive/touch rubric.** A new
  `templates/frontend-rubric.md` the `review` skill injects into the reviewer/challenger brief when
  track includes frontend (the agents stay generic — no per-track fork). Every item is **falsifiable**
  (measurable or greppable) and scored **against `DESIGN.md`** — "is it tasteful?" is out of the
  rubric. Core items (token-first, no hardcoded hex/px, semantic HTML, state-not-by-colour-alone,
  reduced-motion) plus the **M1–M10** gates (viewport/zoom, no horizontal scroll at each breakpoint +
  the 320 px floor, reflow @320 px, touch-target ≥ 44×44 px, input-zoom ≥ 16 px, tap/hover parity,
  focus-visible, contrast, safe-area, pointer-input parity). Constants (44/24 px, 16 px, 4.5:1,
  320 px) are **standards**, not config.
- **F4 — frontend ACs ride the layer-match hard gate (reused, not forked).** A
  "renders/responsive/contrast/a11y" AC has an integration/runtime (or `document`/`computed-style`)
  risk layer; a unit-only proof against a mocked DOM is a layer-match `❌` and **blocks Gate 2** —
  clearing only with a proof against a **real rendered DOM** (or the served document for the
  viewport-meta gate) or a recorded human-approved coverage-gap exclusion. A **risk-layer floor**
  puts `document`/`computed-style`/`integration-runtime`/`behavioral` all above the logic/unit layer.
  `review` re-confirms no frontend AC closed clean on a layer-mismatched proof. `execute` goes
  **token-first** (all colour/spacing/radius/font through tokens; no scattered hex/px) and
  **input-agnostic** (Pointer Events, no affordance gated solely on `:hover`). **M10 degrades
  gracefully:** an always-on greppable smell (mouse-only / hover-only) can block, while the
  best-effort pointer/touch dispatch-assert runs only when the environment can — else it is recorded
  as a coverage-gap exclusion and never wedges the gate. New generic eval fixtures assert the @320 px
  unit-proof block and the hover-only/mouse-only flag. Validator requires the `execute`
  `token-first`/`pointer` and `review` `a11y`/`DESIGN.md`/`touch-target` tokens.

## [0.6.0] — 2026-06-24

Four fixes from a real run where the gates caught a 4× scope explosion but one of the most
load-bearing checks was **advisory, not binding** — so a worthless proof was allowed to stand. The
theme of this release is mango's own binding contract made literal: prose and self-declared columns
do not bind; only an emitted artifact that **blocks a gate** binds. Every fix is generic and
stack-agnostic; no existing behaviour was removed.

### Added / Changed
- **N1 — Layer-match becomes a hard gate (was advisory).** `design`'s per-AC verification plan now
  requires the **layer-match column to be filled before the proving test is named**, and the rule is
  **binding**: if an AC's **risk layer is integration / runtime / e2e and its proof sits at the
  logic/unit layer**, that row is `❌` and **Gate 2 is blocked** — it passes only when the proof is
  upgraded to the matching layer **or** the row is recorded as a human-approved coverage-gap
  exclusion. The gate keys on the **risk-layer vs proof-layer comparison** (a wording cue —
  "renders / runs / dispatches / persists / sends" — only hints at the risk layer; it is never
  keyword-triage). `review` re-confirms no AC closed clean on a layer-mismatched proof. `PRINCIPLES.md`
  Principle 4 now reads "enforced, not advisory", and `scripts/validate.py` requires the `design`
  binding wording (`layer-match` + a blocking token). *(Observed: a runtime acceptance criterion was
  backed only by a logic-layer unit proof; it passed and proved nothing, because the per-AC
  layer-match check existed but was advisory.)*
- **N2 — Stale-review guard in `finalise`.** A clean review is scoped to the commit it covered.
  `review` now records a **`Reviewed at <sha>` marker** (commit SHA + reviewed files) on a clean
  verdict; `finalise` compares the live `HEAD`/diff against it **before any outward action** and
  **refuses** to open a PR — routing back to `review` for a re-review covering the new diff — if
  commits landed or files changed beyond the reviewed set. A bare "go" does not override a stale
  review. `solve` carries the reviewed SHA across review→finalise and marks the review stale if
  `execute`/`design` re-ran after it. New `Reviewed at` slot in the working-doc template; validator
  requires a `finalise` stale token. *(Observed: a clean review covered a small diff, the diff then
  grew, and finalise opened the PR on the stale review.)*
- **N3 — "Outgrew its ticket" nudge.** `solve` (with light checks in `analysis`/`design`/`execute`)
  tracks the declared `SCOPE`/`TIER`. If at any gate the **realized** scope crosses up a tier
  (especially S/M → L), or the change-list/diff materially exceeds the approved one, mango **stops at
  the next gate** and asks the human to either formally **re-scope** (updating the working-doc scope,
  and the branch/PR type if the change type drifted) or **split** the excess into a follow-up — never
  silently absorbing the expansion. The re-declaration is recorded in the Decision log; validator
  requires a `solve` outgrew/re-scope token. *(Observed: a small card's realized scope grew
  several-fold mid-flow and the working doc absorbed it silently, with the change type drifting from
  the branch type.)*
- **N4 — `init` resolves the config-file commit policy.** After writing `.harness.json`, `init`
  **asks** whether it should be **committed** (shared team config) or **kept local**: on "local" it
  adds `.harness.json` to `.gitignore` (creating it if absent) and tells the user; on "committed" it
  leaves `.gitignore` untouched but warns that secrets never belong in the config (they live in a
  gitignored `.env`). It does not hard-gitignore by default — the config is often shared, so the human
  decides — and never writes secrets into the config file. A note was added to the README Operational
  notes. *(Observed: the per-project config sits at the repo root, so honouring "don't commit it" was
  manual vigilance on every commit.)*

## [0.5.0] — 2026-06-23

The largest feature since v0.1: a facilitated way to **bootstrap a project's rule book** when it is
missing, thin, or inconsistent, plus **opt-in descriptive maps** of the code surface and the database
schema. This closes the single biggest adoption blocker — the rule book the whole plugin grounds in.
Everything here honours one boundary: **mango generates the descriptive and facilitates the normative,
but never authors the normative.** Generic and stack-agnostic throughout; the descriptive maps are
opt-in and never core.

### Added
- **A — `/mango:codify` (facilitated rule/convention definition).** New `skills/codify/SKILL.md`
  observes and **counts** the conventions the code and schema actually use — across generic code
  dimensions (error handling, naming/case, layering, validation, logging, imports) and database
  conventions (table/column naming, timestamps, soft-delete, FK on-delete policy, raw-SQL vs ORM,
  migration style) — flags dimensions with **no dominant pattern** as "no consistent rule found", then
  **asks the human to choose** each going-forward standard. It presents counts as **data** (it may
  state "the majority is X") but **never picks, recommends, or defaults to** any option, and **never
  authors** a rule. Chosen standards are written to `rulebook_path` tagged
  **`PROVISIONAL (awaiting ratification)`** and stay provisional until the human **ratifies** them; an
  optional drift list of diverging files may be emitted as tech-debt. Read-only on code — it changes
  no code. `doctor` now **suggests** `/mango:codify` (suggest only) when the rule book is missing or
  looks thin. `PRINCIPLES.md` states the observe/facilitate/never-author boundary authoritatively.
  *(Observed: with no real rule book, the reviewer/challenger produced generic, low-value output; the
  fix is to help define the standard without mango inventing it.)*
- **B — Opt-in descriptive adapters `/mango:sitemap` and `/mango:db-map`.** Two **descriptive-only**
  skills generate regenerable **facts** (never normative rules), off unless configured and **not** part
  of the lifecycle. `sitemap` maps the code surface (routes/endpoints + modules) via an optional
  `code_map_cmd`; `db-map` maps the schema (tables, columns+types, primary/foreign keys, indexes,
  relationships, views/procedures) via `db_kind` + either `db_introspect_cmd` or `migrations_path`,
  writing to `docs_dir` — read-only, it alters no schema. The *normative* database conventions live in
  the `codify` rule book, not in these maps. Light optional wiring: **if a `db-map` exists**, `analysis`
  may widen the Phase-1 blast radius to schema dependents (columns, FKs, dependent views/procs) — used
  if present, never required; the lifecycle runs fully without either adapter. *(Observed: mango had no
  view of the code surface or the database — where the costliest mistakes live and where the
  reviewer/challenger are blindest — yet schema maps are too stack-specific to be core.)*

### Changed
- **Config.** New optional, generic, commented keys in `config/harness.example.json`: `docs_dir`,
  `code_map_cmd`, `db_kind`, `db_introspect_cmd`, `migrations_path` (all `null`/off by default).
- **Validator.** `scripts/validate.py` skill-contract checks now require the `codify` boundary tokens
  (counting, PROVISIONAL/ratification, does-not-author/recommend). A new **documentation-consistency
  check** asserts that every `skills/*/` directory is named in the plugin README, that the README
  references no `/mango:` skill that does not exist, and that every key in `harness.example.json` is
  documented in the plugin README — failing the build on any doc drift.
- **Docs synced to reality.** The plugin README now carries the full skill inventory (incl. `codify`,
  `sitemap`, `db-map`), an explicit agent inventory, the complete config-key list (incl. the new keys
  and `update_check_url`), and the boundary one-liner; `PRINCIPLES.md`, `plugin.json` `description`, the
  marketplace `README.md`, and the root README were brought into line.

## [0.4.1] — 2026-06-23

A small, high-value patch from a real run where a preflight reported green while a stale plugin
version was silently loaded, and where a counted "for each of N" requirement shipped with its tail
incomplete. Every fix is generic; mango still **detects and informs, never self-administers** — it
does not install, reinstall, reorder a registry, or run plugin administration on your behalf.

### Added / Changed
- **L — `doctor` surfaces the running version.** `doctor`'s **first output line** is now the
  authoritative running-version signal — `mango <version> @ <base path>`, read from the running
  manifest and base path — with the plain note that a green doctor does **not** prove the intended
  version is loaded, and that a version should be resolved from the host (not by working around the
  loader from a restricted/remote channel). If the base path carries a version segment that differs
  from the manifest, `doctor` emits a mismatch ❌. `doctor` stays **offline**: no network call, no
  reading or editing of any host plugin registry, no install. *(Observed: a preflight passed while a
  stale version ran silently behind it, because the check validated config but never showed which
  version was actually loaded.)*
- **M — Counted "for each of N" requirements become a verified per-item checklist.** `analysis` now
  records a "do X for each of N" requirement as a **per-item checklist** (one row per item) in the
  inventory, not a single aggregate row; `review` verifies it **item-by-item** and is not clean until
  **every** item is confirmed (or each unconfirmed item is a recorded, human-approved coverage-gap
  exclusion) — an aggregate "k/N" alone is insufficient. The working-doc template's inventory gains a
  per-item checklist table. *(Observed: a counted "for each" requirement passed an aggregate check
  with the tail incomplete; only an independent reviewer caught it.)*
- **V — Opt-in `version-check` skill (informs, never updates).** New `/mango:version-check`: reads
  the running version and, **only if** the optional `config.update_check_url` (a raw URL to the
  published marketplace manifest) is set, fetches it to compare against the latest published version.
  When a newer version exists it **prints** the exact host `/plugin` commands to update — it never
  runs them, never installs, and never edits any registry. With `update_check_url` unset it makes no
  network call. New optional `update_check_url` key in `config/harness.example.json`. *(Observed: no
  in-tool way to learn a newer version existed without doing forbidden admin from a restricted
  channel.)*
- **Operational notes (README) + validator.** The plugin README gains an **Operational notes**
  section: plugin administration is the host's job, verify the live version from `doctor`'s first
  line, and use `version-check` to learn of newer versions. `scripts/validate.py` skill-contract
  checks now require the running-version / base-path tokens in `doctor`, item-by-item / per-item
  verification tokens in `review`, a `for each` token in `analysis`, and the `version-check` skill's
  frontmatter, so the new behaviours cannot be silently dropped.

## [0.4.0] — 2026-06-22

Five fixes validated across more than one project and stack. Each describes a generic failure mode
and a universal mechanism — no project, framework, tracker, tool, or filename is baked in. No
existing behaviour was removed; the full tier is unchanged.

### Added / Changed
- **G — Tier triage on the resolved denominator N, not on keywords.** `analysis` now keys the
  lite/full decision on the **resolved inventory denominator N** (from the Phase-1 numbered
  inventory), not on the literal presence of universal wording. A requirement that *sounds* universal
  ("all/every/no") but resolves to **N = 1** is lite-eligible — a single-site change already covers
  "all". `quick`'s hard entry check aligns: it refuses on a universal requirement only when **N > 1**.
  *(Observed: a universal-sounding requirement that resolved to one site forced full tier where lite
  would have sufficed, spending the challenger/reviewer budget on confirmation, not findings.)*
- **H — Project-supplied finalise-checklist hook.** New optional `config.pr_checklist_path` points at
  a project-owned checklist (e.g. a PR-template or definition-of-done file). When set, `finalise`
  reads it before drafting the PR body, walks each item, reports it satisfied / not-satisfied / N-A
  with evidence, and surfaces any unmet item at the final gate. mango supplies the mechanism; the
  project supplies the content. `doctor` warns if the key is set but the file is missing.
  *(Observed: a ship-time requirement mango cannot know was caught only by a project's own checklist,
  not by mango's generic finalise.)*
- **I — Coverage-gap exclusion for proof-tier mismatches.** `design`'s per-AC verification plan now
  requires any row whose proof tier sits below its risk layer to EITHER upgrade the proof OR be
  recorded as a **named, human-approved coverage-gap exclusion** (item · risk tier · why deferred ·
  follow-up). `review` treats a challenger "not met" that corresponds to a recorded exclusion as
  **not a blocker** — an *unrecorded* gap still blocks. New "Coverage-gap exclusions" slot in the
  working-doc template. *(Observed: a requirement whose real risk sat at an integration/behavioural
  tier was only unit-proven, so the challenger's "not met" read as a hard failure when it was a
  proof-tier mismatch.)*
- **J — Conditional working-doc placement (still challenger-blind).** New `config.work_doc_mode`
  (`auto | separate | embed`, default `auto`). A tracker-hosted ticket gets a separate
  `<work_dir>/<KEY>.work.md` (v0.3 behaviour). When the ticket is **itself a local file in the repo**,
  `auto`/`embed` append the working doc to that file **below a clear raw-ticket separator line** — one
  file, no duplicate. `analysis` chooses placement; `review` builds the challenger payload from the
  raw ticket portion only (above the separator) + the diff, never the working-doc portion — the
  challenger-blindness guarantee holds in both modes. *(Observed: a separate working-doc file
  duplicated a ticket that already lived as a repo file.)*
- **K — Full field set on tracker reads.** `analysis` now requests a full field set on a ticket read
  (honouring an optional `config.tracker.fields`, else a sensible default of
  description/body, type, labels, parent, priority) so one read returns the ticket body. *(Observed: a
  tracker read defaulted to a minimal field set and returned an empty description, wasting re-fetches.)*
- **Validator.** `scripts/validate.py` skill-contract checks now require `denominator` in `analysis`,
  `coverage-gap` in `design` and `review`, and `checklist` in `finalise`, so the new behaviours
  cannot be silently dropped.

## [0.3.1] — 2026-06-21

Hardening patch from a review of the built plugin — closing gaps where v0.3 behaviour was asserted
but not *guarded* or *evaluated*. No existing behaviour was removed.

### Added / Changed
- **F1 — Behavioural eval now covers the v0.3 behaviours.** `tests/eval/run.sh` previously exercised
  only `analysis` happy-path artifacts. It now also asserts, via headless `claude -p` (still gated to
  `workflow_dispatch`): proof at the risk layer (`design` marks an integration-layer AC proved only
  by a unit test as a layer-match `❌` and demands an integration/e2e proof), the ticket-blind
  `challenger` catching an unmet AC as "not met" with `path:line`, the design-invalidated escalation
  (STOP + re-open Gate 2), and the stuck-detector (STOP + escalate at the threshold). New generic
  fixtures `design-layer.md` and `challenger-unmet.md`.
- **F2 — `cost_tier: max` has a real Opus-reviewer mechanism.** Because a skill cannot re-pin a
  subagent's model at runtime, the Opus upgrade is now a **choice of agent**: new
  `agents/reviewer-max.md` (identical role/rules/output to `reviewer`, `model: opus`). `review`
  dispatches `reviewer-max` when `cost_tier == "max"` AND the diff is high-stakes (security-tagged,
  or touching auth / data access / schema migration), else `reviewer`; never a Haiku reviewer.
  `PRINCIPLES.md` replaces the vague "upgrade to Opus" wording with this concrete rule.
- **F3 — Right-sizing & escalation are guarded, not advisory.** `quick` gains a **hard entry check
  (step 0)**: it REFUSES and routes to `solve` if the ticket is security-tagged, touches more than
  one file, or has a universal ("all/every/no") requirement. `validate.py` skill-contract checks add
  `TIER` + `design[ -]invalidat` to `solve` and `stuck` to `quick`, so the routing/escalation
  behaviours can't be silently deleted.
- **F4 — Wider reserved-name guard.** `validate.py` `RESERVED_NAMES` now also rejects
  `claude-code-plugins`, `claude-plugins-official`, `anthropic-marketplace`, `anthropic-plugins`, and
  `agent-skills`. `mango-plugins` still passes.

## [0.3.0] — 2026-06-21

Retrospective-driven hardening. Unlike v0.2 (predicted risks), these six fixes come from **two real
mango runs**. Each fix cites the observed failure that motivated it. No v0.2 behaviour was removed.

### Added / Changed
- **A — Proof at the risk layer + per-AC verification plan.** `design` Phase 2 now emits a
  verification-plan table (`AC | risk layer | proof artifact | layer-match? ✅/❌`); the proving test
  must sit at the layer where the requirement can fail, and **Gate 2 may not pass with any ❌**.
  Principle 4 in `PRINCIPLES.md` and the ticket template updated. *(Observed: a store unit test
  passed while the integration-layer feature was broken — Gate 2 cleared on a false green; and an
  "in-browser confirm" verification artifact surfaced only at Gate 4.)*
- **B — Spike novel library/runtime assumptions before Gate 2.** `design` adds an **Assumptions**
  step (`verified | novel-untested`); a `novel-untested` third-party/runtime assumption must be
  resolved by a recorded **spike** or an integration/e2e-shaped proving test before Gate 2.
  *(Observed: a design leaned on the untested "two live rich-text editors coexist" assumption — the
  exact thing that broke.)*
- **C — Execute escalation / re-gate.** `execute` defines a **"design invalidated"** STOP: when a
  test proves the approved approach can't work, execute stops, records the finding, surfaces options,
  and **re-opens Gate 2** (re-passing A + B) — never continues with a known-broken approach. `solve`
  defines the `execute → (design-invalidated) → design re-gate` transition. *(Observed: execute found
  the Gate-2 approach unworkable but mango had no defined transition; the operator improvised.)*
- **D — Stuck-detector / circuit-breaker.** `execute` and `quick` STOP and escalate after `K` failed
  attempts at the same failing-test signature (default `K=3`, configurable `stuck_threshold` in
  `.harness.json`); the counter resets when the signature changes. *(Observed: ~7 attempts against
  the same failing e2e before escalating.)*
- **E — Finalise captures a durable lesson on every run.** `finalise` now asks for a durable lesson
  (constraint / wrong assumption / process gap) **independent of deferred rows** and writes it to
  `config.lessons_path` as a repo artifact, never only personal memory. Reinforced in `PRINCIPLES.md`.
  *(Observed: a durable constraint nearly never reached `LESSONS.md` because there were no deferred
  rows to hang it on.)*
- **F — Working doc separated from the ticket spec.** The working doc moves to
  `<config.work_dir>/<KEY>.work.md` (default `work_dir` = `tickets_dir`), a distinct file never
  appended to the ticket spec; the `challenger` payload provably excludes it. `analysis`, `review`,
  `solve`, the template, `PRINCIPLES.md`, and `challenger.md` updated — independence is now backed by
  a path separation (still procedural, not cryptographic). *(Observed: the ticket file doubled as the
  working doc, so challenger independence was a convention, not structure.)*
- **Validator.** `scripts/validate.py` skill-contract checks now require `risk layer` + `Assumptions`
  in `design`, a stuck/escalation token + a "design invalidated" token in `execute`, and
  `durable lesson` in `finalise`.

## [0.2.0] — 2026-06-20

Architecture-review hardening. Each item closes a specific adoption risk; no full-tier v1 behaviour
was removed.

### Added
- **IMP-1 `/mango:init`** — bootstraps `.harness.json` (detect stack read-only, interview only for
  the undetectable, mark guesses `UNVERIFIED`) and scaffolds a single-file starter rule book
  (`skills/init/rulebook-template.md`) when none exists. `rulebook_path` may now be a **file or a
  directory** (reviewer/onboarder read all `*.md` in a directory).
- **IMP-2 `/mango:doctor`** — health-checks `.harness.json` with a ✅/⚠/❌ checklist and exact
  remediation; `solve` gains a fail-fast preflight that refuses to start while any ❌ remains.
- **IMP-3 Right-sizing** — `analysis` declares `TIER: lite | full`; new `/mango:quick` lite lane
  (two human gates, reviewer-only, no challenger/matrix/fan-out); `solve` routes by tier.
- **IMP-4 Freeform tickets** — `analysis` synthesizes the matrix, sets `STRUCTURE: synthesized`, and
  forces a Gate-0 confirmation of the reading.
- **IMP-5 Behavioural guard** — `validate.py` adds per-skill contract token checks; optional
  `tests/eval/` harness (`run.sh` + fixtures) and a manual `eval.yml` workflow.
- **IMP-6 Honest independence** — `review` builds the challenger's input explicitly (re-fetched raw
  ticket + diff only); `challenger.md`/`PRINCIPLES.md` state the independence is procedural.
- **IMP-7 Cost knob** — `explore_fanout` config key (default `true`); lite tier always skips
  fan-out; README cost-profile note.
- **IMP-8 Model delegation** — routing map + the "Opus decides, Sonnet executes, Haiku gathers"
  principle in `PRINCIPLES.md`; `cost_tier` config key (`economy|standard|max`, default `standard`);
  a Haiku-pinned read-only `agents/extractor.md` for bulk read-and-extract; `analysis`/`execute`/
  `review` honour `cost_tier` and run shell directly (no model). `reviewer`/`challenger` stay on
  Sonnet (upgradable to Opus, never Haiku); lite tier runs on a single model.

## [0.1.0] — 2026-06-20

Initial release. The cheap, installs-anywhere core of the mango ticket-lifecycle harness.

### Added
- **Marketplace** `mango-plugins` with the `mango` plugin (`source: ./plugins/mango`).
- **Six gated lifecycle skills:** `analysis`, `design`, `execute`, `review`, `finalise`, and the
  `solve` orchestrator — each grounded at runtime in `.harness.json` and `PRINCIPLES.md`.
- **Three read-only agents:** `reviewer` (rule-book verdict), `challenger` (ticket-blind), and
  `onboarder` (wayfinding).
- **Templates:** the per-ticket working doc and the PR body.
- **`PRINCIPLES.md`** — the binding contract: think before coding, simplicity first, surgical
  changes, goal-driven execution.
- **`config/harness.example.json`** — the per-project contract users copy to `.harness.json`.
- **Production hygiene:** stdlib-only `scripts/validate.py`, a GitHub Actions `validate` workflow,
  `.gitignore`, MIT `LICENSE`, and two READMEs.

### Out of scope (planned for v2)
- Stack-specific building-block skills (trace / new-module / db-patch / modernize).
- The enforcement layer (write-time hooks, a CI static-check mirror, a worktree fleet).
