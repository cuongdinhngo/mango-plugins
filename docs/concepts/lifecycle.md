# The mango lifecycle

> **In 30 seconds.** How one ticket moves through mango: `refine`, five gated phases, the lite lane, the
> epic path, and the artifacts each phase leaves behind. The trust rules behind it are in
> [the protocol](../PROTOCOL.md); setting a project up is in [Set up a project](../howto/set-up-a-project.md).
> **Status:** Implemented in 1.21.0. Experimental parts are listed in [`principles/maturity.md`](../../plugins/mango/principles/maturity.md).

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
- **challenger** — a ticket-blind agent that reconstructs the requirements from the raw ticket alone,
  then judges the diff against them and reports met / not met / can't tell. It never sees the working doc, the design, or **the PR body**
  (`gh pr view` and equivalents are forbidden while challenging), so it can't rubber-stamp.
- **TIER** — process weight (`lite | full`); **track** — which gate set (`backend | frontend`).
  Orthogonal.
- **Counted line** — a one-line, prefixed, machine-parseable count a phase emits (`SECTIONS:`,
  `HANDLES:`, `EXCLUSIONS:`, `CLAIMS:` …). It ships in exactly **one** grammar, and the **harness parses
  it** — `scripts/check_lines.py` reads the working doc and verdicts every line for internal
  contradiction, absence when the phase required it, and off-grammar drift. Its **exit status is the
  verdict**: `0` clean, `2` a failed or missing line (the gate does not close), `3` **not-checkable** — a
  line mango ships no grammar for, an undeclared phase, an unreadable doc. `not-checkable` is never a
  pass. The checker **reports and never rewrites**, ships no counted line of its own, and where it cannot
  run at all the run records `check-lines: could-not-run` and does not claim to have checked. Run it
  yourself any time:

  ```
  python3 <mango>/scripts/check_lines.py check docs/tickets/<KEY>.work.md
  python3 <mango>/scripts/check_lines.py grammars     # the canonical form of every shipped line
  ```

  An all-zero line is a valid line, so a first ticket on an empty project pays nothing for this.

## Where mango's own contract lives

**Where mango's own contract lives.** `plugins/mango/PRINCIPLES.md` is the always-loaded core — the four
principles, the `<mango>` path-resolution order, and the model-delegation map. The rest of the contract sits
in `plugins/mango/principles/*.md`, each file read **on demand** by the phase that applies it under an
explicit read instruction in that skill, so a run pays only for the contract it actually uses. Each skill's
frontend-only rules likewise live in `skills/<name>/frontend.md`, read when `config.track` includes
frontend. Every mango-shipped path resolves through the documented order — `${CLAUDE_PLUGIN_ROOT}` when the
host sets it, else the plugin root located from the loaded skill file, else a read-only search — so no
shipped file depends on one host variable.

## The phases

Run the whole thing with `/mango:solve`, or invoke a phase directly. mango stops and waits at every ✋
gate. For an **unattended** run, `/mango:autorun <KEY>` runs the same phases and closes each gate from
the artifacts they emit, stopping at the PR — the merge stays a human. The lifecycle is:

```
refine → analysis → design → execute → review → finalize                       (ticket path)
refine → analysis(epic) → design(epic) → breakdown → N× ticket-lifecycles       (epic path)
```

## Phase 0 — `refine` (expose the decisions, never author the intent)

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
`PREMISE: <r> reference(s) checked | <m> missing | <a> ambiguous (surfaced, not blocking)`,
zero included.

refine stops at solution **DIRECTIONS** (wrap vs rebuild), never the specific tool — that is analysis's
job. Its completeness backstop is the **ticket-blind challenger as a 1-dispatch exposure-checker**, not
a debate — and it runs on **both paths**: on an epic it dispatches **before `breakdown`**, so the epic
(costliest place for an un-exposed decision) is never the one path that skips the backstop. It holds **no gate of its own** — its want-decision questions are its interaction and its
output is challenged at Gate 1. **refine exposes for you to decide; it never authors intent** (the same boundary
`codify` holds for rules). An **epic** input routes to the epic path (below).

