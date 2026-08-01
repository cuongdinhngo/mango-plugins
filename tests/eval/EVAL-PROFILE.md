# Eval profile — full instrumented run, v1.7.6

> **Status.** This is a **measurement record of the suite as it stood at v1.7.6**, kept as the evidence
> base for v1.8.0's eval work. Of its four recommendations (§4): **(1) parallel dispatch with
> per-worker sandboxes** and **(2) the five brittle assertions** shipped in **1.8.0**; **(3) the four
> merges** and **(4) the validator-overlap set** were deliberately **not** taken — once dispatch is
> parallel, their ~9.5 min is noise against the ~2 h 34 m parallelism removes, and each merge would
> trade a distinct non-vacuity proof for seconds. Numbers below describe the sequential runner and are
> not re-measured per release; the timing table is the input to the scheduler's longest-first ordering.

Milestone run of `bash tests/eval/run.sh --no-cache` at HEAD `0bcafa9` (v1.7.6), 2026-07-31 21:35:25 → 2026-08-01 00:31:55 (+07:00). Two goals in one pass: VERIFY the behavioural suite, and MEASURE it so the trim + parallel-dispatch work has evidence behind it.

No fixture was trimmed, merged or edited. The only change to `run.sh` is measurement instrumentation, gated on `MANGO_EVAL_PROFILE` and a complete no-op when unset (see the last section).

---

## 1. VERIFY verdict — behaviourally GREEN

| | |
|---|---|
| Fixtures | 57 (all dispatched fresh) |
| Fixture-less scenarios (`run_prompt`) | 7 |
| Total `claude -p` dispatches | 64 |
| Assertions | 199 (173 on dispatches + 26 dispatch-free self-tests) |
| Result | **194 pass / 5 fail** |
| Behavioural regressions | **0** |

All 5 failures are assertion-wording brittleness over behaviour that is demonstrably correct in the transcript. Every one was re-run once to classify it (`tests/eval/.transcripts/` holds run 1; the re-run transcripts are in the session scratchpad).

| # | assertion | run 2 | classification | what the model actually did |
|---|---|---|---|---|
| 1 | `frontend-layer: layer-match ❌` (regex `❌`) | **PASS** | flap | Run 1 wrote the verification table to the work doc and summarised in prose — "layer mismatch on all 9 verification rows", Gate 2 BLOCKED, demanded a `render@320` proof. Correct; just no ❌ glyph in the response text. |
| 2 | `epic-scaffold: committed before any child branch` (regex `before .{0,24}(child\|branch)`) | **PASS** | flap | Run 1 said "**after** the human ratifies … and **before** the first child ticket runs `git checkout -b`". The markdown bold `**before**` breaks the `before ` + space match. |
| 3 | `refine-consistency: NOT asked as a want-decision` | FAIL again | reproducible brittleness | Run 1: "did **not** put it to you as an open want" — 23 chars inside a `.{0,20}` window. Run 2 expressed it as a count: `0 want-decision asked`, tie-breaker branch (b) cited. Behaviour right both times; the regex demands a negation phrase the skill emits as a zero-count. |
| 4 | `breakdown-invest: ticket failing Small is flagged for re-split` (regex `small`) | FAIL again (+1 new: `names the individual letters`) | reproducible brittleness | Both runs enumerate all six letters and flag/re-split the oversized ticket. Run 1 wrote "failed **S** (three deliverables)"; run 2 wrote "**I**ndependent, **N**egotiable, … **S**mall" — emphasis *inside* the word, so `small` and `independent` never match as contiguous strings. |
| 5 | `invest-force-resplit: right-sized control is not split` | FAIL again | reproducible brittleness | Both runs carry the control through unsplit — run 1 "carried through **unsplit** … all six affirmed", run 2 "### The right-sized control — untouched … passes **6/6**". The alternation lists `not split\|no re-split\|kept\|left intact\|as-is` and misses both "unsplit" and "untouched". |

**No-regression verdict:** every pre-v1.7.5 fixture passes. Failures 1 and 2 are on v1.7.2/v1.7.3 fixtures and both cleared on re-run; failures 3–5 are on v1.7.1/v1.7.2/v1.7.3 fixtures and are assertion defects, not behavioural drift — the guarded behaviour appears in every transcript inspected.

**The v1.7.5 fixtures — all pass, first full verification:**

