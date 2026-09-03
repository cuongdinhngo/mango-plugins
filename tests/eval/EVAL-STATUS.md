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

## Cycle 2, proof pass — the batch-1 ruler

The discovery pass is finished and its ruler is gone. The v1.15.1 edit landed on 2026-09-03 and
changed `RUNNER_FP`, wiping all 118 `.green` entries. **Batch 1 then found a behavioural red and it was
fixed on the spot**, which moved the ruler a second time and voided batch 1's own 12 rows — see *Batch 1,
attempt 1* below. That is the strategy working, not failing: the loss is 12 jobs at batch 1, and would
have been ~100 at batch 8. Everything below the *Register* describes the discovery pass and is kept only
as evidence of what was found — **no row from it may be cited.**

```
Runner fingerprint  : 1489839c47215913…   (R4 + the transcript archive — the ruler now in force)
Plugin-tree fp      : 9b199a8b5b77c989…   (UNCHANGED — the batch-1 fix is harness-only, no plugin bump)
Model / CLI         : cli-default / 2.1.259 (Claude Code) — PINNED, see below
Suite               : 126 jobs · 511 transcript assertions · dispatch-free self-tests +6 on v1.15.0
Ledger              : empty — 0 of 126 jobs recorded
Superseded rulers   : 3be2609b8f88 — 13 rows from batch 1 attempt 2 (12 green, 1 red), none usable
                      ecf9e4c6bfb0 (v1.15.1) — 12 rows from batch 1 attempt 1, none usable
                      82580ae5a827 (v1.15.0, CLI 2.1.258→.259) — 118 rows, none usable
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
2. **Proof — superseded by a sampling pass, see below.** Under runner `3be2609b8f88` the permitted `run.sh` edits had landed
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
| **Machinery fingerprint** | `4fed82315266` — names the ledger (49 functions, everything above `suite()`) |
| Runner fingerprint | `d7105fd5795a` — forensic only, no longer compared by the gate |
| Plugin-tree fingerprint | `9b199a8b5b77` |
| Jobs recorded | **0 of 126** — the two-tier change moved the machinery, so batches 1-2 re-run once |
| Rows not green | — (fresh ledger). R5's red row stands in the superseded ledger `1489839c4721` as the evidence it was found under. |
| Stale greens | 0 |
| Distinct rulers among rows | 1 |
| `--verify-suite` | 21/22 — the sole failure is `has NO row` defects, and **no other defect class**; at 13 rows it was exactly 113 = 126 − 13 |

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

### Batch 1, attempt 1 — voided by its own fix (ruler `ecf9e4c6bfb0`)

Ran 2026-09-03 with CLI 2.1.259 pinned and both selectors verified dispatch-free beforehand.

| Part | Jobs | Assertions | Slowest job | Dispatch | Result |
|---|---|---|---|---|---|
| 00 | 7 | 97 / 97 | `freeform` 393s | 393s | ✅ green |
| 01 | 6 | 101 / 102 | `vague-requirement` 244s | 244s | 🔴 1 red |

Both parts confirmed the writer fix shipped in v1.15.1: all 5 `coverage-row WRITER` self-tests passed,
and the ledger accumulated across two separate runs (7 → 12 rows) exactly as the coverage gate requires.

**The red, and why it was a wording fix.** `vague-requirement: flags AC-1 as not falsifiable` missed.
The transcript's verdict was *"AC-1 split into two clauses, both flagged as **neither falsifiable nor
excluded**, both barred from a matrix `✅`"* — the correct outcome, phrased with `neither … nor` instead
of `not`. The sibling assertion `cannot carry a bare ✅` passed on that same transcript, which is what
distinguishes a wording miss from an outcome miss: the guard fired, only the token failed to see it. So
the token was widened over wording, to `not falsifiable|(neither|nor) falsifiable|…`, and the widen was
proved in both directions before the ruler moved:

| Check | Result |
|---|---|
| new token vs the real transcript | matches — the red clears |
| new token vs a synthetic wrong outcome (`AC-1 is falsifiable`, carries a `✅`) | no match — still fails |
| **old** token vs the real transcript | miss — so the widen is load-bearing, not cosmetic |
| the added alternative alone vs the wrong outcome | no match |

**No plugin version bump.** The fix is harness-only, so `plugin.json` stayed at 1.15.1 and
`PLUGIN_TREE_FP` did not move. Bumping it would have moved a second identity component for a change
that touched nothing inside the plugin — the trap this document warns about two sections up.

A static sweep for the same `neither … nor` blind spot across the other 513 assertions was **considered
and not acted on**: it can only be judged against a real transcript, and speculatively widening ~40
negation tokens to pre-empt a hypothesis is how a suite stops discriminating. A second ruler move later
is the cheaper mistake. The class is recorded in EVAL-FINDINGS so the next instance is recognised on
sight rather than re-derived.

**Cost of the move:** the 12 rows above are void and batch 1 re-runs in full under `3be2609b8f88`.

### v1.16.0 — identity split in two, so a token fix stops costing 126 dispatches

Chosen 2026-09-03, **before batch 3**, because the cost of making this change grows with every batch
recorded: 34 rows now, ~70 after batch 5, all 126 after batch 10.

The ledger was named by a hash of the whole of `run.sh`, so any edit voided every row. That made the
plan *sampling pass → one fix → proving pass* cost ≥ 252 dispatches with no termination condition —
at the measured red rate (1.7–7.7% per pass) the proving pass is unlikely to be clean first time, and
each retry is another 126. Identity is now two tiers:

| Tier | Covers | An edit voids |
|---|---|---|
| `MACHINERY_FP` (names the ledger) | every function above `suite()` — dispatch, prompt assembly, judging, hashing, row writer, gate | all rows |
| `job_fp` (row field 12) | that job's prompt, test-command, and every `(kind, resolved regex-set)` judging it, sorted | that job's row |

Forward cost becomes **126 + k**, and `--verify-suite` now *names* the stale jobs so k is re-run with
`--only`. A **green** job whose token is edited is re-judged from its cached transcript with no
dispatch at all — the cache survives an assertion edit now — so in practice only red jobs cost.

**12 new dispatch-free self-tests** (21 → 33), each proved to bite: the fingerprint mismatch is caught;
an 11-field pre-v1.16.0 row is refused rather than credited; an *uncomputable* fingerprint fails
instead of skipping; editing one job's assertions strands **only** that job (j1 reported, j2 stands —
the scoping claim itself, tested); a label re-wording moves nothing; a regex edit does; `contains` →
`absent` with the same regex does; no judging function is defined below the boundary; and `declare -f`
is comment-insensitive so a comment edit voids nothing. Rationale and the two design decisions behind
it are in [`EVAL-FINDINGS.md`](./EVAL-FINDINGS.md).

**The hole it closed in passing:** a scenario's prompt is written inline in `run.sh` and was covered by
nothing per-job — the whole-file hash had been carrying it. It is now inside `job_fp`.

**The migration that was refused.** The 35 existing rows could have been credited by computing their
`job_fp` and appending it, since no assertion or prompt had changed. Declined: `MACHINERY_FP` exists so
that "was this harness change harmless?" is not answered by whoever made the change. Batches 1-2
re-run — and the green transcript cache was wiped by the same fingerprint move, so those are real
dispatches, not free re-judges. Last time that bill is paid.

### Batches run — proof pass, superseded ruler `1489839c4721`

| Batch | Group | Parts | Jobs | Assertions | Dispatch | Result |
|---|---|---|---|---|---|---|
| 1 | `analysis` | 2 | 13 | **199 / 199** | 562s + 249s | ✅ **13 green / 0 red** |
| 2 | `refine` | 4 | 22 | 395 / 396 | 333s + 331s + 330s + 371s | 🟡 **21 green / 1 red** — R5, recorded not fixed |

Part 00 (7 jobs) 97/97, slowest `freeform` **562s** — 38s inside the 600s tool ceiling, the narrowest
margin any part has run at. Part 01 (6 jobs) 102/102, slowest `vague-requirement` 249s. Both parts
foreground with `timeout 600`, per EVAL-FINDINGS rule 6. Selectors re-verified dispatch-free against all
126 registered job names immediately before each dispatch: `matches 7 of 126` and `6 of 126`,
named-but-absent 0.

**The two widens held on fresh transcripts.** R3's assertion is in `vague-requirement` and R4's in
`greenfield-recall-handles-none-match`; both fixtures are in this batch, both passed. That is the first
evidence either widen survives a phrasing it was not written against — the offline four/five-direction
proofs showed the token *could* match the archived transcript, not that it matches the next one.

**The archive is now verified, not just declared.** Part 00 wrote 7 transcripts plus `IDENTITY.tsv`
into `.archive/20260903T134714Z-850139/`, part 01 six more — 13 files under two run directories, with
the identity stamp carrying the same `runner_fp`/`plugin_tree_fp`/CLI as the ledger rows. Nothing was
read back from it as a verdict.

**Batch 1 recorded zero reds, and that does not settle the sampling question.** (Batches 1-2 below are
recorded under ruler `1489839c4721`; their rows were voided by the v1.16.0 machinery split above and
both batches re-run. The reds they found — R5 in particular — stand as findings.) Two prior passes over
these same 13 jobs each produced exactly one red, a different assertion each time, so the honest read
is that the per-pass red rate on this batch is low but non-zero and this pass sampled the quiet side of
it. The sampling pass continues as planned: reds are recorded, not fixed, and the remaining 113 jobs
are where the estimate comes from.

#### Batch 2 — R5, the third red of the same class

The 22-member `refine` group was split 6/6/5/5 by an **exact partition check**, not by eye: the four
selectors' union was diffed against the group derived from `FIXTURE_SKILLS` and had to be the identical
set — nothing dropped, nothing in two parts. All four verified `matches N of 126`, named-but-absent 0.
The two likely-heaviest jobs (`greenfield-full-run`, `epic-scaffold-committed`) were deliberately put in
the *same* part so their latencies overlap in one wave instead of serialising across two.

Timings were flat and comfortable — slowest job per part 333s / 331s / 330s / 371s, all ~230s inside the
600s ceiling. This group has no `freeform`-class outlier.

**R5 — `refine-want-unattended-stops`, assertion "want-j: it is NOT recorded as a silent ASSUMED that
ships a PR".** Token:

```
not[ *_]{1,4}(silent|adopt)|never[ *_]{1,4}(silent|assum)|does not|no[ *_]{1,4}silent
```

Measured against the archived red transcript
(`.archive/20260903T151409Z-913165/refine-want-unattended-stops.red.log`): **0 matches**. The transcript
answers the question correctly and in the negative — *"No — `ASSUMED` is not the fallback for silence"*,
*"Silence is not a hand-back"*, *"the ASSUMED block in the working doc is deliberately empty"* — and
prints `0 ASSUMED` twice in its counted REFINE line. What defeated the token is `[ *_]{1,4}`: it allows
at most four spaces/asterisks/underscores between `not` and `silent`, and the real phrasing puts
*"the fallback for"* (17 characters) between them. `does not` does not appear at all.

Same class as R3 and R4 — **a negation token that enumerates adjacencies of `not` and cannot see the
words the model actually put in between.** Third instance, third distinct spelling of the same blind
spot. All five sibling assertions on this fixture passed, including `the run STOPS at Gate 0` and
`no product decision is invented at 3am`, so the mechanism fired and only the wording check missed.

**Not fixed.** Per *The sampling pass*, the widen is deferred to the single offline edit after batch 10,
where it will be swept across the whole archive rather than proved against one transcript. Two candidate
anchors already visible and to be judged then: the counted `0 ASSUMED` (a counted artifact, which binds
harder than prose) and a distance-tolerant negation form. Whether the counted form *replaces* the prose
check or joins it is exactly the R4 question — there, re-anchoring would have deleted a check that a
sibling already covered, so it was refused.

### Batches run — batch 1, attempt 2 (superseded ruler `3be2609b8f88`)

| Batch | Group | Parts | Jobs | Assertions | Dispatch | Result |
|---|---|---|---|---|---|---|
| 1 | `analysis` | 2 | 13 | 198 / 199 | 275s + 414s | 🟡 **12 green / 1 red** — R4 |

Part 00 96/97 (`greenfield-recall-handles-none-match` red, slowest `analysis-section-coverage` 275s);
part 01 **102/102** — which includes `vague-requirement`, so the R3 widen is confirmed in a live run and
not only offline. Ledger holds 13 rows: 12 green, 1 red. The red **is recorded as a row**, so
`--verify-suite` will keep refusing until it is green — the ledger does not quietly drop it.

#### R4, and the thing batch 1 actually discovered

`no-match: the handle-carrying sections are NOT applicable here` failed on a transcript whose verdict was
*"Are §4.2 and §7.3 applicable?* **No — neither source makes them so**", closing with *"a ratified section
blocks only when it is applicable, and neither is."* Correct outcome; `neither` again.

Two things rule out the obvious shortcut. The counted line `RULE SECTIONS: … 0 by recalled handle` is
already asserted **one line above** in `run.sh`, and it passed — so re-anchoring this assertion on the
counted artifact would delete the prose check rather than strengthen it. And the fix cannot be judged
against the discovery pass's transcripts, because **`run.sh` clears `.transcripts/` at the start of every
run**: only the last part's 7 files exist at any time. There is no corpus.

Fix designed and proved offline before being applied (adds `applicab[^.]{0,30}\b(neither|nor)\b` and the
reverse order), on five checks rather than four — the fifth being a *dodge* transcript where the model
declines to judge applicability at all, which the widened token must still reject:

| Check | Result |
|---|---|
| new token vs the real transcript | match |
| **old** token vs the real transcript | miss — load-bearing |
| new token vs a wrong outcome (*"both are applicable… 2 by recalled handle"*) | no match |
| new token vs a **dodge** (*"I could not determine this"*) | no match |
| the added alternatives alone vs the wrong outcome | no match |

**But the finding that matters is not R4.** Part 00 was **97/97 on attempt 1 and 96/97 on attempt 2**, with
a *different* single assertion failing each time, both in the same negation-vocabulary class. That falsifies
the assumption this pass was built on — *"Nothing was left to discover"*. The discovery pass dispatched each
job exactly **once**, so it sampled one phrasing per assertion; an assertion that enumerates spellings of a
negation can only be proven by more than one sample. These are not flaky assertions in the usual sense: the
token is simply narrower than the space of correct answers, and each run draws from that space afresh.

Batch 1 holds 47 transcript assertions and produced one red on each of two passes — ~2%. The discovery
pass's own rate was ~0.4% (2 reds across 511). Both samples are small; the honest range is **2–11 reds per
full 126-job pass**. What decides the strategy is only that it is **not zero**: under *fix-as-found*, every
fix moves `RUNNER_FP`, voids every row already bought, and re-rolls every other assertion — so the pass
converges only if a whole 126-job run comes back with zero reds, which at any of those rates is unlikely.


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

### Register — R1/R2/D1/R3/R4 fixed; **R5 open, recorded not fixed**

| # | Job | Assertion | Class | Evidence |
|---|-----|-----------|-------|----------|
| R1 | `refine-consistency-is-how` | `refine-consistency: NOT asked as a want-decision` | wording / emphasis window | Behaviour **correct**: H1 filed, resolved "apply to ALL consumers sharing the recipe", cited, flagged for ratification. Transcript says *"It was **not** put to the user as an open want"*. Regex is `not .{0,20}(ask\|want-decision\|open want)`; `open want` lands at offset **25** because the `**` emphasis eats 2. |
| R2 | `ledger-gate-complete` (scenario) | `ledger-gate-complete: proceeds, BECAUSE the rows equal the dispatches` | **outcome — underspecified prompt** | Model answered *"Not enough information — row count alone doesn't clear it"*, then split it correctly: every token cell carrying a value or an explicit `unmeasured (…)` → proceeds; any cell blank → blocks, citing `skills/finalise/SKILL.md:230-241`. The prompt fixes the row **count** and says nothing about row **content**, and mango's gate has both conditions. Better behaviour than the assertion expects. |
| R3 | `vague-requirement` | `vague-requirement: flags AC-1 as not falsifiable` | wording / emphasis window | Found in batch 1, not the discovery pass, because the discovery pass's `analysis` batch happened to draw a transcript phrased with `not`. Behaviour **correct**: AC-1 split into two clauses, both flagged, both barred from a matrix `✅`. The verdict was worded *"neither falsifiable nor excluded"*, which the `not …`-only token could not see. Fixed by adding `(neither\|nor) falsifiable`; proved load-bearing and still discriminating in both directions before the ruler moved. See *Batch 1, attempt 1*. |
| R5 | `refine-want-unattended-stops` | `want-j: it is NOT recorded as a silent ASSUMED that ships a PR` | wording / adjacency window — **OPEN** | Found in batch 2. Behaviour **correct**: *"No — `ASSUMED` is not the fallback for silence"*, *"Silence is not a hand-back"*, `0 ASSUMED` printed twice in the counted REFINE line, and all five sibling assertions on the fixture pass. The token's `not[ *_]{1,4}(silent\|adopt)` allows at most four spaces/asterisks between the two words, and the real phrasing puts *"the fallback for"* between them; `does not` never appears. **0 matches** against the archived transcript. Deferred to the post-batch-10 edit by design — see *Batch 2* above. |
| D1 | `skills_files` / `hash_files` | — (kills the run) | **harness — blocking** | A scenario has no `$FIXTURES/<name>.md`, so `cat` fails under `pipefail`+`errexit` and no scenario row can ever be written. `--verify-suite` is unsatisfiable as shipped. Fix: emit that path only `if [ -f … ]`, keeping exit status 0, plus a self-test that writes and verifies a real scenario row. |

**R1, R2 and D1 were fixed** in one edit as planned; R3 and R4 during batch 1's two voided attempts; R5 is open. What shipped for the first three, and what proves each:

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

### The sampling pass — chosen 2026-09-03, replaces fix-as-found

Batch 1 established that a single dispatch per assertion samples **one phrasing**, so the reds left in
this suite cannot all be found by one pass and cannot be fixed one at a time: every fix moves
`RUNNER_FP` and voids every row already bought. Four steps, in order:

| # | Step | Dispatch | Yields |
|---|---|---|---|
| 1 | Apply R4, add the transcript archive | none — **done**, ruler `1489839c4721` | a ruler that keeps its evidence |
| 2 | **Sample:** run all 126 jobs, record reds, **fix nothing** | 126 jobs | the red list **and** 126 archived transcripts |
| 3 | One edit: fix every red, each widened token swept offline against all 126 archived transcripts | none | the class closed, not the instance |
| 4 | **Prove:** run all 126 jobs, then `--verify-suite` | 126 jobs | the proof, if step 3 was right |

Step 2 is a discovery pass under a *new* ruler, which is why batch 1 re-runs with the rest. Its rows are
never citable as proof — only step 4's are. `run.sh` must not be touched between step 1 and the end of
step 2, exactly as in the first discovery pass.

**What the archive changes.** `.transcripts/` is wiped at the start of every run, so until now a token
could only be re-judged against the last part that ran — which is why batch 1 fixed one negation token
per pass instead of the class. `.archive/<RUN_ID>/<job>.<verdict>.log` now keeps every judged
transcript, **reds included**, with an `IDENTITY.tsv` recording the runner, plugin-tree, model and CLI
that produced them. A red transcript is the only record of a phrasing an assertion failed to match; the
greens are what show a widened token has not gone toothless elsewhere. Nothing is ever read back from
the archive as a verdict — it is evidence for offline work, never an input to judging — so it cannot
become a false green. It is git-ignored, like `.transcripts/` and `.cache/`.

The archive is **unverified until step 2's first part**: the fingerprint change wiped the cache, so
there is no cache-hit path to exercise it dispatch-free. Confirm files land before trusting it.

Step 3 is the step this whole plan exists for, and it has a bar: a widened token must be checked
against **every** archived transcript, not just the one that failed — matching where the outcome is
right, and still missing where it is wrong. That is what turns "fix the instance" into "close the
class", and it is free.

### Next — re-run batches 1-2, then batches 3 to 10

Gates on 2026-09-03, under the live machinery `4fed82315266`:

```
python3 scripts/validate.py            → 2057 checks run, 0 failed
python3 tests/envelope/test_envelope.py → 128 tests, OK
bash tests/eval/run.sh --verify-suite  → 33/34; the one failure is the empty ledger, by design.
                                          33 dispatch-free self-tests now, up from 21.