## Tiers — right-sizing the rigor

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
| `/mango:analysis` | 1 → Gate 1 | Requirements matrix (C/R/G/AC) with counts, falsifiable-AC check (a value that is neither falsifiable nor a recorded manual-check exclusion is flagged and may not carry `✅`), root-cause & blast radius, a `RULE SECTIONS` coverage line (applicable rulebook sections from **two sources, union** — derived from the change type, e.g. migration → DB-conventions mandatory, **and** any section carrying a `handle:` this run's `RECALL:` line surfaced, so a rule promoted from a lesson can actually become applicable; 0 recalled handles adds 0 sections. Each is answered by naming what in *this* change the rule constrains, or `N/A because <reason>` — a bare `✅` with nothing named is not an answer; a `PROVISIONAL` section is surfaced but never gate-blocks as if codified), scope, and a `BASELINE` capture from the untouched checkout. A ratified **multi-clause** want-decision is split into **one matrix + proof row per clause** (a clause with no row of its own is a finding). Frontend: emits `SURFACES: N` for universal requirements. Surfaces any **uncodified standard** into `codify`'s provisional→ratify flow rather than enforcing it silently. |
| `/mango:design` | 2 → Gate 2 | Approach + rejected alternatives, assumptions (`verified \| novel-untested`), smallest row-traced change list, rule compliance, the named proving test, and a **per-AC verification plan whose layer-match is a hard gate** (an integration/runtime AC backed only by a logic-layer proof blocks Gate 2 unless upgraded or recorded as a human-approved coverage-gap exclusion). Its **test blast-radius traces to real producers/consumers** — a shared type/symbol change enumerates every test root + factory patterns + `typecheck`, a threaded value enumerates every builder call site — so the change-list is the smallest **complete** set and a shallow name-grep miss is a finding. Frontend: builds/updates `DESIGN.md`, plans one row per (AC × surface). |
| `/mango:execute` | 3 (autonomous) | Branch, the approved changes only, the proving test, a verification sweep on **both axes** — file set (diff ⊆ approved list) **and** a design-conformance self-check that records any deviation from a Gate-2 bullet even when the diff is clean — with a baseline-aware DoD, commits carrying no AI co-author trailer. Formats **only authored/edited files**. **Commits the change-set BEFORE review is dispatched**, so the ref-based review sees a real committed diff. STOPs to re-gate on an invalidated design or via a **stuck-detector** (`stuck_threshold` failed attempts at the same signature). Frontend: emits the proof manifest. |
| `/mango:review` | 4 (stop if not clean) | `reviewer` + ticket-blind `challenger` (each waivable separately), evidence-provenance refusal (test evidence from a tree that is not the one under review is refused), scope reconciliation on both axes (file set **and** behavioural conformance), regression check, layer-match re-confirmation, proving-test result judged against `BASELINE`, `k/N` coverage. A round-1 **conditional LGTM** makes the re-review a **verify-only pass** (named-fix check + affected proof + regression scan, no full re-derivation), re-dispatching a subagent only when a fix changed scope. Frontend: also scores the M1–M10 rubric + `N == M + X` surface check. On a clean verdict records a `Reviewed at <sha>` marker for the stale-review guard. Subagents inspect **ref-based or worktree-isolated**; a worktree used to *run* a suite must **carry the untracked env** (or run in place at the reviewed SHA), and a **near-total** worktree failure is an **env-fault, not a finding**. An **empty** `<base>..<branch>` range falls back to `git diff HEAD` + `git status --porcelain -uall` before concluding no-change. |
| `/mango:finalise` | 5 → final gate | **Stale-review guard** (routes back to `review` only if a source file changed beyond the reviewed set), optional `pr_checklist_path` walk, PR draft, per-action approval for every outward action, tracker writes via CLI, a **cost-ledger completeness gate**, follow-up tickets for deferred rows, and a **durable lesson** captured to `lessons_path` and pushed to a shared ref — then the **learning loop** on it: split into atomic claims → classify (a proposal) → recurrence/supersession → a **falsification check in front of** the ratification gate → each promotion **proposed** into a **project** file and ratified per claim. No lesson edits a mango skill. |
| `/mango:quick` | lite lane | Single combined pre-code gate → execute → reviewer-only check → final gate, for trivial tickets. Runs exactly two reads from the full lane — the advisory `RECALL:` and the `RULE SECTIONS:` coverage (reused, not reimplemented) — so a **directly-invoked** lite ticket reads the lesson corpus it writes to at `finalise` instead of only feeding it. Both close with zeros on an empty corpus. No challenger, matrix, fan-out or baseline. |
| `/mango:breakdown` | epic path (after design(epic)) | Splits an epic into tickets from the thin epic-level architecture: a **counted** ticket list with a per-ticket **enumerated six-letter INVEST** self-check (each of Independent/Negotiable/Valuable/Estimable/Small/Testable affirmed or N/A — a one-liner is a finding; a ticket failing a letter is flagged for **re-split**), held at a **✋ human gate** — the human ratifies the split before any ticket executes. Each ratified ticket then runs its own full lifecycle. **Boundary sizing is corrected by retro; the re-ratification behaviour is Experimental.** |
| `/mango:autorun` | unattended orchestrator | Runs the **same** phases as `solve` and closes each gate from the artifacts they already emit, instead of waiting for a human to type "go" — five waits become one, and that one is the merge. **No gate is removed** (the review seat included) and **there is no auto-merge**: the run stops when the PR exists. Takes one handover authorisation naming exactly two outward actions (push the branch, open the PR); everything else is on the abort list. `j > 0` stops the run — every unaffected part is still finished and the open question is reported. Writes three envelope artifacts: a machine-written **`RUN CONTRACT`** (fixed grammar, parsed back before the run starts, every condition declaring a statement, origin, `derived-by`, value and runnable `check`; the `force-broken` / `force-holding` fields were retired in 1.14.0; `${PLACEHOLDER}`s bound at Gate 2), a harness-run **`RECONCILE`** at t0 **and** at close (three floor conditions the agent may not author: the PR is readable, a **tree** comparison, and nothing stranded unpushed), and a **`DISCLOSURE`** list read first in the morning. |
| `/mango:solve` | orchestrator | Runs `refine` (Phase 0) FIRST and branches — **skip** / **ticket-refine** / **epic-path** — then a Doctor preflight and every gated phase in order honouring `TIER`, holding each gate; resumes from `Session status`. Raises an **"outgrew its ticket" nudge** — if realized scope crosses up a tier (S/M → L) or the diff materially exceeds the approved list, it stops to re-scope or split. |

Unattended runs are in [Unattended runs](./unattended-runs.md); the frontend gates in
[Frontend track](./frontend-track.md).

## Epic path — thin by design

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
[Maturity](../../plugins/mango/principles/maturity.md)) — and it **commits the epic scaffold** (child stubs + BACKLOG) to a shared ref
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