| fixture | result |
|---|---|
| validator jargon-guard self-test (10 assertions) | PASS — non-vacuous in both `skills/solve/SKILL.md` and root `README.md` |
| `worktree-env-fault` | PASS (4/4) |
| `execute-commit-before-review` | PASS (4/4, incl. the empty-diff fallback non-vacuity) |
| `workdoc-solve-autopath` | PASS (3/3) |
| `epic-lesson-capture` | PASS (4/4) |
| `codify-drift-count` | PASS (3/3) |
| `multi-clause-want` | PASS (3/3) |

v1.7.6's no-rationale-guard self-test also passes all 11 assertions, including the `RATIONALE.md`-reference check.

**Isolation proof — live checkout pristine:**

```
$ git branch -vv
* main 0bcafa9 [origin/main] mango: README restructure — …

$ git status --short --branch
## main...origin/main
 M tests/eval/run.sh          ← the measurement instrumentation only

$ git for-each-ref 'refs/heads/*PROJ-*'   → (empty)
$ ls docs                                  → does not exist
```

The suite's own guard agrees: `eval-isolation-guard: live checkout untouched after full eval (HEAD on main, no stray *PROJ-* branch, no work doc)` — PASS, and its non-vacuity check against an injected leak also PASS.

---

## 2. Per-fixture timing, slowest first

`⚠️` marks a fixture with a failing assertion (all five are wording-brittleness, see §1).

| fixture-id | wall-time | #assertions | skills exercised | cache |
|---|---|---|---|---|
| `refine-epic-detect-breakdown` | 395s | 3 | refine breakdown | miss (--no-cache) |
| `multi-clause-want` | 362s | 3 | analysis | miss (--no-cache) |
| `refine-direction-not-tool` | 358s | 3 | refine | miss (--no-cache) |
| `refine-skip-clear-ticket` | 353s | 3 | refine | miss (--no-cache) |
| `blast-radius` | 330s | 2 | design | miss (--no-cache) |
| `refine-classify-A-vs-B` | 319s | 3 | refine | miss (--no-cache) |
| `epic-exposure-checker` | 309s | 4 | refine | miss (--no-cache) |
| `behavioural-drift` | 305s | 3 | execute | miss (--no-cache) |
| `surface-denominator` | 302s | 2 | design | miss (--no-cache) |
| `design-blastradius-shared-type` | 298s | 4 | design | miss (--no-cache) |
| `design-layer` | 297s | 3 | design | miss (--no-cache) |
| `freeform` | 295s | 2 | analysis | miss (--no-cache) |
| `refine-backstop-challenger` | 293s | 3 | refine | miss (--no-cache) |
| `frontend-layer` ⚠️1 flap | 277s | 3 | design | miss (--no-cache) |
| `vague-requirement` | 268s | 2 | analysis | miss (--no-cache) |
| `breakdown-reratify` | 264s | 3 | breakdown | miss (--no-cache) |
| `epic-scaffold-committed` ⚠️1 flap | 256s | 2 | refine breakdown | miss (--no-cache) |
| `no-runner-proof` | 251s | 2 | execute | miss (--no-cache) |
| `lite` | 250s | 1 | analysis | miss (--no-cache) |
| `refine-consistency-is-how` ⚠️1 flap | 247s | 2 | refine | miss (--no-cache) |
| `red-baseline` | 246s | 4 | analysis | miss (--no-cache) |
| `refine-assumed-on-handback` | 243s | 5 | refine | miss (--no-cache) |
| `analysis-section-coverage` | 237s | 3 | analysis | miss (--no-cache) |
| `epic-lesson-capture` | 233s | 4 | breakdown | miss (--no-cache) |
| `full` | 232s | 2 | analysis | miss (--no-cache) |
| `design-blastradius-value-threading` | 231s | 3 | design | miss (--no-cache) |
| `uncodified-standard-nudge` | 204s | 3 | analysis | miss (--no-cache) |
| `refine-acceptance-bar-is-want` | 200s | 2 | refine | miss (--no-cache) |
| `breakdown-invest-enumerated` ⚠️1 flap | 194s | 3 | breakdown | miss (--no-cache) |
| `invest-force-resplit` ⚠️1 flap | 186s | 3 | breakdown | miss (--no-cache) |
| `challenger-unmet` | 153s | 2 | review | miss (--no-cache) |
| `per-clause` | 129s | 3 | design execute | miss (--no-cache) |
| `ledger-auto-append` | 115s | 3 | solve finalise | miss (--no-cache) |
| `rubric-hover` | 113s | 2 | review | miss (--no-cache) |
| `workdoc-solve-autopath` | 112s | 3 | solve | miss (--no-cache) |
| `ledger-dispatch-only-honesty` | 108s | 3 | finalise | miss (--no-cache) |
| `usage-unmeasured-marker` | 99s | 3 | solve finalise | miss (--no-cache) |
| `worktree-env-fault` | 97s | 4 | review | miss (--no-cache) |
| `budget-rtk-wire-guidance` | 97s | 3 | budget | miss (--no-cache) |
| `optimizer-adoption-gated` | 94s | 3 | budget | miss (--no-cache) |
| `caveman-critic-guard` | 88s | 2 | review | miss (--no-cache) |
| `rtk-degrade` | 87s | 2 | budget | miss (--no-cache) |
| `ledger-descriptive` | 87s | 3 | finalise | miss (--no-cache) |
| `ledger-label` | 85s | 2 | solve finalise | miss (--no-cache) |
| `review-git-isolation` | 77s | 4 | review | miss (--no-cache) |
| `verify-only-scoped` | 71s | 3 | review | miss (--no-cache) |
| `conditional-LGTM` | 64s | 3 | review | miss (--no-cache) |
| `verify-only-main-loop` | 61s | 3 | review | miss (--no-cache) |
| `finalise-lesson-pushed` | 57s | 3 | finalise | miss (--no-cache) |
| `execute-commit-before-review` | 54s | 4 | execute review | miss (--no-cache) |
| `ledger-gate` | 51s | 4 | finalise | miss (--no-cache) |
| `verify-only-bookkeeping-carveout` | 50s | 2 | review | miss (--no-cache) |
| `format-scope` | 48s | 2 | execute | miss (--no-cache) |
| `stuck-detector` | 46s | 1 | execute solve | n/a (scenario — never cached) |
| `stale-source-change` | 37s | 3 | finalise | miss (--no-cache) |
| `design-invalidated` | 34s | 2 | execute solve | n/a (scenario — never cached) |
| `ledger-gate-complete` | 34s | 1 | finalise | n/a (scenario — never cached) |
| `artifact-delta-emission` | 34s | 3 | solve finalise | n/a (scenario — never cached) |
| `ledger-content-gate` | 33s | 4 | finalise | miss (--no-cache) |
| `codify-drift-count` | 31s | 3 | codify | miss (--no-cache) |
| `carveout-nonexempt` | 28s | 1 | review | n/a (scenario — never cached) |
| `stale-workdoc-bump` | 27s | 2 | finalise | miss (--no-cache) |
| `per-clause-both` | 27s | 1 | design execute | n/a (scenario — never cached) |
| `ledger-content-gate-marker` | 26s | 1 | finalise | n/a (scenario — never cached) |

