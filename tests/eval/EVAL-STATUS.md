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
| **Machinery fingerprint** | `5c877b488793` — names the ledger (49 functions, everything above `suite()`) |
| Runner fingerprint | `43af5e47dbd8` — forensic only, no longer compared by the gate |
| Plugin-tree fingerprint | `9b199a8b5b77` |
| Jobs recorded | **126 of 126 — all green**, under one uniform ruler. No vacuous credit: R5's pass is now carried by a counted artifact and R6's by claims bound to their objects |
| Rows not green | 0 |
| Stale greens | 0 |
| Distinct rulers among rows | 1 |
| `--verify-suite` | **34/34 — the suite IS proven green.** 126/126 jobs, 511 assertions, every green under machinery `5c877b488793`, plugin-tree `9b199a8b5b77`, model `cli-default`, CLI 2.1.259. See *Closing entry* |

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
| 10 | scenarios | 7 | 2 | ✅ done 2026-09-04 — 7 green. R2 was fixed before it ran and passed live; the first scenario rows ever recorded |

Sums to 126. Each part's selector is built and **verified dispatch-free** immediately before its run —
every name present on disk, every match named, nothing extra — because `--only` matching is unanchored
(`grep -qE "$ONLY"`), so every selector must be `^(a|b|c)$`.

**Batch 7 was the one to watch, and it did get killed — resolved 2026-09-04.** The prediction was that
discovery's 564s `autorun` part was a *single job's* latency, 27s inside the ceiling, so splitting
would only cap the loss at 3 jobs and a kill would write no rows. Both halves held: part 00 was killed
at 600s having written nothing, and the three jobs re-run singly all went green. What did **not** hold
is the premise that a part costs only its slowest job — see *Batch 7* below. The live worst case is
`greenfield-autorun-clean` at **533s solo**, and it must be dispatched alone.

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

### The isolation guard had two defects, and a topic branch found both

Running batch 1 from `eval/cycle-2-proof-pass` failed the guard that exists to prove no fixture
leaked into the live checkout — 7/7 jobs green, one self-test red, and because a failing self-test
taints its run, all 7 rows were worthless. The checkout was pristine.

1. **It hardcoded `main`.** Off main it printed `LIVE CHECKOUT MUTATED — a fixture leaked` plus
   recovery commands, every time. The property it should assert is *the eval left the checkout where
   it found it*, so the expected branch is captured at startup and passed in. On main the two are
   identical — nothing loosened. Making it a parameter could have turned the HEAD check into a no-op,
   so both directions are now asserted: clean-on-a-topic-branch passes against its own branch, and
   still fails against a different one.
2. **`for-each-ref 'refs/heads/*PROJ-*'` never matched a nested branch.** That pattern is fnmatch
   with `FNM_PATHNAME`, so its `*` does not cross a `/`. Measured against `PROJ-777`,
   `feat/PROJ-999-leak` and `fix/PROJ-1-x`: the old pattern found **one**. `feat/PROJ-*` is the shape
   mango's fixtures create — and the shape the guard's own injection test uses. Branches are now
   listed and filtered in `grep`.

**Why it survived nine batches** is the part worth keeping. The injection test built a repo with three
leaks at once — HEAD off main, a stray branch, a work doc — so the guard failed on the other two and
the stray-branch rule was never once proven alone. Every rule now has an isolated non-vacuity test:
correct HEAD, no work doc, only the named artifact. Four new checks.

### Batches run — proof pass, live machinery `5c877b488793`

| Batch | Group | Parts | Jobs | Assertions | Dispatch | Result |
|---|---|---|---|---|---|---|
| 1 | `analysis` | 2 | 13 | **231 / 231** | 331s + 335s | ✅ **13 green / 0 red** |
| 2 | `refine` | 4 | 22 | **460 / 460** | 451s + 296s + 355s + 361s | ✅ **22 green / 0 red** — but one green is vacuous, below |
| 3 | `design` | 3 | 18 | **344 / 345** | 305s + 333s + 342s | **17 green / 1 red** — R6, and part 00 was re-run after a CLI slip |
| 4 | `review` | 3 | 14 | **326 / 327** | 90s + 111s + 78s | **13 green / 1 red** — R7. The fastest batch by far: no part exceeded 111s |
| 5 | `finalise` + `codify` | 4 | 19 | **450 / 450** | 231s + 155s + 256s + 79s | ✅ **19 green / 0 red** — the anchoring rule earned its keep, below |
| 6 | `execute` + `breakdown` | 2 | 8 | **208 / 208** | 256s + 443s | ✅ **8 green / 0 red** — the isolation batch; and `breakdown` is not the light group it was taken for |
| 7 | `autorun` | 3 (part 00 as 3 singles) | 9 | **522 / 522** | 152s + 234s + 533s, then 221s + 92s | ✅ **9 green / 0 red** — **the ceiling kill happened**, and the singles falsified the wave model |
| 8 | `promote` + `solve` | 3 | 9 | **318 / 318** | 40s + 116s + 141s | ✅ **9 green / 0 red** — the fastest batch of the pass; and `greenfield-` turns out not to predict weight |
| 9 | `budget` + `quick` + `init` | 2 | 7 | **216 / 216** | 94s + 229s | ✅ **7 green / 0 red** — **all 119 fixtures are now recorded**; only the 7 scenarios remain |
| 10 | scenarios | 2 | 7 | **196 / 196** | 38s + 22s | ✅ **7 green / 0 red** — **the first scenario rows this repo has ever held**; R2 passed live |