```

That is the state to expect until batch 10 lands: the 21 harness checks pass, and the gate refuses on
row count alone, with the shortfall shrinking by each batch's job count. The freeze is now narrower and
enforced rather than remembered: **do not touch anything above `suite()`** between the first batch and
the last, because that is what renames the ledger. Editing a token inside `suite()` costs exactly the
jobs that token judges, and `--verify-suite` names them.

Then, per batch: pin the CLI, confirm `claude --version`, build the part selectors and verify them
dispatch-free, run, record the row in the table above, commit. **Reds are recorded, not fixed** — see
*The sampling pass* above; fix-as-found was tried in batch 1 and does not converge.

Batch 1 has now been run three times: attempt 1 found R3, attempt 2 found R4, and the third — the only
one whose rows survive — was clean at 199/199. Three operational notes it produced:

- **Run each part in the foreground.** Both background attempts at part 01 were reaped within ~10s of the
  dispatch line — no error, no residue, just `[killed]` — while part 00 had survived 401s in background.
  Foreground with a 600s ceiling is the reliable shape, and it fits every part except possibly batch 7's.
- **Budget the slowest job, never the mean.** With `--workers 8` a part of ≤ 8 jobs is one wave, so a
  7-job part costs its slowest job's latency. Part 00's `freeform` came in at 562s against the 600s
  ceiling — sum 2313s, mean 330s, both irrelevant. Batch 7's `autorun` group is the one still expected
  to test that ceiling.
- **A killed run writes nothing and damages nothing.** Both kills left the ledger at exactly its prior row
  count, the checkout clean, no stray branch, no live process, and no worker clone on disk — checked, not
  assumed, before re-dispatching.

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