---

## 3. Analysis

### 3.1 Slowest fixtures — where the time is

| rank | fixture | wall | assertions | s/assertion |
|---|---|---|---|---|
| 1 | `refine-epic-detect-breakdown` | 395s | 3 | 132 |
| 2 | `multi-clause-want` | 362s | 3 | 121 |
| 3 | `refine-direction-not-tool` | 358s | 3 | 119 |
| 4 | `refine-skip-clear-ticket` | 353s | 3 | 118 |
| 5 | `blast-radius` | 330s | 2 | 165 |
| 6 | `refine-classify-A-vs-B` | 319s | 3 | 106 |
| 7 | `epic-exposure-checker` | 309s | 4 | 77 |
| 8 | `behavioural-drift` | 305s | 3 | 102 |
| 9 | `surface-denominator` | 302s | 2 | 151 |
| 10 | `design-blastradius-shared-type` | 298s | 4 | 75 |

Those ten are **3331s — 31% of the entire run**. The distribution is flat-topped, not spiky: the slowest fixture is 395s and the median fixture ~150s, so there is no single hot fixture to fix. Time tracks *phase*, not fixture design:

| skill group | dispatches | total |
|---|---|---|
| refine (incl. `refine breakdown`) | 10 | 2974s |
| analysis | 8 | 2094s |
| design (incl. `design execute`) | 7 | 1864s |
| breakdown | 4 | 877s |
| review (incl. `execute review`) | 10 | 826s |
| execute | 3 | 604s |
| finalise + `solve finalise` + `solve` | 11 | 811s |
| budget | 3 | 278s |
| scenarios (`run_prompt`) | 7 | 229s |
| codify | 1 | 31s |

