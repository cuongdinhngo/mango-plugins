# EVAL-STATUS.md — the current eval cycle

**This file is rewritten in place, never appended to.** It describes one cycle: what is green, what is
red, and what runs next. When a cycle is superseded its per-batch rows move to
[`EVAL-ARCHIVE.md`](./EVAL-ARCHIVE.md) and this file is reset. Findings worth keeping go to
[`EVAL-FINDINGS.md`](./EVAL-FINDINGS.md) instead — never here.

| File | Job |
|---|---|
| `EVAL-STATUS.md` | this file — the current cycle |
| [`EVAL-FINDINGS.md`](./EVAL-FINDINGS.md) | permanent findings and the rules they produced |
| [`EVAL-ARCHIVE.md`](./EVAL-ARCHIVE.md) | superseded cycles, verbatim |
| `.cache/coverage.<runner-fp>.tsv` | **the authority** |

**Do not hand-type status into this file.** Read it from the ledger:

```
bash tests/eval/coverage-report.sh              # the dashboard
bash tests/eval/coverage-report.sh --remaining  # bare list of fixtures with no green row
bash tests/eval/coverage-report.sh --md         # a table to paste below
bash tests/eval/run.sh --verify-suite           # THE GATE — the only thing that proves green
```

`coverage-report.sh` is a dashboard and says so; `--verify-suite` is the gate. Only the gate's output
may be cited as evidence the suite passes.

---

## Cycle 2, proof pass — the v1.15.1 ruler

The discovery pass is finished and its ruler is gone. The single edit landed on 2026-09-03 as
**v1.15.1**; it changed `RUNNER_FP`, which wiped all 118 `.green` entries and started a fresh ledger.
Everything below the *Register* describes the discovery pass and is kept only as evidence of what was
found — **no row from it may be cited.**

```
Runner fingerprint  : ecf9e4c6bfb0e98e…   (v1.15.1 — the proof-pass ruler)
Plugin-tree fp      : 9b199a8b5b77c989…   (moved: the 1.15.1 version bump is inside it)
Model / CLI         : cli-default / 2.1.259 (Claude Code) — PINNED, see below
Suite               : 126 jobs · 511 transcript assertions · dispatch-free self-tests +6 on v1.15.0
Ledger              : empty — 0 of 126 jobs recorded
Superseded ruler    : 82580ae5a827 (v1.15.0, CLI 2.1.258→.259) — 118 rows, none usable
```

Re-read the fingerprint before each batch, never from this line:

```
sha256sum tests/eval/run.sh
```

### Pin the CLI for the whole pass

The CLI moved 2.1.258 → 2.1.259 in the middle of the discovery pass and split its ledger into two
rulers, which is a refusal condition. Four versions are on disk. Every batch of this pass runs with
2.1.259 first on `PATH`:

```
export PATH="$HOME/.cache/mango-eval-cli-pin:$PATH"    # → claude 2.1.259, verified
claude --version                                        # confirm before every batch
```

The pin is a directory holding one symlink to `~/.local/share/claude/versions/2.1.259`. If a batch
ever reports a different CLI, stop: the rows already written are the ones that count, and mixing a
second version costs the whole pass.

**And the same trap has a second door.** `plugin_tree_fp` hashes `plugins/mango/.claude-plugin/*.json`
and `plugins/mango/scripts/*.py`, so the 1.15.1 version bump moved it from `136caac19f92` to
`9b199a8b5b77` — deliberately, before any batch ran. **No edit to `plugin.json` or to any
`plugins/mango/scripts/*.py` until the pass is proven**, or the rows split into two rulers exactly as
the CLI bump split them. Skill and doc edits are a different matter: they move the per-fixture
skills-hash instead, which shows up as a **stale** green rather than a mixed ruler — still a refusal,
still worth not doing mid-pass.

### Strategy — a discovery pass, then a proof pass

Editing `run.sh` changes `RUNNER_FP`, which wipes every `.green` and starts a fresh ledger. That is the
design working: the fingerprint **is** the ruler. But it means fixing an assertion mid-cycle throws away
every green bought so far, and the loss grows with each batch — fix at batch 2 and lose 30 fixtures, fix
at batch 8 and lose 100. So this cycle is deliberately two passes:

1. **Discovery — done, 2026-09-02.** Every batch under runner `82580ae5a827`. Reds were **recorded,
   not fixed**; `run.sh` was not touched, so no batch was paid for twice. All 126 jobs were dispatched
   and judged: 118 rows written, 6 scenarios green but unrecordable, 2 behavioural reds, 1 blocking
   harness defect. Nothing was left to discover.
