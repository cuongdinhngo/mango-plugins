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

## Cycle 2 — the v1.15.0 ruler

```
Runner fingerprint  : 82580ae5a8272bb39fd5d0f2fce0e17260d01ee4c85e7d4d8df9e7d33334b492
Plugin-tree fp      : 136caac19f92894859da81a6a1439332d6b1aa173474c52ad4a457b5e79aa5f0
Model / CLI         : cli-default / 2.1.258 (Claude Code)
Suite               : 126 jobs · 511 transcript assertions · 71 dispatch-free self-tests
Started             : 2026-09-02, at df45512
```

### Strategy — a discovery pass, then a proof pass

Editing `run.sh` changes `RUNNER_FP`, which wipes every `.green` and starts a fresh ledger. That is the
design working: the fingerprint **is** the ruler. But it means fixing an assertion mid-cycle throws away
every green bought so far, and the loss grows with each batch — fix at batch 2 and lose 30 fixtures, fix
at batch 8 and lose 100. So this cycle is deliberately two passes:

1. **Discovery (running now).** Every batch under runner `82580ae5a827`. Reds are **recorded, not
   fixed**; `run.sh` is not touched, so no green is invalidated and no batch is paid for twice.
2. **Proof.** Apply every fix in **one** edit — one fingerprint change, one wipe — then run the full
   suite once and prove it with `--verify-suite`.

The considered alternative was to split `DISPATCH_FP` (what determines a transcript) from `RUNNER_FP`
(the ledger's ruler), so an assertion-only edit would keep the transcripts and the proof pass would be a
free re-judge. It is ~$50 cheaper and was **rejected on risk**: it means new cache-invalidation
machinery, and the cache is exactly where a false-green would hide. Paying twice for a blunt, obviously
correct ruler is the cheaper mistake.

> **A discovery-pass green is not a green.** Every row in this pass is measured under a ruler the proof
> pass will replace. Nothing here may be cited as evidence the suite passes.

### Coverage

| Metric | Value |
|---|---|
| Runner fingerprint | `82580ae5a827` |
| Plugin-tree fingerprint | `136caac19f92` |
| Fixtures green | 118 of 119 on disk (+0 scenario rows) |
| Rows not green | 1 |
| Stale greens | 0 |
| Distinct rulers among rows | 2 (must be 1) |
| Fixtures with no green row | 1 |

Regenerate with `bash tests/eval/coverage-report.sh --md`.

### Batches run

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

### Register — reds to fix in the single edit

| # | Job | Assertion | Class | Evidence |
|---|-----|-----------|-------|----------|
| R1 | `refine-consistency-is-how` | `refine-consistency: NOT asked as a want-decision` | wording / emphasis window | Behaviour **correct**: H1 filed, resolved "apply to ALL consumers sharing the recipe", cited, flagged for ratification. Transcript says *"It was **not** put to the user as an open want"*. Regex is `not .{0,20}(ask\|want-decision\|open want)`; `open want` lands at offset **25** because the `**` emphasis eats 2. |

Each fix ships with its paired `selftest_assertion` — a `good` transcript carrying the observed wording
and a `bad` one that actually asked the question, so the widened token still misses wrong behaviour.

### Next

**Every fixture is now green except R1.** What is left is **7 scenarios + R1 = 8 jobs**:

| Group | Left | Note |
|---|---|---|
| scenarios | 7 | **foreground, split** — the background attempt was stopped host-side; latency unmeasured, and a scenario spans several phases, so expect `autorun`-scale or worse |
| `refine` | 1 | R1 — stays red by design this pass |

The scenario selector must be built from the `run_scenario` call sites, not from `FIXTURE_SKILLS`
(scenarios are not in that map). An earlier `grep -oE 'run_scenario [a-zA-Z0-9_-]+'` returned 0 and
needs reworking against the actual call syntax before batch 10.

Derive every remaining selector the batch-6 way — from `FIXTURE_SKILLS` re-parsed with `grep -oE`,
intersected with `coverage-report.sh --remaining` — never by copying a recorded one.

**Bundle into the proof-pass `run.sh` edit** (it is the only edit this cycle allows, so anything
wanted in `run.sh` must ride with it): per-job dispatch timing in the run output, so a group's latency
becomes an artifact instead of something re-learned by nearly timing out.

**Pin the CLI before the proof pass.** The install is native
(`~/.local/bin/claude` → `~/.local/share/claude/versions/<v>`), `autoUpdates` is already `false` in
`~/.claude.json`, and the version moved anyway — `autoUpdatesProtectedForNative: true` is in the same
file. 2.1.258 is still on disk. Put the chosen version's directory first on `PATH` for the proof
pass and record which version it was — a bump landing inside it splits the ruler and wastes the run.

**The proof pass will not fit in one invocation, and the numbers say so.** The R1 fix lands inside
`run.sh`, which moves `RUNNER_FP` and wipes all 118 cache entries (`run.sh:631`), so every job runs
fresh. 126 jobs at `--workers 8` is 16 waves; the ten part-waves measured this cycle averaged ~204s
and the slowest was 564s, putting a full pass at roughly **55–90 minutes** — six to nine times the
600s tool ceiling. The earlier "~30 minutes" estimate in this file was wrong.

So the proof pass runs **the same way this discovery pass did**: batched, but every batch under one
pinned CLI and one unchanged `run.sh`, so all 126 rows share a ruler. `CONTRIBUTING.md` already allows
this — a full pass in one invocation satisfies the bar but is *not* the only way to reach it. The
route is not the proof; `--verify-suite` is.

Then: one edit fixing the register, re-run every job under the new fingerprint, then
`bash tests/eval/run.sh --verify-suite`.

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