**Refine + analysis + design = 6932s, 65% of the run over 25 dispatches.** The `review`, `finalise` and `budget` families are already cheap (30–115s each) — cutting there buys minutes at most.

Worst value-for-time single fixture: **`lite` — 250s for one assertion** (`TIER: lite`). `full` (232s / 2) and `freeform` (295s / 2) are the same shape: three separate full-analysis dispatches, 777s combined, for 5 assertions total.

### 3.2 Overlap candidates

**Rated against the cut rule: nothing is proposed for removal unless the behaviour is still caught elsewhere, and the "elsewhere" is named.**

**(a) Merge candidates — same skill, overlapping assertions, coverage preserved**

| candidate | cost | overlaps with | what is genuinely unique | proposed action |
|---|---|---|---|---|
| `breakdown-invest-enumerated` | 194s | `invest-force-resplit` (186s) — both assert the enumerated six-letter INVEST *and* an oversized ticket flagged + re-split | only the `names the individual letters` assertion. `invest-force-resplit` is a strict superset in evidence: it also carries the **right-sized control** proving non-vacuity, which this fixture lacks. Both re-run transcripts of `invest-force-resplit` print the full six-letter table. | move the one assertion onto `invest-force-resplit`; drop the fixture. **−194s** |
| `refine-consistency-is-how` + `refine-acceptance-bar-is-want` | 247s + 200s | each other — the two branches of the *same* v1.7.1 tie-breaker: (a) acceptance-bar → want-decision; (b) convention-answerable scope → how-decision | each pins one branch; neither tests discrimination | merge into **one** ticket carrying both a bar-decision and a scope-decision, asserting the classifier splits them correctly. This is *stronger* than the pair (it forces discrimination) and drops a dispatch. **−~220s** |
| `ledger-descriptive` | 87s | `records a cost ledger` ⊂ `ledger-auto-append` (which asserts the stronger N-dispatches→N-rows); `does not auto-cut` ⊂ `ledger-gate` **and** `ledger-content-gate` | only `finalise summary (total + driver)` | fold that one assertion into `ledger-auto-append`; drop the fixture. **−87s** |
| `verify-only-scoped` | 71s | `verify-only-main-loop` (61s) — v1.5's main-loop rule subsumes v1.4's "no blanket re-run"; same round-1-conditional-LGTM scenario shape | `reuses round-1 facts`, `challenger not repeated` | fold both assertions into `verify-only-main-loop`. **−71s** |

Total from (a): **~570s (9.5 min), 4 dispatches.** Real, but small next to a 176-minute run — which is the headline finding of this profile.

**(b) Conditional — overlap is real but the merge is risky**

- `ledger-gate` (51s) and `ledger-content-gate` (33s) share two assertions verbatim (`blocks like an unfilled matrix column`, `completeness check, never auto-cuts`) but inject **different** faults (missing row vs blank cell). A merged fixture injecting both cannot attribute which fault caused the block, so the non-vacuity weakens. Keep both unless someone writes a merged fixture asserting two *distinct* blocks.

**(c) Explicitly DO NOT cut — looks redundant, is not**

- `refine-backstop-challenger` (293s) and `epic-exposure-checker` (309s) carry near-identical assertions (1 dispatch, not a debate, can surface an un-exposed decision). They guard **different paths** — ticket vs epic. v1.7.2 added the epic one precisely because the epic path was the one path skipping the backstop. Merging them re-opens that hole. 602s stays.
- The four Gate-2 blockers (`design-layer`, `frontend-layer`, `surface-denominator`, `per-clause`, 1176s combined) all end in "Gate 2 blocked", but each blocks for a different reason (unit-proof layer mismatch / frontend render proof / surfaces denominator / per-clause M-gate). Each reason is guarded nowhere else.

**(d) Fixtures whose behaviour also appears in `scripts/validate.py`**