2. **Proof — running now,** under runner `ecf9e4c6bfb0`. The one permitted `run.sh` edit has landed
   (see *Register*). Every job re-runs, batch by batch, under a pinned CLI; then `--verify-suite`,
   which for the first time this cycle is a gate that **can** pass.

The considered alternative was to split `DISPATCH_FP` (what determines a transcript) from `RUNNER_FP`
(the ledger's ruler), so an assertion-only edit would keep the transcripts and the proof pass would be a
free re-judge. It is ~$50 cheaper and was **rejected on risk**: it means new cache-invalidation
machinery, and the cache is exactly where a false-green would hide. Paying twice for a blunt, obviously
correct ruler is the cheaper mistake.

> **A discovery-pass green is not a green.** Every row in that pass was measured under a ruler this
> one replaced. Nothing in the *Batches run* table below may be cited as evidence the suite passes.

### Coverage — proof pass

| Metric | Value |
|---|---|
| Runner fingerprint | `ecf9e4c6bfb0` |
| Plugin-tree fingerprint | `9b199a8b5b77` |
| Jobs recorded | 0 of 126 |
| Rows not green | 0 |
| Stale greens | 0 |
| Distinct rulers among rows | 0 (must be 1 once rows exist) |

Regenerate with `bash tests/eval/coverage-report.sh --md`. The gate is
`bash tests/eval/run.sh --verify-suite`, and only its output counts.

### The batch plan

126 jobs = 119 fixtures + 7 scenarios, grouped by the skill each fixture's `FIXTURE_SKILLS` entry names
first. Group sizes are **larger than the discovery pass's** because nothing is cached now — every job
re-runs. Re-derive them rather than trusting this table:

```
sed -n '/^declare -A FIXTURE_SKILLS=(/,/^)$/p' tests/eval/run.sh \
  | grep -oE '\[[a-zA-Z0-9_-]+\]="[^"]*"' | sed 's/^\[//; s/\]="/\t/; s/"$//' \
  | awk -F'\t' '{split($2,a," "); print a[1]}' | sort | uniq -c | sort -rn
```

(`grep -oE`, not `sed -n s///p`: the map packs several `[key]="value"` pairs per line, and a
one-match-per-line substitution under-counted it by 46% once already.) Cross-checks that must hold
before dispatching anything: 119 map keys, 119 `fixtures/*.md` on disk, the two lists **identical**,
7 scenario labels from `$(run_prompt <label>`, and 126 registered by `--verify-suite` itself.

| Batch | Group | Jobs | Parts | Note |
|---|---|---|---|---|
| 1 | `analysis` | 13 | 2 | Gate 1 — selectors verified 2026-09-03, 7/6, `matches 7 of 126` and `6 of 126`, nothing absent, nothing over-matched. 2 parts not 3: the discovery pass ran this exact group at this exact size in 2 parts / 693s, so the slowest single job is ~350s and a 7-job wave clears the ceiling with margin. |
| 2 | `refine` | 22 | 4 | phase 0, the largest group; carries **R1** |
| 3 | `design` | 18 | 3 | Gate 2 |
| 4 | `review` | 14 | 3 | Gate 3 |
| 5 | `finalise` + `codify` | 19 | 4 | |
| 6 | `execute` + `breakdown` | 8 | 2 | `execute` branches and commits — isolation guards matter |
| 7 | `autorun` | 9 | 3 | ⚠️ **the ceiling risk** — see below |
| 8 | `promote` + `solve` | 9 | 2 | |
| 9 | `budget` + `quick` + `init` | 7 | 2 | |
| 10 | scenarios | 7 | 2 | carries **R2**; the first pass that can record a scenario row at all |

Sums to 126. Each part's selector is built and **verified dispatch-free** immediately before its run —
every name present on disk, every match named, nothing extra — because `--only` matching is unanchored
(`grep -qE "$ONLY"`), so every selector must be `^(a|b|c)$`.

**Batch 7 is the one to watch.** In the discovery pass the `autorun` part of 7 jobs took **564s**, and
with `--workers 8` a part of ≤ 8 jobs is one wave — so that 564s is a *single job's* latency, 27s
inside the 600s tool ceiling. Splitting the group does not make that job faster; it only means a
ceiling kill loses 3 jobs instead of 9, and a killed run writes no rows at all. If a part of batch 7 is
killed, re-run it as single jobs. The new per-job timing output names the slow one on the first part.

### Batches run — discovery pass (superseded ruler `82580ae5a827`)

| Batch | Group | Parts | Jobs | Assertions | Dispatch | Result |
|---|---|---|---|---|---|---|
| 1 ↻ | the unknowns (stop-gate) | 1 | 10 | 127 / 127 | 457s | ✅ green |
| 2 ↻ | `refine` (phase 0) | 3 | 21 | 302 / 303 | 1047s | 🟡 **20/21** — R1 |
| 3 ↻ | `analysis` (Gate 1) | 2 | 13 | 189 / 189 | 693s | ✅ green |
| 4 ↻ | `design` (Gate 2) | 2 | 17 | 205 / 205 | 645s | ✅ green |
| 5 ↻ | `execute` (phase 3) | 1 | 4 | 82 / 82 | 218s | ✅ green |
| 6 ↻ | `review` (Gate 3) | 2 | 11 | 177 / 177 | 283s | ✅ green |
| 7 ↻ | `finalise` (+`codify`) | 3 | 17 | 289 / 289 | 445s | ✅ green ⚠️ CLI split |
| 8 ↻ | `autorun` (unattended) | 1 | 7 | 120 / 120 | 564s | ✅ green ⚠️ 27s under the ceiling |
| 9 ↻ | the small groups (5 skills) | 1 probe + 3 | 19 | 358 / 358 | 752s | ✅ green |
| 10 ↻ | scenarios | 1 probe + 1 | 7 | 6 of 7 judged green | 160s | 🟡 **6/7** — R2, and **0 rows recorded** |

Assertion counts include the 71 dispatch-free self-tests once per part, so they do not sum to 511.

Notes worth carrying:

- **Batch 4 is the one that mattered.** Its cycle-1 predecessor went red on `API Error: 529` with seven
  fixtures never running and three assertions passing anyway on the harness header. All 17 are now
  proven on real output, no `API Error` in any transcript. See [`EVAL-FINDINGS.md`](./EVAL-FINDINGS.md).
- **Batch 2's fixture assertion count did not move** — 56 before Fix 3, 56 after. Stripping the header
  removed no assertion and broke none, so the checks that could have matched the header were matching
  real output too. Not an outcome to assume; the strip is the kind of change that turns a silent pass
  red.
- **Batch 5's isolation guards were read, not assumed** — it is the batch that branches and commits.
  All three fired their non-vacuity controls, then passed.
- **Selector rebuilt for batch 4** from `FIXTURE_SKILLS` rather than copied: it is the one batch with no
  recorded selector. 18 map to `design`, 1 already green, 17 run — exactly the original's count.
- **Batch 6's selector was rebuilt too**, and the rebuild caught a counting bug in my own
  extraction: `FIXTURE_SKILLS` packs several `[key]="value"` pairs per line, so a
  one-match-per-line `sed` reported **64** entries instead of **119**. Re-derived with
  `grep -oE`, it gives 119 distinct keys — 12 map to `review`, 1 already green, **11 ran**,
  matching the count this file already carried. Both parts were then proven an exact
  partition with zero named-but-absent and zero over-matched jobs before dispatch.
- **Batch 6 ran faster than the cycle predicted** — 283s of dispatch for 11 jobs in two parts,
  against the ≈1.55× slowdown seen in batches 1–5. (This note originally read "≈26s/job", which
  divided a part's wall-clock by its job count. With `--workers 8` a part of ≤8 jobs is a single
  **wave**, so its wall time is the *slowest job's* latency and nothing about it is per-job — part A
  was 6 jobs in 185s, meaning one job took ~185s. The wrong reading is what mis-sized batch 8.)
- **Batch 10 hit a blocking harness defect: a scenario can never be recorded in the ledger.**
  `skills_files` ends by emitting `$FIXTURES/<name>.md`, and a scenario has no fixture file, so
  `cat` fails, `pipefail` promotes it, and `errexit` kills the run one statement past
  `_h="$(skills_hash …)"` — after the assignment succeeded, before any row is written. Both
  probe runs died that way: every assertion judged and printed, then exit 1 with no summary and
  no rows. **`--verify-suite` as shipped can therefore never pass**, because 7 of its 126 jobs
  are scenarios. Nine fixture batches went through the same code untouched. Fix and its
  self-test are queued for the proof-pass edit; see [`EVAL-FINDINGS.md`](./EVAL-FINDINGS.md).
- **The scenario labels came from `run_prompt`, not `run_scenario`** — the function I had
  recorded as needing rework does not exist, which is why the old grep returned 0. The naive
  `grep -oE 'run_prompt [A-Za-z0-9_-]+'` then returned **9** labels: the 7 real ones plus
  `REGISTERS` and `resolves`, lifted out of comment prose at `run.sh:24` and `:29`. Anchoring on
  the executable form `$(run_prompt <label>` gives exactly 7, agreeing with the list
  `--verify-suite` derives for itself. Fourth text-pipeline miscount of this cycle.
- **Scenarios are the fastest group in the suite**, not the slowest as this file predicted:
  16s / 17s / 20s / 25s / 62s individually, two parts at 43s and 117s. They carry no ticket, so
  they answer one question instead of driving a lifecycle.
- **Two empty `mktemp` directories survive a run** (`/tmp/tmp.*`, both stamped with the run's
  own minute). The worker-isolation guard passed because it looks for worker *trees* with
  content. Harmless, left in place, noted rather than swept.
- **Batch 9's probe falsified my own guess, for 95 seconds.** I expected `solve` to be
  `autorun`-scale because it drives a whole ticket; the 2-job probe came back in **95s**. The
  slowest part of the batch turned out to be the mixed small groups at 364s, a group I had no
  reason to suspect. Probing the *suspected* slowest is not the same as probing the slowest —
  the probe is worth running, but it bounds nothing it did not sample.
- **The CLI moved mid-batch — 2.1.258 → 2.1.259 — between batch 7 part A's dispatch and the
  batch before it.** The ledger now carries two rulers (76 rows at .258, 17 at .259) and
  `coverage-report.sh` says so: `distinct rulers among rows 2 (NOT uniform — --verify-suite
  will refuse)`. This is the machinery working, not failing: the ruler that was invisible to
  every hash before v1.15.0 is now the thing that shouts. See [`EVAL-FINDINGS.md`](./EVAL-FINDINGS.md).
- **Batch 8 nearly timed out, and my sizing reasoning was wrong in a way worth keeping.** I ran
  all 7 jobs as one part because with 8 workers and 7 jobs the wall time is the *slowest job's*
  latency, not the sum — correct in form. But I took that latency from batch 6 by dividing a part's
  wall time by its job count — and a part of ≤8 jobs is one wave, so 185s for 6 jobs meant one job
  took ~185s, not 26s. The part took **564s** against my ~200s estimate, 27s inside the 600s tool
  ceiling. The real gap between a `review` and an `autorun` fixture is ~3×, not the ~21× the bad
  arithmetic implied — but 3× off a 185s baseline is still enough to nearly hit the ceiling.
- **No artifact records per-job latency.** `run.sh` keeps no per-job timing, and cache-entry
  mtimes are all written at end-of-part, so they are batch-uniform and useless as a measurement
  (checked: batch 6's nine entries carry exactly two timestamps, one per part). Part wall-time
  is the only observable, so latency per group cannot be derived after the fact — only measured
  by running a small part of that group first.
- **Timing:** this cycle runs ≈**1.55×** slower than cycle 1, so any batch whose predecessor took over
  ~380s must be split to stay under the 600s tool ceiling. Splitting is free.
  **Superseded by batch 8:** the predecessor's *total* is the wrong predictor when workers ≥ jobs,
  because wall time is then the slowest job's latency. **A part of ≤ `--workers` jobs is one wave, so
  splitting a group across such parts costs nothing but the per-part self-test overhead (~8s) while
  bounding every tool call** — batch 9 ran 17 jobs as 6/6/5 and the parts came in at 364s / 169s /
  124s, none near the ceiling. For a group whose latency has never been measured, dispatch **2–3 jobs
  first** and size the rest from what that part took.

  Measured wall time per part (dispatch seconds, `--workers 8`, so each figure is that part's
  slowest single job):

  | Group | Part size | Wall |
  |---|---|---|
  | `autorun` | 7 | **564s** |
  | mixed small groups (`breakdown`/`budget`/`codify`/`quick`) | 6 | 364s |
  | `finalise` | 6 | 194s |
  | `review` | 6 | 185s |
  | mixed (`init doctor`/`promote`/`solve finalise`) | 6 | 169s |
  | `solve` (probe) | 2 | 95s |

  `autorun` is the only group that has come close to the ceiling, and it is done.

### Register — all three FIXED in v1.15.1 (2026-09-03)

| # | Job | Assertion | Class | Evidence |
|---|-----|-----------|-------|----------|
| R1 | `refine-consistency-is-how` | `refine-consistency: NOT asked as a want-decision` | wording / emphasis window | Behaviour **correct**: H1 filed, resolved "apply to ALL consumers sharing the recipe", cited, flagged for ratification. Transcript says *"It was **not** put to the user as an open want"*. Regex is `not .{0,20}(ask\|want-decision\|open want)`; `open want` lands at offset **25** because the `**` emphasis eats 2. |
| R2 | `ledger-gate-complete` (scenario) | `ledger-gate-complete: proceeds, BECAUSE the rows equal the dispatches` | **outcome — underspecified prompt** | Model answered *"Not enough information — row count alone doesn't clear it"*, then split it correctly: every token cell carrying a value or an explicit `unmeasured (…)` → proceeds; any cell blank → blocks, citing `skills/finalise/SKILL.md:230-241`. The prompt fixes the row **count** and says nothing about row **content**, and mango's gate has both conditions. Better behaviour than the assertion expects. |
| D1 | `skills_files` / `hash_files` | — (kills the run) | **harness — blocking** | A scenario has no `$FIXTURES/<name>.md`, so `cat` fails under `pipefail`+`errexit` and no scenario row can ever be written. `--verify-suite` is unsatisfiable as shipped. Fix: emit that path only `if [ -f … ]`, keeping exit status 0, plus a self-test that writes and verifies a real scenario row. |

**All three are fixed**, in one edit as planned. What shipped, and what proves each:

| # | Fix | Proof it is not vacuous |
|---|---|---|
| D1 | `skills_files` emits the fixture path only `if [ -f … ]`, and returns 0. The row-writing block became a function, `cov_row_for`, **so that the self-tests can call it.** | 4 new dispatch-free checks on a job with no fixture file: `skills_hash` returns status 0, a green row is produced, that row satisfies the real gate against the real current hashes and real identity, and the same holds for the real registered scenario label (`per-clause-both`). Confirmed by reverting the one-line fix and re-running the gate: **`--verify-suite` reports 17/22 with the defect and 21/22 with it fixed** — the 4 substantive writer checks flip, and the remaining failure in both cases is the empty ledger. Reported as failures, never a dead run. A 5th check asserts the control job really has no file, so the set cannot pass vacuously. |
| R1 | Token hoisted to `RE_NOT_ASKED_AS_WANT`, shared by the fixture and **two** paired self-tests. Window widened over emphasis only (`not[*_ ]{1,6}[^.]{0,30}…`) and bounded by `[^.]`, so it can never leap a sentence boundary. | Checked against 5 transcripts offline: the field wording and the emphasised form now match, the zero-count form is unaffected, and **both** wrong transcripts — which actually asked the question — still miss. The new paired self-test's `good` file deliberately carries no zero-count line, so it can only pass through the widened alternative. |
| R2 | The scenario's **premise** completed: the prompt now states every row carries a token value, so the dispatch-count identity is the only condition under test. The assertion is untouched. | Row content stays tested where it already was, in `ledger-content-gate-marker`. Widening the assertion to accept "not enough information" was rejected: the class is *outcome*, and this suite does not widen over outcome. |

Also in the edit: **per-job dispatch timing**, printed on every run with the slowest job named — the
figure batch 8 needed and had to nearly time out to learn. `plugin.json` 1.15.0 → **1.15.1**, the
CHANGELOG entry carrying the reasons, and the root README badge (which had silently sat at 1.14.2).

Two findings came out of writing the tests rather than the fixes, and both are in
[`EVAL-FINDINGS.md`](./EVAL-FINDINGS.md): **`set -e` is ignored inside an `if` condition**, which made
my own first version of the D1 status check pass under the defect; and **every assertion in this suite
is line-bounded by `grep`**, recorded and deliberately *not* fixed, because changing it would
re-interpret all 511 assertions at once — a ruler change, not a batch fix.

(Named D1, not H1: R1's own evidence quotes a mango *want-hypothesis* labelled H1, and two different
H1s in one table is exactly the kind of collision this file exists to avoid.)

### Next — run the ten batches

Gates re-run after the edit, on 2026-09-03:

```
python3 scripts/validate.py            → 2057 checks run, 0 failed
python3 tests/envelope/test_envelope.py → 128 tests, OK
bash tests/eval/run.sh --verify-suite  → 21/22; the one failure is the empty ledger, by design
```

That last line is the state to expect until batch 10 lands: the 21 harness checks pass, and the gate
refuses because no job has a row yet. It is the first time this cycle the gate has been *able* to pass.

Then, per batch: pin the CLI, confirm `claude --version`, build the part selectors and verify them
dispatch-free, run, record the row in the table above, commit. Reds this time are **fixed as found** —
the discovery pass is over, and there is nothing left to keep a ruler intact for.

Finally `bash tests/eval/run.sh --verify-suite` with all 126 rows in, and paste its output below.

### Closing entry — fill after the proof pass

```
Suite proven green at SHA :
Date                      :
--verify-suite output     :        ← paste it; it is the only admissible evidence
Total jobs                : 126
Batches needed            :
Reds fixed from register  :
New findings              :        ← and move them to EVAL-FINDINGS.md
```