## Subagent git isolation

A review subagent reads the branch by ref or in an isolated worktree that carries the untracked env, and
never mutates the shared working tree. The rule is [`principles/git-isolation.md`](../../plugins/mango/principles/git-isolation.md).

## What the artifacts look like

`analysis` decomposes the ticket into a counted matrix, and the count is itself the gate — sections
found MUST equal sections decomposed:

```
SECTIONS: 7 found (Context, Scope, AC, Non-goals, Risks, Rollout, Metrics) | 7 decomposed
ROWS: C=2 R=7 G=3 AC=4
```

`review` fills a `k/N` on **every** matrix row and requires `k = N` to call the change clean, with
each shortfall named as a human-approved exclusion rather than waved through. An aggregate total is
deliberately not sufficient on its own — a "for each of N" requirement is checked item by item,
because a passing total can hide an incomplete tail. Frontend surface coverage blocks with its count
visible:

```
surfaces proven: 11/12
```

The ticket-blind `challenger` rebuilds the requirements from the raw ticket alone and returns a
numbered table — every item **met** / **not met** / **can't tell**, each with a `path:line` — then a
one-line summary:

```
1. AC-3  password reset invalidates the old token   met        src/auth/reset.ts:88
2. R-5   audit log entry written on failure         met        src/audit/log.ts:22
3. AC-4  rate limit applies to the reset endpoint   not met    —

14 requirements: 13 met, 1 not met, 0 can't tell
```

That output is never compressed — the per-requirement verdict and its evidence must survive in full.
On a clean verdict, review writes a `Reviewed at <sha>` marker into the working doc, so a later
commit can't quietly inherit an old review.

> These show the *shape* of the artifacts; exact fields depend on your project and ticket.