| fixture | cost | validator counterpart |
|---|---|---|
| `multi-clause-want` | 362s | `validate_multi_clause_want` |
| `epic-lesson-capture` | 233s | `validate_epic_lesson_owner` |
| `workdoc-solve-autopath` | 112s | `validate_solve_workdoc_route` |
| `worktree-env-fault` | 97s | `validate_worktree_env_parity` |
| `optimizer-adoption-gated` | 94s | `validate_token_optimizer` |
| `caveman-critic-guard` | 88s | `validate_critic_guardrail` |
| `ledger-label` | 85s | `validate_ledger_label` |
| `review-git-isolation` | 77s | `validate_review_git_isolation` |
| `execute-commit-before-review` | 54s | `validate_empty_diff_fallback` |
| `codify-drift-count` | 31s | `validate_drift_count_line` |

**Read this table with care.** Every one of those validator checks is a **prose-presence grep over the shipped instruction text** — it proves the directive is still written in `SKILL.md` / the agent brief / the template, not that the model follows it. The `claude -p` fixture is the only thing that proves the directive is *effective*. Under mango's own prose-IS-behaviour premise those are closer together than in a normal codebase, but they are not the same check, and the difference is exactly what a false-green looks like (v1.7.5's own jargon-guard fix was a validator that passed while the shipped text was wrong).

Two exceptions worth noting, where the validator genuinely is the stronger guard:

- **`ledger-label` (85s)** — the label lives in `templates/ticket.md`, a static file, and `validate_ledger_label` asserts the exact column header and forbids both false-precision variants mechanically. The fixture only adds "the model emits an unsplit figure in prose". This is the single best drop candidate in the table.
- **`codify-drift-count` (31s)** — `validate_drift_count_line` pins the exact `DRIFT: <n> entries | <m> tickets` shape. The fixture's unique value is that the model *counts correctly* (5 entries / 2 tickets from the list), which the validator cannot check — but at 31s it is the cheapest fixture in the suite, so there is nothing to win by cutting it.

**The load-bearing conclusion:** these ten fixtures total **1232s — 12% of the run**, and eight of the ten cost ≤112s. Dropping the entire validator-overlap set buys ~20 minutes off a 176-minute run while surrendering every behavioural proof that those directives are obeyed. **Speed is not in this set.** It is in refine + analysis + design, where the fixtures are unique guards and the answer is parallel dispatch, not deletion.

### 3.3 Cache reality — the bug IS fixed, but nothing has populated it

State at HEAD before this run: **`tests/eval/.cache/` did not exist** — no green transcript has ever been written, consistent with the "never populated" report.

Two independent reasons, both now established:

1. The historical bug (v1.7.5 Fix 4): the hit/fresh tallies were incremented inside command-substitution subshells and discarded, so `FRESH_FIXTURES` was always empty and the end-of-run write loop iterated over nothing.
2. `--no-cache` — this run — skips the write by design (`run.sh:1318` gates on `CACHE_ENABLED -eq 1`, and additionally on `fails -eq 0`). **A milestone run can never populate the cache.** So this run says nothing about the cache either way.