Assertion counts rose (199 → 231) purely from the 12 new dispatch-free self-tests being counted once
per part; no job assertion was added.

**The two-tier split was demonstrated live before it was relied on.** A self-test edit — below the
`suite()` boundary — moved the runner fp from `d7105fd5795a` to `ffc12be6ec1c` while the machinery fp
held at `4fed82315266`, so the ledger name and every row survived a file change. Under the old rule
that edit would have voided the suite.

**And the cross-check that had to hold did:** rows written by a *partial* `--only` run satisfy the
full gate's per-job fingerprint. `--verify-suite` reports 113 `has NO row` defects — 126 − 13 exactly
— and **zero** fingerprint mismatches among the 13 recorded. Had `job_fp` differed between a batched
run and the full registration walk, every batch would have been unbankable and the whole change
worthless.

**Batch 5 — the anchoring rule paid for itself, and the group needed re-deriving.** Two of the 19
selector names are proper prefixes of a *scenario* label: fixture `ledger-content-gate` sits under
scenario `ledger-content-gate-marker`, and fixture `ledger-gate` under `ledger-gate-complete`. `--only`
matches with `grep -qE` and is unanchored, so `--only 'ledger-gate'` would have dispatched a scenario
into a fixture part and reported success. Anchored `^(a|b|c)$` matched `5 of 126`, `5`, `5` and `4`, the
four selectors' union diffed **identical** to the group derived from `FIXTURE_SKILLS`, and
named-but-absent was 0. The group is also 19, not the 17 the discovery pass ran under the same label,
and **all 19 already existed then** (checked against the discovery ledger's 119 names, none absent) — so
what moved is the grouping, not the fixture set. That is the case for re-deriving from `FIXTURE_SKILLS`
each time rather than trusting the plan's own table.

Timings were the most comfortable of any batch: slowest job per part 231s / 155s / 256s / 79s, the worst
of them 344s inside the 600s ceiling. The archive holds 23 new files across four run directories — 19
transcripts plus one `IDENTITY.tsv` each — and nothing was read back from it as a verdict. After the
batch the ledger reduces to 86 jobs, one ruler throughout: 13 fields on every row, one `runner_fp`
(`43af5e47dbd8`), one plugin tree (`9b199a8b5b77`), CLI 2.1.259 on all 86.

**Batch 6 — the batch that mutates git, and it left nothing behind.** The 8 jobs were split by skill
rather than alphabetically, so all four `execute` jobs — the ones that branch and commit — sat in part
00 and the four `breakdown` jobs in part 01. That is deliberate: if the isolation guard tripped, the
part would name the cause without a bisect. It did not trip. Both parts passed every guard on the live
run, and the guards that matter here are the ones the topic-branch defect (above) had made
unprovable: `live checkout untouched after full eval (HEAD on eval/cycle-2-proof-pass, no stray
*PROJ-* branch, no work doc)`, `all 4 per-worker clone(s) disposed`, and `all 4 job(s) started from the
provisioned baseline`. Checked independently after the batch as well, not just believed: HEAD still
`f64d4f0` on `eval/cycle-2-proof-pass`, working tree clean, zero `PROJ-` branches in **any** namespace
(listed with `for-each-ref refs/heads` and filtered in `grep`, per the fnmatch defect), zero worker
clones on disk.

**`breakdown` is heavier than the plan assumed, and that matters for batch 7.** `epic-lesson-capture`
took **443s** — 157s of ceiling margin, the narrowest of this pass apart from batch 1's `freeform` at
562s — in a group the plan carried as an afterthought next to `execute`. Nothing predicted it: in the
discovery pass `breakdown` was folded into batch 9's small groups, whose 752s total across four parts
hid it. So batch 7's `autorun` is not the only ceiling risk left, and the rule stands unchanged —
budget the slowest job, never the mean, and re-measure rather than inherit an assumption about which
group is light.

**Batch 7 — the predicted ceiling kill arrived, and the fallback worked exactly as written.** Part 00
held both `greenfield-*` jobs, deliberately placed together so their latencies would overlap in one
wave. Dispatched as a wave of 3 it hit the 600s ceiling: `rc=124`, and — as documented — the ledger
stayed at exactly its prior 100 rows, the tree clean, HEAD unmoved, no stray `PROJ-` branch, no worker
clone, no `/tmp` residue newer than the kill. Re-run as **single jobs** per the plan, all three went
green: 152s, 234s and 533s.

**That falsifies the sizing model this document has used since batch 1.** The rule was "with
`--workers 8` a part of ≤ 8 jobs is one wave, so the part costs its *slowest job*" — 533s, comfortably
inside 600s. What actually happened is that **every job in the wave was inflated**, not just the
slowest: `autorun-budget-degrades` alone takes 152s and had still not finished at ~591s in the wave,
a ≥3.9× inflation, and neither of the two transcripts the kill left behind had completed (both end
mid-sentence). So a wave costs *more* than its slowest job, and the surcharge is large enough to turn a
67s margin into a kill.

It is also not a constant. The same hour, part 01 (3 jobs) came in at 221s and part 02 (3 jobs) at 92s
with no sign of inflation, and batches 5-6 ran 4- and 5-job waves at up to 443s without trouble. What
distinguished the killed wave is that it contained a job already near the ceiling. **The cause is not
established** — host CPU, API-side concurrency limits and per-job token volume are all candidates and
none was measured — so the rule is stated as the observation, not the theory: *budget the slowest job
and leave real headroom; a job that takes over ~450s alone must be dispatched alone.*
`greenfield-autorun-clean` at **533s solo — 67s of margin** — is that job, and it is now the known
worst case in the suite, ahead of batch 1's `freeform` at 562s in a 7-job wave.

One incidental correction, worth recording because it nearly caused a false alarm: the post-kill check
for surviving processes used `pgrep -f 'tests/eval/run.sh'` and `pgrep -f 'claude '`, both of which
**matched the checking script's own command line** and reported a live run plus two stray dispatches.
There were none. Use a self-excluding pattern (`eval/[r]un.sh`) when checking for eval residue.

**Batch 8 — the fastest batch of the pass, and a heuristic of mine that did not survive contact.**
Three parts rather than the plan's two: `greenfield-promote-zeros` was given its own dispatch because
it is the one greenfield-class job in the group and that class had just produced batch 7's 533s worst
case, so under the new rule it looked like a candidate to run alone. It took **40s**. The prefix means
*empty-repo baseline*, not *long run* — `greenfield-autorun-clean` is slow because of `autorun`, not
because of `greenfield`. The caution cost one extra dispatch and bought a correction worth more than
that: **job name prefixes do not predict latency; only a measured solo time does.**

Everything else was uneventful, which is itself the point after batch 7 — parts of 4 came in at 116s
and 141s, the whole batch dispatched in 297s across three parts, 318/318 assertions, and the slowest
single job in the group (`workdoc-solve-autopath`, 141s) sits nowhere near the ceiling.

**Batch 9 — the fixture half of the suite is complete.** Two parts of 4/3, 7 jobs, 216/216, dispatch
94s and 229s, nothing near the ceiling. With it the ledger reaches **119 of 126** and the residual is
exact: the 7 jobs `--verify-suite` still reports as `has NO row` are precisely the 7 scenarios
(`artifact-delta-emission`, `carveout-nonexempt`, `design-invalidated`, `ledger-content-gate-marker`,
`ledger-gate-complete`, `per-clause-both`, `stuck-detector`) — checked by diffing the recorded names
against the 126 registered, not by subtraction. Every one of the 119 **fixtures** now carries a green or
red row under machinery `5c877b488793`, one ruler, 13 fields, CLI 2.1.259 throughout.

That makes batch 10 the whole of the remaining risk, and it is the batch with the least precedent:
scenarios are the jobs that **no pass has ever recorded**. Defect D1 — a file-less job could not produce
a coverage row at all, so `--verify-suite` was unsatisfiable as shipped — was fixed in v1.15.1 and its
fix is exercised every run by the row-writer self-tests, but always against a *synthetic* file-less
control. The `NOTE: row-writer: this run registered no scenario, so the real-label proof did not run`
line has appeared in every part of every batch so far. Batch 10 is the first time that proof runs
against a real registered scenario label. It also carries **R2**.

**Batch 10 — the scenarios are recorded, and the bar is satisfiable.** Two parts of 4/3, 7 jobs,
196/196 assertions, all green, dispatched in 38s and 22s — the cheapest batch in the suite by an order
of magnitude. Three things it settles that no earlier run could:

1. **D1's fix works on a real label, not just a synthetic control.** Every part of every batch before
   this one printed `NOTE: row-writer: this run registered no scenario, so the real-label proof did not
   run`. Batch 10 replaced it with `PASS: row-writer: the REAL registered scenario 'design-invalidated'
   yields a green row (the shipped bar is satisfiable)` in part 00 and the same for `per-clause-both` in
   part 01. The seven rows carry `scenario` in field 2 and satisfy the gate.
2. **R2 passed on live output.** `PASS: ledger-gate-complete: proceeds, BECAUSE the rows equal the
   dispatches`. R2 was an *outcome* red caused by an underspecified prompt, and the fix completed the
   scenario's premise rather than widening the assertion — this is the first evidence that fix holds
   against a fresh transcript, and the assertion is still the one that was failing.
3. **Scenarios mint no cache entries.** Both parts reported `0 cache-hit(s), 0 fresh run(s)` and
   `0 cache entry(ies) minted` while judging 7 jobs green. The transcript cache is keyed on a fixture's
   skills hash, and a scenario has no fixture, so scenarios re-dispatch on every run. At 16-37s each
   that is not worth changing, and it means the CLI-version gap in the cache key (below) cannot affect
   them.

**`has NO row` is now 0 — the first time in this repo's history.** The gate still refuses, and its
refusal is now exactly the two open reds (R6, R7) and nothing else: no missing row, no fingerprint
mismatch, no pre-identity row, no different-ruler row, no stale green. One ruler across all 126 rows,
13 fields on each.

### The R5/R7 edit — what it fixed, and what it did not

Landed after batch 10 as the first half of the single edit. Both tokens live **inside** the `job_fp`
tier: `MACHINERY_FP` hashes `declare -f` over the 49 functions above `suite()`, and a regex *variable*
is not a function, so the ledger was never renamed. `--verify-suite` then stranded exactly the two
edited jobs and left the other 124 rows standing — the two-tier split doing precisely what
[`321d32e`](#) was written for.

**R5 — fixed, and the old token was wrong in both directions.** Measured against the archive, not
argued: the free-floating `does not` alternative made it a **demonstrated** false green, not a
suspected one. A negative control in which mango records `2 ASSUMED` and ships the PR **passes** the
old token, on the same unrelated merge-strategy phrasing (`narrows, does not remove, the judgement`)
that carried the archived green. The same token **missed** the correct wording, because mango writes
"No — `ASSUMED` is not the fallback for silence" and the old window allowed four glyphs between `not`
and `silent`. Deleting `does not` alone leaves *both* correct transcripts red — checked. So the fix
deletes it **and** widens over the claim's own subject bounded by `[^.]`, **and** admits the counted
artifact `0 ASSUMED` inside the `REFINE:` line, with `[^0-9]` before the zero so `10 ASSUMED` cannot
match. Hoisted to `RE_NOT_SILENT_ASSUMED` with two paired self-tests, each `.correct` carrying exactly
one readable form so it can only pass through the alternative it is named for.

The re-judge cost **zero dispatches** — `run.sh:1435-1440`, a token fix on a green job re-reads its
cached transcript — and it passed through the **counted-artifact** branch, with the widened window
scoring 0 on that transcript. That is the branch that replaced the vacuous pass, so the edit is
load-bearing and the job is now proven rather than credited.

**R7 — the token is stronger; the green is not the edit's doing.** State this plainly. The token now
drops free-floating `does not` for the same reason R5 did, and gains the shape the batch-4 transcript
actually used — a negative asked as a question and answered on the same line, `## 3. Does "84 passed"
establish AC1 and AC2? No — for two independent reasons.` — which no `not … establish` window can
reach. A new self-test proves that branch reads the correct form and still misses a transcript asking
the identical question and answering "Yes"; `grep`'s line-bounding does that work.

But the re-run's fresh transcript passed via **`false.?green`**, a branch the *old* token already
carried, and the new question-answered branch scored **0** on it. So the old token would have passed
this sample too: **R7's red was a sampling artifact, and the re-dispatch is what cleared it, not the
fix.** The fix's value is that the archived phrasing is now readable at all, and that one false-green
path is gone. This is the third job in this cycle to change verdict with nothing but a new dispatch.

**Two things found while doing it, both recorded rather than fixed:**

- **`--verify-suite` does not run the assertion-convention or row-writer self-tests.** It stops at
  `run.sh:3162`, after `coverage_selftest` and the gate. Its "33/34" is those checks plus the gate —
  *not* the 33 dispatch-free self-tests the gate block in *Next* implies. Those run only in a
  dispatching run. The gate block's wording is corrected below.
- **R6's three passing assertions are largely vacuous, and that is worse than its red.** Its
  transcript is 3 lines: mango pointed at `docs/tickets/PROJ-410.work.md` instead of answering the
  four questions. A1 passes on `expiry` — from mango *deferring* the question — plus `missing`, from
  its description of the file's contents; A3 passes on `expiry` + `checkable` out of that same clause.
  Only A2 (`Gate 2` + `blocked`) is sound. `assert_all` requires each regex to match *somewhere in the
  body*, not within one claim, so a reply that answers nothing scores 3 of 4. This is the
  harness-header vacuity class again, one level up, and the fix is `assert_all` semantics — machinery,
  so cycle 3.

### The CLI pin was written down and never actually applied

Batch 3 part 00 came back 6/6 green and reported **CLI 2.1.260**. Every earlier row says 2.1.259. The
gate compares `plugin-tree / model / CLI` as one identity tuple, so a mixed ledger is a refusal
condition — the exact failure *Pin the CLI for the whole pass* was written to prevent, recurring one
batch after the document warning about it.

The cause is not the CLI. It is that the pin is an `export PATH=…` in a document, and **every dispatch
runs in a fresh shell**, so no run of this pass ever had the pin on `PATH`. Batches 1 and 2 recorded
2.1.259 because the auto-update had not happened yet — luck, not process. The pin directory was
correct and in place the whole time; nothing ever consulted it.

Two things had to be undone, and the second was nearly missed:

- **The six rows.** `verify_suite` reduces the ledger with `awk 'NF>=11 {r[$1]=$0}'`, so the *last*
  row per job wins. Re-running the six under the pin supersedes them; no ledger was hand-edited.
- **The six cached transcripts.** The cache key is `$name.$skills-hash.green` — it carries **no CLI
  version**. A plain re-run would have hit those cache entries, re-judged the 2.1.260 transcripts, and
  written rows stamped 2.1.259. The row would have been a lie about which CLI produced the evidence.
  They were deleted by name first, leaving exactly the 35 entries the valid rows accounted for.

After the pinned re-run: 53 rows, **all at 2.1.259**, `different-ruler` defects **0**.

That cache-key gap is worth stating on its own, because it outlives this incident: **a transcript
cached under one CLI is silently reusable under another.** The skills-hash catches skill edits and
`job_fp` catches assertion edits, but nothing in the key notices that the thing which produced the
transcript changed. Queued for the post-batch-10 edit — it belongs above `suite()`, so it cannot be
touched until the ledger is complete.

Every dispatch from batch 3 onward begins `export PATH="$HOME/.cache/mango-eval-cli-pin:$PATH"` and
prints `claude --version` in the same command, so the pin is visible in the log beside the run it
governed rather than asserted in a document.

### R6 — the counted line was written to a file the assertion cannot see

`exclusion-expiry-required` scored 3 of 4. The failure is
`assert_contains "expiry-required: the EXCLUSIONS counted line is emitted" "$t" 'EXCLUSIONS:'`, and
the transcript is four lines long:

> `docs/tickets/PROJ-410.work.md:1` holds the Phase 2 section — verification plan, the exclusion
> record with the missing field named, **the counted line**, and the two unblock paths.
>
> Design stops here at Gate 2, blocked. I did not write code and did not close the gate; whether
> AC1(b) is upgraded to a real-corpus run or deferred with a checkable expiry is your decision.

The three sibling assertions all pass: the no-expiry exclusion does not count as recorded, Gate 2 is
blocked, and the fix named is a checkable expiry. The behaviour under test is right. What failed is
that mango **wrote the counted artifact into the work doc and referenced it** instead of echoing it
into the reply, and this suite judges the transcript only.

So R6 is neither a wording red nor an outcome red — it is a **visibility** red, and the widening rule
does not reach it. Widening `EXCLUSIONS:` would be worse than useless: the point of a counted-artifact
assertion is that the count binds, and a looser pattern would accept prose *about* a count.

The honest limit on this entry: the harness keeps no copy of the fixture's work doc, and the worker
clone is gone, so **it cannot now be confirmed that the file really carried the `EXCLUSIONS:` line**.
The transcript claims it did. That the only evidence which would settle the question is the one thing
the harness discards is itself part of the finding.

Recorded, not fixed. The candidate fixes are structural and belong to the post-batch-10 edit: have the
prompt require the counted line in the reply, or have the harness preserve and judge the work doc.

### R5 came back green, and the green proves nothing

R5 was expected to reappear in batch 2 part 03. It did not: `refine-want-unattended-stops` went
**green**, with its token unchanged — R5 was recorded, not fixed, so nothing about the assertion moved
between the red and the green.

A red that stops reproducing against an unchanged assertion is not a fixed red. It was checked offline
against both archived transcripts, and the result is worse than a flake. The token is
`ASSUMED` **and** `not[ *_]{1,4}(silent|adopt)|never[ *_]{1,4}(silent|assum)|does not|no[ *_]{1,4}silent`:

| Branch | Red transcript (44 lines) | Green transcript (55 lines) |
|---|---|---|
| `not[ *_]{1,4}(silent\|adopt)` | 0 | **0** |
| `never[ *_]{1,4}(silent\|assum)` | 0 | **0** |
| `no[ *_]{1,4}silent` | 0 | **0** |
| `does not` | 0 | **4** |

Every branch that actually tests the claim missed the green transcript too. The pass was carried
entirely by `does not`, and the lines it fired on are these:

- `merge-strategy: squash-or-rebase (first-parent topology; narrows, does not remove, the judgement)`
- `… so reading the verdict is mine: Gate 0 does not close.`
- `… a guess mango made about intent it does not own …`
- `… PROJ-903: j = 0, and the self-skip does not change it.`

A configuration line about merge strategy satisfied an assertion about whether mango silently records
an `ASSUMED`. `judged_body` strips only `^== fixture: ` / `^== scenario: `, so all four lines are inside
the judged text. The companion pattern `ASSUMED` is no help either: the fixture's transcript prints
that word whatever it decides.

**So R5 is not a wording-window red. It is a false-green assertion, and it is the more serious class.**
The behaviour was correct in both runs; what changed was only whether the model happened to write two
common words. R5 stays **OPEN** and is carried into the post-batch-10 edit, where the fix is to delete
the `does not` branch and bind the surviving ones to the claim — not to widen anything.

One row in the ledger is therefore credited on a pass that discriminates nothing. It is left standing
rather than hand-edited: removing the token's dead branch changes that job's `job_fp`, so
`--verify-suite` will name `refine-want-unattended-stops` as stale and re-run **that job alone**. This
is the first time the two-tier ruler has been the thing that makes an honest correction affordable.

#### How wide is the class — measured, not guessed

The same sweep was run over all 511 assertion call sites, splitting each regex on its top-level `|`
and flagging any branch that is bare common English. Base rates over the 77 archived transcripts:

| Branch | Transcripts matched |
|---|---|
| `not`, `no`, `on` | **77 / 77 (100%)** |
| `this` | 71 / 77 (92%) |
| `only` | 64 / 77 (83%) |
| `would`, `can` | 58 / 77 (75%) |
| `never` | 55 / 77 (71%) |
| `does not` | 35 / 77 (45%) |

**39 assertions across 31 jobs** carry such a branch. Two facts bound the damage:

- **No `assert_absent` is affected** (35 are `assert_all`, the rest `assert_contains`), so this class
  can only ever produce a false green, never a false red. Nothing already recorded as red is suspect.
- **No affected argument consists only of the weak branch** — every one sits in an alternation beside
  specific siblings, so the argument is not dead by construction, only satisfiable by prose.

Of the 7 affected jobs already banked green, each was re-checked against its own archived transcript to
see whether a discriminating branch actually fired. Six did. **One did not: R5's.** So the class is real
and worth fixing at the source, but exactly one banked green is currently unproven, and it is the one
already named above.

### Batches run — superseded ruler `1489839c4721`

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

### Register — **all eight fixed**; R5/R6/R7 closed 2026-09-04, see *Closing entry*

| # | Job | Assertion | Class | Evidence |
|---|-----|-----------|-------|----------|
| R1 | `refine-consistency-is-how` | `refine-consistency: NOT asked as a want-decision` | wording / emphasis window | Behaviour **correct**: H1 filed, resolved "apply to ALL consumers sharing the recipe", cited, flagged for ratification. Transcript says *"It was **not** put to the user as an open want"*. Regex is `not .{0,20}(ask\|want-decision\|open want)`; `open want` lands at offset **25** because the `**` emphasis eats 2. |
| R2 | `ledger-gate-complete` (scenario) | `ledger-gate-complete: proceeds, BECAUSE the rows equal the dispatches` | **outcome — underspecified prompt** | Model answered *"Not enough information — row count alone doesn't clear it"*, then split it correctly: every token cell carrying a value or an explicit `unmeasured (…)` → proceeds; any cell blank → blocks, citing `skills/finalise/SKILL.md:230-241`. The prompt fixes the row **count** and says nothing about row **content**, and mango's gate has both conditions. Better behaviour than the assertion expects. |
| R3 | `vague-requirement` | `vague-requirement: flags AC-1 as not falsifiable` | wording / emphasis window | Found in batch 1, not the discovery pass, because the discovery pass's `analysis` batch happened to draw a transcript phrased with `not`. Behaviour **correct**: AC-1 split into two clauses, both flagged, both barred from a matrix `✅`. The verdict was worded *"neither falsifiable nor excluded"*, which the `not …`-only token could not see. Fixed by adding `(neither\|nor) falsifiable`; proved load-bearing and still discriminating in both directions before the ruler moved. See *Batch 1, attempt 1*. |
| R5 | `refine-want-unattended-stops` | `want-j: it is NOT recorded as a silent ASSUMED that ships a PR` | **false green** (was: wording / adjacency window) — **FIXED** (v1.16.1) | Found in batch 2. Behaviour **correct**: *"No — `ASSUMED` is not the fallback for silence"*, *"Silence is not a hand-back"*, `0 ASSUMED` printed twice in the counted REFINE line, and all five sibling assertions on the fixture pass. The token's `not[ *_]{1,4}(silent\|adopt)` allows at most four spaces/asterisks between the two words, and the real phrasing puts *"the fallback for"* between them; `does not` never appears. **0 matches** against the archived transcript. Re-run under the live ruler with the token **unchanged**, it went green — and offline measurement shows the pass came only from the free-floating `does not` branch, firing on a merge-strategy config line. All three branches that test the claim scored **0** on the green transcript too. Reclassified: not a narrow window but a false green. Deferred to the post-batch-10 edit, where the fix is to **delete** `does not` and bind the rest — see *R5 came back green* above. |
| R6 | `exclusion-expiry-required` | `expiry-required: the EXCLUSIONS counted line is emitted` | visibility → **FIXED** (v1.16.1) by binding each claim to its object | Found in batch 3. Behaviour **correct**: the three sibling assertions all pass (no-expiry exclusion not counted as recorded, Gate 2 blocked, checkable expiry named). The 4-line transcript says the work doc `docs/tickets/PROJ-410.work.md` holds *"the counted line"* — mango wrote the artifact to the file and referenced it rather than echoing it, and this suite judges the transcript only. Not a wording red, so the widening rule does not reach it; widening `EXCLUSIONS:` would accept prose about a count, which is the opposite of what a counted-artifact assertion is for. The harness keeps no copy of the work doc, so the claim cannot now be confirmed. |
| R7 | `evidence-stale-tree-refused` | `evidence-stale: 84 passed does not establish the ACs on b7d5e29` | wording — the negation is a **question answered "No"** — **FIXED** (v1.16.1) | Found in batch 4. Behaviour **correct and unusually thorough**: 90 lines, the other four assertions pass, and section 3 answers this assertion's exact question twice — wrong tree, and wrong instrument with the linter contradicting it. The heading reads `## 3. Does "84 passed" establish AC1 and AC2? No — for two independent reasons.`, so the only line carrying both claim and denial spells the verb **affirmatively** and puts the negation after the question mark. All five alternatives of `RE_DOES_NOT_ESTABLISH` score **0**. No synonym list or window widening inside a `not … establish` shape can read that. |
| D1 | `skills_files` / `hash_files` | — (kills the run) | **harness — blocking** | A scenario has no `$FIXTURES/<name>.md`, so `cat` fails under `pipefail`+`errexit` and no scenario row can ever be written. `--verify-suite` is unsatisfiable as shipped. Fix: emit that path only `if [ -f … ]`, keeping exit status 0, plus a self-test that writes and verifies a real scenario row. |

**R1, R2 and D1 were fixed** in one edit as planned; R3 and R4 during batch 1's two voided attempts; **R5, R6 and R7 in the post-batch-10 edit** — R5 on a counted artifact at zero dispatch cost, R7's token strengthened though its green came from a fresh sample, R6 after two instrument errors of my own. Details in *Closing entry*. What shipped for the first three, and what proves each:

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

### Next — cycle 2 is closed; cycle 3 opens with the machinery group

**Cycle 2 is closed: the suite is proven green, 126/126.** See *Closing entry* for the gate output
and for what that sentence may and may not claim. Gates on 2026-09-04:

```
python3 scripts/validate.py            → 2057 checks run, 0 failed
python3 tests/envelope/test_envelope.py → 128 tests, OK
bash tests/eval/run.sh --verify-suite  → 34/34, the suite IS proven green: 126/126 jobs, 511
                                          assertions, one uniform ruler. NOTE: these 34 are
                                          coverage_selftest plus the gate — verify stops at
                                          run.sh:3162 and never reaches the assertion-convention
                                          or row-writer pairs, which run only in a dispatching run.
```

The freeze held for all ten batches: nothing above `suite()` was touched, so the ledger was never
renamed and no batch was paid for twice. It stays in force until the edit below, because that is what
renames the ledger — whereas editing a token *inside* `suite()` costs exactly the jobs that token
judges, and `--verify-suite` names them.

**What remains is one offline edit, then a bounded re-run.** Per *The sampling pass*: reds were
recorded, not fixed, and all three open ones plus the cache-key gap are fixed together —

- **R5** — delete the free-floating `does not` branch and bind the survivors. It is a false green: the
  branch that made it pass fires on a merge-strategy config line, and all three branches that actually
  test the claim score 0 on the green transcript.
- **R6** — structural, not a widen. Either require the counted line in the reply, or preserve the work
  doc and judge that. Widening `EXCLUSIONS:` would accept prose about a count, which defeats the point
  of a counted-artifact assertion.
- **R7** — needs a shape that can read a question answered "No". No synonym list or window inside a
  `not … establish` shape can match a heading whose verb is affirmative and whose negation follows the
  question mark.
- **The cache key** — `$CACHE_DIR/$name.$h.green` carries no CLI version, which is what let batch 3
  nearly stamp 2.1.260 transcripts as 2.1.259. Add the identity tuple. This one lives above `suite()`,
  so it is why the edit is deferred rather than done now.

Sweep every widened or narrowed token offline across the archive first, then re-run **only** the jobs
`--verify-suite` names stale — the two-tier ruler means a token edit strands its own jobs and nothing
else — then paste the passing gate output into the *Closing entry* block. Note that the 7 scenarios
re-dispatch regardless: they mint no cache entries, at 16-37s each.

Operational notes from the ten batches, worth keeping for the next cycle:

- **Run each part in the foreground.** Both background attempts at part 01 were reaped within ~10s of the
  dispatch line — no error, no residue, just `[killed]` — while part 00 had survived 401s in background.
  Foreground with a 600s ceiling is the reliable shape. Every part of all ten batches ran foreground;
  the only ceiling casualty was batch 7 part 00, and re-running it as singles cleared it.
- **Budget the slowest job and leave headroom — a wave costs more than its slowest member.** The mean
  and the sum are still irrelevant (batch 1 part 00: `freeform` 562s, sum 2313s, mean 330s). But
  batch 7 falsified the stronger claim that a part costs *only* its slowest job: a 3-job wave whose
  worst member takes 533s alone was killed at 600s with **all three** jobs unfinished — the 152s member
  included, a ≥3.9× inflation. The surcharge is not constant (3-job waves the same hour finished at
  221s and 92s), and its cause is unmeasured. Operationally: **a job over ~450s solo is dispatched
  alone.** The known one is `greenfield-autorun-clean` (533s).
- **A killed run writes nothing and damages nothing.** All three kills — two background reaps in
  batch 1, one ceiling kill in batch 7 — left the ledger at exactly its prior row count, the checkout
  clean, no stray branch, no live process, no worker clone on disk, and in batch 7's case no `/tmp`
  residue newer than the kill. Checked, not assumed, before each re-dispatch.
- **Check for eval residue with a self-excluding pattern.** `pgrep -f 'tests/eval/run.sh'` and
  `pgrep -f 'claude '` both match the *checking* script's own command line and will report a live run
  and stray dispatches that do not exist. Use `eval/[r]un.sh`.
- **A name prefix predicts nothing about latency.** `greenfield-autorun-clean` takes 533s and
  `greenfield-promote-zeros` 40s. Only a measured solo time justifies a solo dispatch.
- **Anchor every selector, and re-derive every group.** Batch 5's `ledger-gate` and
  `ledger-content-gate` are proper prefixes of two *scenario* labels; unanchored, they would have
  dispatched a scenario inside a fixture part and reported success. And the `finalise`+`codify` group
  derives to 19 where discovery ran 17 under the same label, with no fixture added since — the
  grouping moved, not the fixture set.

### Closing entry — cycle 2 proof pass, closed 2026-09-04

```
Suite proven green at SHA : see the commit carrying this entry (branch eval/cycle-2-proof-pass)
Date                      : 2026-09-04
Total jobs                : 126   (119 fixtures + 7 scenarios)
Batches needed            : 10, plus 4 single-job re-runs for the token edits
Reds fixed from register  : R5, R6, R7  (R1/R2/R3/R4/D1 were fixed earlier in the cycle)
New findings              : the wave surcharge (batch 7), `assert_all` claim-binding (R6),
                            --verify-suite's check set, `[^\n]` in POSIX ERE — all below,
                            and the durable ones move to EVAL-FINDINGS.md

--verify-suite output, verbatim:

== eval coverage verification (no dispatch, no cost) ==
  machinery fp       : 5c877b488793c4af711a7b476d44b71c39a1f0ec813fbde14ccf4ad860fe4428  (49 function(s))
  runner fp (forensic): 17a32e08e97f2e725d5dac92a18c2278002b8c3446c787662dfc13acc18a32d7
  plugin-tree fp     : 9b199a8b5b77c9898b3db2975545d02973fd1b94cbbccf63617820c4a91970ec
  model / CLI        : cli-default / 2.1.259 (Claude Code)
  jobs registered    : 126
  [18 dispatch-free self-tests — header-vacuity, no-run guard, row-writer, two-tier ruler — all PASS]

== coverage ledger vs the suite ==
  suite            : 126 job(s), 511 transcript assertion(s)
  ledger           : coverage.5c877b488793c4af711a7b476d44b71c39a1f0ec813fbde14ccf4ad860fe4428.tsv
  PASS: coverage: all 126 job(s) green under one uniform ruler, 511 assertion(s) accounted for

EVAL VERIFY: 34/34 check(s) pass.
EVAL VERIFY: the suite IS proven green — 126/126 job(s), 511 assertion(s),
             every green measured under machinery 5c877b488793, plugin-tree 9b199a8b5b77,
             model cli-default, CLI 2.1.259 (Claude Code). Equivalent to one full pass.
```

**What this sentence may and may not claim.** It may claim: every one of the 126 jobs was dispatched
against a real transcript and judged green under a single measurement identity, and that fact is
re-checkable from the ledger by anyone who runs the gate. It may **not** claim that each job would go
green on the next dispatch — three jobs changed verdict in this cycle with nothing but a new sample
(R7 and R6 twice), and the measured per-pass red rate of 0.4-2% predicts 2-11 reds in any fresh full
pass. A green suite here means *the ruler is sound and every job has cleared it once*, not that the
suite is deterministic.

**The R6 close, in order, because the sequence is the finding.** Its red was `EXCLUSIONS:` missing
from a 3-line reply that pointed at the work doc. Tightening A1 and A3 to bind each claim to its
object, then re-running, produced a **different** red: A3 failed. That failure was **mine, not
mango's** — mango had added the field with a *condition* as its value (`expiry: when
config.real_corpus_path is configured`) and asserted the property in the skill's own words one
sentence later ("is checkable by a non-author"), while my first token demanded `checkable` adjacent to
`expiry` adjacent to an action verb on one line. Corrected, re-run, 4 of 4. So the job went
red → red-for-a-new-reason → green across three dispatches, and only the last red was worth anything.
Two of the three reds this fixture produced were instrument error.

**Four findings, recorded here and carried to EVAL-FINDINGS.md:**

1. **A wave costs more than its slowest member** (batch 7). A 3-job wave whose worst member takes 533s
   solo was killed at 600s with all three unfinished — the 152s member included. Cause unmeasured;
   operationally, a job over ~450s solo is dispatched alone.
2. **`assert_all` binds nothing.** Each regex must match somewhere in the body, not within one claim,
   so a reply that answers nothing can score 3 of 4 on bare adjectives — `missing` and `checkable`
   carried R6's two vacuous passes, and every other alternative scored 0. Binding inside the
   alternative is the only fix available without changing the harness. The harness fix is cycle 3.
3. **`--verify-suite` runs 34 checks, not the suite's self-tests.** It stops at `run.sh:3162`, so
   assertion-convention and row-writer pairs run only in a dispatching run. Both were needed to prove
   these token edits, and neither would have been exercised by the gate alone.
4. **`[^\n]` does not mean "any character on this line" in POSIX ERE.** Inside a bracket expression it
   is "not backslash, not the letter n", and it silently failed on `config.real_corpus_path`. `grep`
   is line-bounded, so plain `.` is correct.

**Deferred to cycle 3, deliberately, because each is machinery and costs 0 at a cycle boundary and 126
dispatches here:** the `assert_all` claim-binding above; the cache key's missing identity tuple
(`$name.$h.green` — a transcript cached under one CLI is silently reusable under another); and
preserving the work doc so a counted-artifact assertion can be judged where mango actually wrote it.