Because of (2), the cache was verified separately with a 1-fixture probe (`stale-workdoc-bump`, cache dir redirected out of the repo via `MANGO_EVAL_CACHE_DIR`, using run.sh's real prelude and its real end-of-run write block):

| probe run | expectation | result |
|---|---|---|
| 1 — empty cache, cache enabled | fresh dispatch, green written | `EVAL cache: 0 cache-hit(s), 1 fresh run(s)`; `stale-workdoc-bump.264e4ccb….green` written. **50s** |
| 2 — same skills-hash | cache-hit, no dispatch | `EVAL cache: 1 cache-hit(s), 0 fresh run(s)`. **0s** |
| 3 — `--no-cache` | fresh, no reuse, green not overwritten | fresh dispatch, hash file unchanged. **43s** |

**Verdict: the transcript-cache populates and hits correctly at v1.7.6.** The reason the repo has no `.cache/` is simply that no cache-enabled green run has happened since the fix. Note also that the tally is only written for `run_fixture` — the 7 `run_prompt` scenarios have no cache path at all and always dispatch (229s/run, a small but permanent floor).

One caveat for the dev loop: the runner fingerprint invalidates the **whole** cache whenever `run.sh` itself changes (`run.sh:316-324`). Any version that edits the runner — including a parallel-dispatch change, and including this instrumentation — re-runs all 64 fixtures. The per-skill selectivity only pays off on skills-only versions.

### 3.4 Total wall-time and the parallel-dispatch win

- **Total wall-clock: 10590s (2h56m30s).**
- **Sum of dispatch times: 10587s.** Harness overhead (clone, sandbox, harness JSON, 26 self-test assertions, all 173 greps) is **~3 seconds — 0.03%.**

That is the single most actionable number in this profile: **the suite is 100% `claude -p` latency and it is 100% sequential.** There is nothing to optimise in the harness; the only levers are fewer dispatches and concurrent dispatches.

LPT-scheduled makespan over the measured 64 dispatch times:

| workers | wall-clock | vs today |
|---|---|---|
| 1 (today) | 10587s / 2h56m | — |
| 2 | 5294s / 1h28m | 2.0× |
| 4 | **2649s / 44m** | 4.0× |
| 8 | **1327s / 22m** | 8.0× |
| 16 | 671s / 11m | 15.8× |

Scaling is near-linear and stays so out to 16 workers because the longest single dispatch is only 395s — no fixture is a scheduling floor until well past N=16. **N=8 turns a 3-hour milestone run into ~22 minutes**, which is a bigger win than every merge in §3.2 combined (~9.5 min) by an order of magnitude.

Two hazards a parallel dispatcher must handle, both visible in the runner today:

1. **Shared sandbox.** All 64 dispatches `cd "$SANDBOX"` into one clone. Fixtures that let `execute` branch and commit would race. Either give each worker its own clone (the clone is `--local --no-hardlinks`, so it is cheap) or its own worktree.
2. **`write_harness` mutates shared state mid-run.** `red-baseline` repoints `config.test_command` at the committed failing check and then restores the green default. Under concurrency that flips `.harness.json` under other in-flight fixtures. Per-worker sandboxes fix this too.

Also worth pricing in: the counters (`total`, `fails`) and both tally ledgers already survive subshells only because they are files or main-shell state — a parallel dispatcher must keep that discipline (the v1.7.5 Fix 4 lesson) or it will silently lose assertion counts.

---

## 4. Recommended order of work (evidence-based)

1. **Parallel dispatch with per-worker sandboxes, N=8** — ~22 min, no coverage change. This is the whole win.
2. **Fix the five brittle assertions** — none is a behaviour change; all five violate the suite's own convention in `tests/eval/README.md` (match the decision, tolerate markdown emphasis). Specifically: tolerate emphasis inside words (`\*{0,2}S\*{0,2}mall`), accept a zero-count as a negation, widen `not split` to include `unsplit`/`untouched`, and stop asserting on a single glyph (`❌`) when the artifact may be written to the work doc rather than the response.
3. **The four merges in §3.2(a)** — ~9.5 min, coverage preserved, each with its "covered by" named.
4. **Only then** consider the validator-overlap set, and only `ledger-label` has a strong case.

---

## The rule for the cut (on record)

A fixture may be cut or merged **only if the behaviour it guards is still caught elsewhere** — by `scripts/validate.py` or by another fixture. A fixture that is the sole guard of a behaviour stays, however slow it is. Cutting for speed at the cost of coverage is removing a gate, and is not allowed. Speed comes from removing genuine redundancy and from parallel dispatch — never from dropping a unique check.

Applied to this profile: nothing in §3.2(c) or §3.3 may be cut; §3.2(a) may be merged with the named assertion carried over; §3.2(d) requires a human decision on whether a prose-presence grep is accepted as sufficient coverage, and the answer is "no" for nine of the ten.

---

## Instrumentation note

`tests/eval/run.sh` carries a measurement-only addition (shipped from 1.8.0, still a complete no-op when
`MANGO_EVAL_PROFILE` is unset):

- `prof_now` / `prof_time` / `prof_assert` helpers writing to `$MANGO_EVAL_PROFILE.timing` and `.asserts`. File-based, so they survive the command-substitution subshells — and, from 1.8.0, the background worker subshells too (same constraint as the cache tallies).
- One `prof_time` call per dispatch, in `dispatch_one` (name, ms, hit/fresh/n-a, fixture/scenario). Before 1.8.0 these sat in `run_fixture` / `run_prompt`, which the two-pass split turned into registration-only functions.
- One `prof_assert` call on each branch of `assert_contains` / `assert_all` / `assert_absent`, keyed on the transcript basename.

`PROFILE="${MANGO_EVAL_PROFILE:-}"` — with the variable unset every hook returns immediately, so a normal run is byte-identical in behaviour. No assertion regex, fixture text, prompt, or dispatch path was modified. Reproduce with:

```
MANGO_EVAL_PROFILE=/tmp/prof bash tests/eval/run.sh --no-cache
```
