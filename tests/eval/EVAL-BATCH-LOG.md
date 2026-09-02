# EVAL-BATCH-LOG.md

Tracking file for the batched full eval. **Fill a row in as soon as a batch finishes** — a batch whose
result was never written down did not happen, and that is the exact gap that let four assertions ship
having never run.

Keep this file in the repo, next to `EVAL-PROFILE.md`.

---

## Run header — fill this once, before batch 1

```
RUN ID              : eval-2026-09-01
Started             : 2026-09-01 — pre-flight only, no dispatch yet
Plugin version      : 1.14.2
Pre-flight SHA      : 4196c3eb467c65996636c80576cc3e5e019dd66e
HEAD SHA            :        ← record per batch row; docs commits move it, the fingerprint does not
run.sh fingerprint  : e23452eb45532e966e6f0a89290b8573fc5b179100c99ec1716796f727d1da28
Total jobs expected : 126     ← VERIFIED: 119 fixtures + 7 scenarios
Batches planned     : 10
```

> **The fingerprint is the run's identity.** If it ever differs from the value above, every batch already
> recorded is void and the run restarts from batch 1. Check it before each batch; record it in each row.

---

## Pre-flight — 2026-09-01, at `4196c3e` (no dispatch, source-read only)

| # | Check | Result |
|---|---|---|
| 1 | Working tree committed | ✅ clean apart from this file |
| 2 | Fingerprint recorded | ✅ `e23452eb…1da28` (`hash_files` = sha256 of `run.sh`, `run.sh:480`) |
| 3 | Known assertion fixes landed | ✅ Class-A `--` in all three assert helpers (`run.sh:856,877,898`); Class-B widenings + `reset_sandbox` per job in `dcd236b`/`9ab6994`/`4196c3e` |
| 4 | Batch-1 selector verified | ✅ 10/10, anchored alternation, matched with the same `grep -qE` as `job_selected` (`run.sh:721`) |
| 5 | Cache keying confirmed | ✅ per-fixture, and **all 119 fixtures are mapped** — no fixture falls back to the hash-all-skills path |

**Cache key (`skills_files`, `run.sh:438`)** — a fixture's `.green` survives a change to a skill it does
not map to, but **not** a change to any of: `PRINCIPLES.md`, `principles/*.md`, `agents/*.md`,
`templates/*.md`, its own fixture `.md`, or `run.sh`. `RATIONALE.md` is deliberately outside the key.

### ⛔ BLOCKING FINDING — `--only` writes no cache (`run.sh:2918`)

```sh
if [ "$CACHE_ENABLED" -eq 1 ] && [ "$fails" -eq 0 ] && [ -z "$ONLY" ]; then   # ← -z "$ONLY"
```

A partial run **never mints a `.green`**, by design: "a cache entry may only ever be minted by a run that
proved the whole suite green." The strategy's economics assumed the opposite.

- Ten batches under `--only` = 126 fresh dispatches ≈ **$70**, and leave the cache empty.
- The final full pass then re-dispatches **all 126 again** ≈ **another $70**.
- Batching as written costs **~2×** a single full run, not 1×.

Scenarios compound it mildly: `cache_get` is gated on `kind = fixture` (`run.sh:746`), so the 7 scenarios
dispatch fresh in **every** run regardless.

What batching still buys, at that price: a bounded sitting (~$7, ~4 min), the batch-1 stop-gate on the
never-run assertions, and a written record per batch. What it does not buy is a cheaper total.

**The three live options — a human decision, not the harness's:**

1. **Single full run** (`bash tests/eval/run.sh --workers 8`), ~$70 / ~40 min, one green, cache populated.
   Cheapest correct path.
2. **Batch 1 only as a probe** (~$7), then decide. Answers every unknown; the 116 remaining jobs then run
   as one pass. Total ≈ $77 — a 10% premium for de-risking the stop-gate.
3. **Ten batches as written**, ≈ $140. Buys calendar flexibility, nothing else.

Making batching pay would mean minting per-fixture cache entries under `--only` — the exact false-green
guard that comment defends, and a loosened gate under `CLAUDE.md`. `prof_assert` already records
pass/fail per fixture, so it is *mechanically* possible; it is not taken here, and would need its own
version, its own non-vacuity proof, and a human ratifying the trade.

### Batch 1 — the verified selector

```sh
bash tests/eval/run.sh --workers 8 --only '^(autorun-challenger-default-on|autorun-no-challenger-disclosed|epic-scaffold-committed|evidence-provenance-unknown|evidence-stale-tree-refused|greenfield-no-corpus-clean|greenfield-promote-zeros|no-reviewer-challenger-runs|promote-offers-retirement|stale-source-change)$'
```

Anchored `^(…)$` alternation, not a substring pattern — the `--only 'greenfield'` 3-of-4 trap cannot
recur. What each of the ten is there to answer:

| Fixture | Why in batch 1 |
|---|---|
| `autorun-challenger-default-on` | Class-A `--no-challenger` — unpassable since 1.14.0, never once run |
| `evidence-stale-tree-refused` | Class-A `--tree` + Class-B `RE_DOES_NOT_ESTABLISH` |
| `evidence-provenance-unknown` | Class-A `--tree` |
| `no-reviewer-challenger-runs` | Class-A `--no-reviewer` |
| `epic-scaffold-committed` | Class-B `RE_BEFORE_CHILD` — second flap, widened |
| `stale-source-change` | Class-B continuous-form refusal |
| `promote-offers-retirement` | Class-B rationale token — widened three times, 1.14.1 + 1.14.2 |
| `greenfield-promote-zeros` | the per-job `reset_sandbox` fix, proven at harness level only |
| `autorun-no-challenger-disclosed` | the other half of the seat split |
| `greenfield-no-corpus-clean` | 1.14.0 anti-tax control, never re-run since |

---

## Status

| # | Batch | Jobs | Status | Date | fp ok | Pass/Fail | Wall | Fresh/Cached | Tokens | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | The unknowns | 10 | ✅ green | 2026-09-01 | ✅ | 111 / 0 | 5m01s | 10 / 0 | unmeasured | **stop-gate CLEARED** — the four Class-A assertions passed on a real transcript for the first time |
| 2 | `refine` | 21 | ✅ green | 2026-09-01 | ✅ | 145 / 0 | 11m30s | 21 / 0 | unmeasured | 21, not the ~12 estimated — every refine-mapped fixture |
| 3 | `analysis` | 13 | ✅ green | 2026-09-01 | ✅ | 102 / 0 | 6m07s | 13 / 0 | unmeasured | anchors load-bearing — unanchored `full` also matches `greenfield-full-run` |
| 4 | `design` | 17 | 🔴 red (environment) | 2026-09-01 | ✅ | 96 / 22 | 6m48s | 17 / 0 | unmeasured | 7 fixtures hit `API Error: 529`; the other 10 green. **No behavioural finding.** |
| 4↻ | `design` — re-run | 17 | ✅ green | 2026-09-01 | ✅ | 118 / 0 | 6m01s | 17 / 0 | unmeasured | all 17 dispatched for real; `API Error` sweep clean |
| 5 | `execute` | 4 | ✅ green | 2026-09-01 | ✅ | 66 / 0 | 4m40s | 4 / 0 | unmeasured | only 4 new — `per-clause` and `evidence-stale-tree-refused` came with batches 4 and 1 |
| 6 | `review` + `challenger` | 11 | ✅ green | 2026-09-01 | ✅ | 90 / 0 | 4m11s | 11 / 0 | unmeasured | 6 of the 17 review-mapped fixtures were already paid for by batches 1, 4 and 5 |
| 7 | `finalise` + learning loop | 21 | ✅ green | 2026-09-01 | ✅ | 142 / 0 | 4m53s | 21 / 0 | unmeasured | includes the `solve` cost-ledger fixtures; run survived a repo path rename |
| 8 | `autorun` + contract + reconcile | 7 | ✅ green | 2026-09-01 | ✅ | 104 / 0 | 15m13s | 7 / 0 | unmeasured | slowest batch — autorun is the heaviest scheduler weight |
| 9 | `promote` + `codify` + `breakdown` | 8 | ✅ green | 2026-09-01 | ✅ | 86 / 0 | 5m54s | 8 / 0 | unmeasured | cross-ticket paths; 5 of the 13 mapped were already paid for |
| 10a | supporting skills (7 fixtures) | 7 | ✅ green | 2026-09-02 | ✅ | 87 / 0 | 3m15s | 7 / 0 | unmeasured | run in the FOREGROUND after the background task was stopped by the host |
| 10b | all 7 scenarios | 7 | ✅ green | 2026-09-02 | ✅ | 65 / 0 | 0m40s | n/a | unmeasured | first time any scenario ran this cycle; scenarios are never cacheable |
| — | **Final pass** (whole suite, expect all cached) | 126 | ⬜ not run | | | | | | | proves green *together*, not in ten fragments |

**Status values:** ⬜ not run · 🟡 running · ✅ green · 🔴 red · ⚠️ void (fingerprint changed)

**Tokens:** record what the host actually reports. If it reports nothing, write `unmeasured` — never an
estimate dressed as a measurement. Dispatch totals are the one figure the ledger does give.

---

## Running total

```
Batches green      : 10 / 10 — every batch green.
Fixtures proven    : 119 / 119.  Scenarios proven: 7 / 7.
Jobs proven green  : 126 / 126  — every job in the suite has run and been judged this cycle.
Dispatches spent   : 143  (10+21+13+17 red+17 re-run+4+11+21+7+8+7+7) — 17 paid twice to a 529,
                     and batch 10's first attempt was stopped by the host before judging anything.
Assertions         : the suite holds 566 assertions (any partial run prints passed + skipped = 566).
                     All 566 have been judged at least once across the ten batches, 0 failures.
                     The "1116" figure is a SUM OVER RUNS, not distinct coverage: the ~55
                     dispatch-free self-tests are re-judged in every batch, and batch 4's 17
                     fixtures were judged twice. Do not quote it as an assertion count.
Tokens spent       : unmeasured (the host reports none)
Run still valid    : yes — fingerprint e23452eb…1da28 unchanged from pre-flight through batch 10,
                     across a repo path rename and a host-stopped task.
NOT YET DONE       : the final whole-suite pass. Ten green batches are ten fragments; the suite has
                     not been proven green TOGETHER, and no cache was ever written.
```

### Is the full eval green? NO — and the harness says so itself

Ten green batches are **not** a green suite, for four reasons that are mechanical rather than cautious:

1. **`run.sh` refuses the claim.** Every batch printed `NOT a milestone run`, and the cache write is
   gated on `-z "$ONLY"` (`run.sh:2918`) precisely because under `--only` a `fails -eq 0` means "the
   selected fixtures passed", never "the suite is green".
2. **A partial run cannot detect a lost job.** Under `--only` a missing transcript is counted
   **skipped**; with no `--only` it **FAILS loudly** (`assert_judgeable`). Deferred defect 5 — the
   dispatch loop leaking stdin — is a live mechanism for losing a job. Ten partial greens is exactly
   the shape a false-green would take here.
3. **Nothing has been proven green TOGETHER.** No run has held all 126 jobs in one worker pool. Batch
   4's 529 is the standing proof that environment effects appear at scale and not in a small slice.
4. **No cache exists.** There is no artifact anywhere recording a green suite — the whole reason this
   log was written.

**What the ten batches DO establish, and it is not nothing:** every one of the 126 jobs has been
dispatched and judged at least once at this fingerprint, all 566 assertions have been judged, and
nothing failed for a behavioural reason. Every red in this cycle was the host or the harness — a 529,
and a stopped background task — never mango.

**The honest statement is therefore: 126/126 jobs judged green in ten partial runs at
`e23452eb…1da28`; the suite has NOT been run whole.** That is the sentence that may go in a CHANGELOG
or README. "The suite is green" may not.

---

## Per-batch record

Copy this block for each batch. One per batch, in order.

### Batch __ — <name>

```
Date            : 
fingerprint     :            matches header : yes / NO → RUN IS VOID
git status      : clean / dirty
Selector used   :            ← the exact --only argument or fixture list
Fixtures matched: n          ← VERIFY before dispatching; a pattern once matched 3 of 4
Jobs run        : n
Result          : n pass / n fail
Wall clock      : 
Fresh / cached  : n / n
Tokens          :            ← or `unmeasured`
```

**Failures** — one line each: fixture, what was missing, and the class:

| Fixture | What failed | Class |
|---|---|---|
| | | assertion wording / skill gap / environment |

**Class decides the cost of the fix:**

- **assertion wording** → touches `run.sh` → **the whole run is void.** Record it, finish the remaining
  batches anyway, then fix every wording issue in one edit before a single clean re-run.
- **skill gap** → touches a `SKILL.md` → only the fixtures mapping to that skill invalidate. Cheap.
- **environment** → fix it, and mark every earlier batch as suspect.

**Decision after this batch:** continue / stop / restart — and why.

---

## Batch 1 — the unknowns (stop-gate)

```
Date            : 2026-09-01
fingerprint     : e23452eb45532e966e6f0a89290b8573fc5b179100c99ec1716796f727d1da28
                  matches header : yes
git status      : clean
HEAD SHA        : ccc7e63
Selector used   : ^(autorun-challenger-default-on|autorun-no-challenger-disclosed|epic-scaffold-committed
                  |evidence-provenance-unknown|evidence-stale-tree-refused|greenfield-no-corpus-clean
                  |greenfield-promote-zeros|no-reviewer-challenger-runs|promote-offers-retirement
                  |stale-source-change)$
Fixtures matched: 10  — verified dispatch-free BEFORE dispatching, against the full 126-job list
Jobs run        : 10
Result          : 111 pass / 0 fail   (455 assertions skipped — PARTIAL, no cache written)
Wall clock      : 294s dispatch / 301s total, 8 workers
Fresh / cached  : 10 / 0
Tokens          : unmeasured
```

**Failures:** none.

**What this batch settled — the reason it went first:**

| Question | Answer |
|---|---|
| Do the four Class-A option-shaped assertions pass now that `--` reaches `grep`? | **Yes, all four**, on a real transcript for the first time since they shipped in 1.14.0 |
| Do the four Class-B widenings hold on a fresh run? | **Yes** — `epic-scaffold-committed` 2/2, `stale-source-change` 3/3, `evidence-stale` question-answered negative, `promote-offers-retirement` 10/10 |
| Is the thrice-widened promote/retire rationale token stable? | **Yes**, and the ORDER assertion added beside it in 1.14.1 passed again — 7/7 lifetime, still no miss |
| Is the per-job `reset_sandbox` fix real, or proven at harness level only? | **Real.** `greenfield-promote-zeros` 6/6, with `job-isolation-guard` reporting all 10 jobs started from the provisioned baseline and both non-vacuity proofs green |

All 8 worker clones disposed; the live checkout was untouched (HEAD on `main`, no stray branch, no work
doc), and the eval-isolation guard's injected-leak control fired as it should.

**Decision after this batch: continue — but not as ten batches.** The stop-gate is clear, so nothing
remaining is unknown enough to justify paying twice. Per the pre-flight finding, the rest is one full
126-job pass, which is also the only run that can mint the cache.

---

## Batch 2 — `refine` (phase 0)

```
Date            : 2026-09-01
fingerprint     : e23452eb45532e966e6f0a89290b8573fc5b179100c99ec1716796f727d1da28
                  matches header : yes
git status      : clean
HEAD SHA        : 12a10b1
Selector used   : ^(check-lines-one-grammar|claim-retired-promoted|epic-exposure-checker|greenfield-full-run
                  |premise-falsified|premise-to-be-created|recall-area-type5|recall-retired-skipped
                  |recall-symbol-type1|recall-type2-handle|recall-type6-expiry|recall-zero-no-busywork
                  |refine-acceptance-bar-is-want|refine-assumed-on-handback|refine-backstop-challenger
                  |refine-classify-A-vs-B|refine-consistency-is-how|refine-direction-not-tool
                  |refine-epic-detect-breakdown|refine-skip-clear-ticket|refine-want-unattended-stops)$
Fixtures matched: 21 — verified dispatch-free BEFORE dispatching, against the full 126-job list
Jobs run        : 21
Result          : 145 pass / 0 fail   (421 assertions skipped — PARTIAL, no cache written)
Wall clock      : 683s dispatch / 690s total, 8 workers
Fresh / cached  : 21 / 0
Tokens          : unmeasured
```

**Failures:** none.

**Scope note — 21 jobs, not the ~12 the strategy estimated.** The batch is defined as every fixture
mapping to `refine` in `FIXTURE_SKILLS`, derived from the map rather than from a name prefix: the eight
`refine-*` fixtures, the six `recall-*` ones, both `premise-*`, `epic-exposure-checker`,
`claim-retired-promoted`, `check-lines-one-grammar`, `greenfield-full-run`, and
`refine-epic-detect-breakdown`. `epic-scaffold-committed` also maps to `refine` and was excluded — batch
1 already ran it, and a partial run caches nothing, so re-running it would have bought nothing.

Every one of the 21 had assertions attributed to its transcript — no fixture was dispatched without
being judged. All 8 worker clones disposed, all 21 jobs started from the provisioned baseline, live
checkout untouched.

**Decision after this batch: continue.**

---

## Batch 3 — `analysis` (Gate 1)

```
Date            : 2026-09-01
fingerprint     : e23452eb45532e966e6f0a89290b8573fc5b179100c99ec1716796f727d1da28
                  matches header : yes
git status      : clean
HEAD SHA        : 3c6a5e8
Selector used   : ^(analysis-section-coverage|freeform|full|greenfield-recall-handles-none-match|lite
                  |multi-clause-want|red-baseline|rule-section-by-handle|rule-section-handle-na-closes
                  |rule-section-handle-unanswered|rule-section-provisional-no-block
                  |uncodified-standard-nudge|vague-requirement)$
Fixtures matched: 13 — verified dispatch-free BEFORE dispatching, against the full 126-job list
Jobs run        : 13
Result          : 102 pass / 0 fail   (464 assertions skipped — PARTIAL, no cache written)
Wall clock      : 360s dispatch / 367s total, 8 workers
Fresh / cached  : 13 / 0
Tokens          : unmeasured
```

**Failures:** none.

**The anchors earned their keep here.** Three of these fixtures are named `full`, `lite` and `freeform` —
bare words. Unanchored, `full` also matches `greenfield-full-run` (already run in batch 2), so the
`^(…)$` form is what keeps the batches non-overlapping rather than merely approximately so.
`greenfield-full-run` maps to `refine analysis` and was counted under batch 2.

`red-baseline` carries a per-job `test_command` override, and both `harness-parameterisation` self-tests
passed alongside it — the green default and the per-job override each land in `test_command`, so a
deliberately red baseline was judged against the command it is supposed to run.

All 13 had assertions attributed to their transcript. All 8 worker clones disposed, all 13 jobs started
from the provisioned baseline, live checkout untouched.

**Decision after this batch: continue.**

---

## Batch 4 — `design` (Gate 2) — 🔴 RED on environment

```
Date            : 2026-09-01
fingerprint     : e23452eb45532e966e6f0a89290b8573fc5b179100c99ec1716796f727d1da28
                  matches header : yes
git status      : clean
HEAD SHA        : 9bccc9f
Fixtures matched: 17 — verified dispatch-free BEFORE dispatching
Jobs run        : 17
Result          : 96 pass / 22 fail   (448 assertions skipped — PARTIAL, no cache written)
Wall clock      : 401s dispatch / 408s total, 8 workers
Fresh / cached  : 17 / 0
Tokens          : unmeasured
```

**Every one of the 22 failures has a single cause: `API Error: 529 Overloaded`.** Seven fixtures never
ran; their transcripts contain the harness header, the host's permission warnings, and the 529 line.
Nothing about mango's behaviour is implicated, and no assertion wording is at fault.

| Fixture | pass / fail | Cause | Class |
|---|---|---|---|
| `provenance-authored-blocks` | 0 / 5 | API Error 529 | environment |
| `provenance-na-costs-nothing` | 0 / 4 | API Error 529 | environment |
| `frontend-layer` | 0 / 3 | API Error 529 | environment |
| `surface-denominator` | 0 / 2 | API Error 529 | environment |
| `exclusion-recurrence-escalates` | 1 / 4 | API Error 529 | environment |
| `handle-unanswered-blocks` | 1 / 3 | API Error 529 | environment |
| `blast-radius` | 1 / 1 | API Error 529 | environment |

The other **ten dispatched cleanly and were green**: `design-layer`, `design-blastradius-shared-type`,
`design-blastradius-value-threading`, `check-lines-missing-blocks`, `exclusion-expiry-checkable`,
`exclusion-expiry-required`, `handle-does-not-apply-closes`, `ondemand-companion-read`, `per-clause`,
`provenance-real-corpus-passes`. So `design` is **10 of 17 proven**, 7 unproven pending a re-run.

### The finding that matters — three assertions PASSED on a transcript that never ran

`blast-radius`, `handle-unanswered-blocks` and `exclusion-recurrence-escalates` each recorded a **PASS**
against a transcript whose entire content is a 529. Three distinct mechanisms:

| run.sh | Assertion | Why it passed on nothing |
|---|---|---|
| 1056 | `blast-radius: folds it in as collateral` | needs `/blast[ -]radius|collateral/` — the harness's own header line is `== fixture: blast-radius ==`. **The regex matched the fixture's name.** |
| 1854 | `unanswered: the unanswered handle is named as the cause` | needs `/handle/` AND `/unanswered/` — both present in `== fixture: handle-unanswered-blocks ==` |
| 2182 | `recurrence: mango does not auto-discharge the overdue class` | `assert_absent` — a transcript with no run contains nothing, so nothing is present to fail it |

`assert_judgeable` asks only whether the transcript is **non-empty**. A 529 produces a file that exists
and is non-empty yet contains no run — a third state the harness does not model. mango itself added
exactly this state in 1.14.0 for test evidence (`provenance-unknown`, "never a pass"); its own eval
harness has no equivalent for a dispatch that did not happen.

### Vacuity audit — 510 assertions, dispatch-free, `run.sh` untouched

Each assertion's regexes were tested against a synthetic no-run transcript (the real observed 529 body,
with the header rewritten per fixture). 510 audited, 1 unparsed (`run.sh:1545`, an interpolated
`$RE_INVEST_SMALL|…`).

**Exactly one job would go FULLY GREEN on a transcript that never ran:**

- **`ledger-gate-complete`** (`run.sh:1290`) — its single assertion looks for
  `/proceed|passes|not block|does not block|complete/`, and its own name contains **complete**. This
  assertion **cannot fail**, on any transcript, ever. A scenario, so it has no fixture file. It was in
  none of batches 1–4 and has not run this cycle.

**53 further jobs have SOME vacuous assertion** (1 of n), so a 529 there still shows red — which is why
batch 4's 529s were caught rather than passing silently. Worst ratios: `autorun-challenger-default-on`
3/6, `autorun-clarification-stops` 3/6, `promote-offers-retirement` 3/10, `greenfield-check-lines-clean`
2/4, `check-lines-one-grammar` 2/6, `premise-to-be-created` 2/4, `loop-project-local` 2/6,
`rule-section-provisional-no-block` 2/5.

**Batches 1–3 are therefore VALIDATED, not suspect.** All 44 of their fixtures have at least one
assertion that a no-run transcript would visibly fail, and all three batches reported zero failures — so
no fixture in them silently 529'd. The usual "environment fault ⇒ earlier batches are suspect" rule is
discharged here by measurement rather than by assumption.

### Deferred — every fix touches `run.sh` and would void the run

Recorded, not applied, per the freeze:

1. **A no-run transcript must never be judged.** Detect `API Error: <code>` (and an empty model reply)
   and report the job as `dispatch-failed` on its own status — never a pass, never a wording failure.
   The vocabulary already exists in mango's own `provenance-unknown`.
2. **`ledger-gate-complete` (`run.sh:1290`) is unfalsifiable** and must be re-written so its regex cannot
   match its own name. This is the one true false-green in the suite.
3. **The header should not be greppable.** `== fixture: <name> ==` is inside the file the assertions
   grep, which is what makes a fixture's own name a matchable token. Writing it to a sidecar, or
   stripping it before the assert pass, removes ~54 partial vacuities at the root rather than one at a
   time.
4. Optionally, retry a 529 once before recording the job — a transient host fault is not a result.

**Decision after this batch: continue.** The batch is red on the host, not on mango; the seven 529'd
fixtures need a re-run, and the three harness defects wait for a version of their own after the freeze
lifts.

---

## Batch 4 ↻ — `design` re-run — ✅ GREEN

```
Date            : 2026-09-01
fingerprint     : e23452eb45532e966e6f0a89290b8573fc5b179100c99ec1716796f727d1da28
                  matches header : yes
git status      : clean
HEAD SHA        : 0706425
Selector used   : unchanged from batch 4 — re-verified 17/17 before dispatching
Jobs run        : 17   (the full batch, not only the seven that 529'd)
Result          : 118 pass / 0 fail   (448 assertions skipped — PARTIAL, no cache written)
Wall clock      : 353s dispatch / 361s total, 8 workers
Fresh / cached  : 17 / 0
Tokens          : unmeasured
```

**Failures:** none. `design` is now 17 of 17 proven.

**The whole batch was re-run, not just the seven.** A partial run caches nothing, so re-running the ten
that had already passed cost ten dispatches — paid deliberately, to get one green batch rather than a
result stitched from two runs, and to give the ten a second fresh transcript.

**Every pass in this batch was checked against the defect batch 4 exposed.** Before reading the result:

| Check | Result |
|---|---|
| `API Error` in any of the 17 transcripts | **none** |
| Transcript size | 7.2 KB – 17.8 KB (the 529'd ones were 5.1 KB of host noise) |
| Real mango artifacts present (`Gate 2` / `HANDLES:` / `EXCLUSIONS:` / verification plan) | **17 / 17** |
| Assertions attributed per fixture | 2–5 each, 61 fixture-level passes in total |
| Jobs starting from the provisioned baseline | 17 / 17 |

The three assertions that passed vacuously in the red run — `blast-radius: folds it in as collateral`,
`unanswered: the unanswered handle is named as the cause`, `recurrence: mango does not auto-discharge`
— all passed here on transcripts that contain a genuine run, so they are **now earned rather than
vacuous**. That does not repair them: they would pass again on a no-run, and the fix is still item 1 and
item 3 of the deferred list.

**Decision after this batch: continue to batch 5 (`execute`).** The four deferred `run.sh` fixes stand
unapplied; the freeze holds.

---

## Batch 5 — `execute` (phase 3)

```
Date            : 2026-09-01
fingerprint     : e23452eb45532e966e6f0a89290b8573fc5b179100c99ec1716796f727d1da28
                  matches header : yes
git status      : clean
HEAD SHA        : 699f0c0
Selector used   : ^(behavioural-drift|execute-commit-before-review|format-scope|no-runner-proof)$
Fixtures matched: 4 — verified dispatch-free BEFORE dispatching
Jobs run        : 4    (4 workers — one per job)
Result          : 66 pass / 0 fail   (500 assertions skipped — PARTIAL, no cache written)
Wall clock      : 273s dispatch / 280s total
Fresh / cached  : 4 / 0
Tokens          : unmeasured
```

**Failures:** none.

**Only four jobs, and that is correct.** `execute` maps six fixtures, but `per-clause` (design execute)
ran in batch 4 and `evidence-stale-tree-refused` (review execute) ran in batch 1. Deriving from
`FIXTURE_SKILLS` rather than from the strategy's ~12 estimate is what keeps a fixture from being paid
for twice — the opposite error to the one that cost 17 dispatches on the 529.

**No-run check applied, as it now is to every batch:** no `API Error` in any of the four transcripts,
sizes 6.6–8.1 KB, and all four carry real execute artifacts (change list, proving test, verification
sweep, branch/commit).

**These are the fixtures that branch and commit, so isolation was checked directly, not just asserted.**
The live checkout after dispatch: HEAD on `main` at `699f0c0`, `git status` clean, no stray `PROJ-*`
branch, all 4 worker clones disposed, all 4 jobs started from the provisioned baseline — and both
non-vacuity controls (injected leak, undisposed tree) fired as they should.

**Decision after this batch: continue to batch 6 (`review` + `challenger`).**

---

## Batch 6 — `review` + `challenger` (phase 4, the two critics)

```
Date            : 2026-09-01
fingerprint     : e23452eb45532e966e6f0a89290b8573fc5b179100c99ec1716796f727d1da28
                  matches header : yes
git status      : clean
HEAD SHA        : 9752102
Selector used   : ^(caveman-critic-guard|challenger-pr-body-refused|challenger-unmet|conditional-LGTM
                  |ondemand-read-no-plugin-root|review-git-isolation|rubric-hover
                  |verify-only-bookkeeping-carveout|verify-only-main-loop|verify-only-scoped
                  |worktree-env-fault)$
Fixtures matched: 11 — verified dispatch-free BEFORE dispatching
Jobs run        : 11
Result          : 90 pass / 0 fail   (476 assertions skipped — PARTIAL, no cache written)
Wall clock      : 244s dispatch / 251s total, 8 workers
Fresh / cached  : 11 / 0
Tokens          : unmeasured
```

**Failures:** none.

`review` maps 17 fixtures; 6 of them — the two `evidence-*`, `no-reviewer-challenger-runs`, both
`autorun-*challenger*`, and `execute-commit-before-review` — were already proven by batches 1, 4 and 5,
so 11 dispatches covered the phase. The anchors matter again here: unanchored, `verify-only` alone would
have collapsed three distinct fixtures into one pattern.

**No-run check:** no `API Error` in any of the 11 transcripts; sizes 6.3–12.5 KB; all 11 carry real
review artifacts (a verdict — `BLOCK` / `CHANGES REQUESTED` / `LGTM` — or a named finding).

**Isolation:** `review-git-isolation` and `worktree-env-fault` exercise git state directly. After
dispatch the live checkout is on `main` at `9752102`, clean, with no stray branch; all 7 isolation
assertions passed, including the three non-vacuity controls.

**Decision after this batch: continue to batch 7 (`finalise` + the learning loop).**

---

## Batch 7 — `finalise` + the learning loop + the cost ledger

```
Date            : 2026-09-01
fingerprint     : e23452eb45532e966e6f0a89290b8573fc5b179100c99ec1716796f727d1da28
                  matches header : yes
git status      : clean
HEAD SHA        : 574d208
Repo path       : /home/cuong-ngo/WORKSPACE/PROJECTS/mango-plugins   ← renamed mid-run, see below
Fixtures matched: 21 — verified dispatch-free BEFORE dispatching
Jobs run        : 21
Result          : 142 pass / 0 fail   (424 assertions skipped — PARTIAL, no cache written)
Wall clock      : 285s dispatch / 293s total, 8 workers
Fresh / cached  : 21 / 0
Tokens          : unmeasured
```

**Failures:** none. Covers both the `finalise`-mapped fixtures and the four `solve`-mapped cost-ledger
ones (`ledger-auto-append`, `ledger-label`, `usage-unmeasured-marker`, `workdoc-solve-autopath`); only
`stale-source-change` was already paid for, in batch 1.

**The anchors were load-bearing in an unusually sharp way.** Four job names are prefixes of others:
`ledger-gate` / `ledger-gate-complete`, and `ledger-content-gate` / `ledger-content-gate-marker`. In
both pairs the longer name is a **scenario**, with no `FIXTURE_SKILLS` entry, so an unanchored selector
would have dispatched two scenarios this batch had no business running — one of which,
`ledger-gate-complete`, is the single unfalsifiable assertion the vacuity audit found. It remains unrun.

**No-run check:** no `API Error` in any of the 21 transcripts, and all 21 carry real artifacts (a
ledger, a `CLAIMS:` line, a lesson record, a counted gate). Transcripts here run 1.7–7.6 KB — smaller
than the 5.1 KB the 529'd jobs produced, because those 5.1 KB were almost entirely host permission
warnings and these are actual short answers. **Size is not the discriminator; the `API Error` sweep and
the artifact check are.**

87 of the 142 passes are attributed to the 21 fixtures; the other 55 are the dispatch-free self-tests
(assertion-convention, validator guards, the envelope suite, cache, harness parameterisation, isolation).

### The repository was renamed during this batch

Between batch 6 and batch 7 the parent directory changed case — `WORKSPACE/Projects` →
`WORKSPACE/PROJECTS` — and the shell lost its working directory mid-command. Verified before dispatching
anything: clean tree, HEAD `574d208`, all eight batch commits present, batch log intact, and **the
`run.sh` fingerprint unchanged**. The fingerprint is the run's identity, not the path, so **the run
remains valid** and batches 1–6 still stand. `CLAUDE.md` and the session config still name the old path.

**Decision after this batch: continue to batch 8 (`autorun` + contract + reconcile).**

---

## Batch 8 — `autorun` + RUN CONTRACT + RECONCILE

```
Date            : 2026-09-01
fingerprint     : e23452eb45532e966e6f0a89290b8573fc5b179100c99ec1716796f727d1da28
                  matches header : yes
git status      : clean
HEAD SHA        : 1f4ae27
Selector used   : ^(autorun-budget-degrades|autorun-clarification-stops|autorun-gate-grammar-mismatch
                  |check-lines-contradiction-blocks|check-lines-not-checkable|greenfield-autorun-clean
                  |greenfield-check-lines-clean)$
Fixtures matched: 7 — verified dispatch-free BEFORE dispatching
Jobs run        : 7    (7 workers — one per job)
Result          : 104 pass / 0 fail   (462 assertions skipped — PARTIAL, no cache written)
Wall clock      : 906s dispatch / 913s total
Fresh / cached  : 7 / 0
Tokens          : unmeasured
```

**Failures:** none. Six of the 13 `autorun`-mapped fixtures were already proven by batches 1, 2, 4 and
6, so 7 dispatches closed the phase.

**The slowest batch of the run — 15m13s for 7 jobs, against 4m53s for 21 in batch 7.** That is the
expected shape, not an anomaly: `SKILL_WEIGHT` gives `autorun` the top weight of 4, and these fixtures
drive a whole unattended lifecycle. `greenfield-autorun-clean` alone produced a 14.4 KB transcript
carrying 11 assertions, and `autorun-budget-degrades` 11.8 KB carrying 10.

**No-run check:** no `API Error` in any of the 7 transcripts; all 7 carry real envelope artifacts (a
`RUN CONTRACT`, a `RECONCILE`, a `DISCLOSURE` line, or a counted `CHECK`/`GATES:` line).

**The envelope itself was already covered, dispatch-free, in every batch of this run.** The RUN CONTRACT
/ RECONCILE / BUDGET scripts are script-enforced: the envelope suite's **128 tests** ran green as part
of batches 1–8 alike, so the strategy's expectation that batch 8 would be low-surprise held for the
reason it predicted — the envelope's guarantees do not depend on a dispatch.

**Decision after this batch: continue to batch 9 (`promote` + `codify` + `breakdown`).**

---

## Batch 9 — `promote` + `codify` + `breakdown` (the cross-ticket paths)

```
Date            : 2026-09-01
fingerprint     : e23452eb45532e966e6f0a89290b8573fc5b179100c99ec1716796f727d1da28
                  matches header : yes
git status      : clean
HEAD SHA        : d970788
Selector used   : ^(breakdown-invest-enumerated|breakdown-reratify|codify-drift-count
                  |epic-lesson-capture|invest-force-resplit|promote-idempotent
                  |promote-single-lesson-noop|promote-two-lessons-one-rule)$
Fixtures matched: 8 — verified dispatch-free BEFORE dispatching
Jobs run        : 8
Result          : 86 pass / 0 fail   (480 assertions skipped — PARTIAL, no cache written)
Wall clock      : 347s dispatch / 354s total, 8 workers
Fresh / cached  : 8 / 0
Tokens          : unmeasured
```

**Failures:** none. Five of the 13 fixtures mapping to `promote`, `codify` or `breakdown` were already
proven — `epic-scaffold-committed` and `promote-offers-retirement` in batch 1,
`greenfield-promote-zeros` in batch 1, `refine-epic-detect-breakdown` in batch 2 and
`promotion-rulebook-wiring` in batch 7 — so 8 dispatches closed all three skills.

**No-run check:** no `API Error` in any of the 8 transcripts; sizes 2.2–4.8 KB, each with assertions
attributed (3–6 per fixture).

**The remaining work is now exactly determined.** 112 jobs proven, and batch 10 holds the last 14: the
7 supporting-skill fixtures (`budget-rtk-wire-guidance`, `optimizer-adoption-gated`, `rtk-degrade`,
`greenfield-quick-direct`, `quick-direct-recall`, `host-context-file-default`, `host-context-file-agents`)
plus **all 7 scenarios**, none of which has run this cycle. 112 + 14 = 126.

Two mapped skills still have no behavioural fixture at all — `db-map` and `version-check` — unchanged
since 1.14.1 and to be carried into the closing entry, not into batch 10.

**Decision after this batch: continue to batch 10 — the last one.**

---

## Batch 10 — supporting skills + every scenario — ✅ GREEN (two foreground halves)

```
Date            : 2026-09-02
fingerprint     : e23452eb45532e966e6f0a89290b8573fc5b179100c99ec1716796f727d1da28
                  matches header : yes
git status      : clean
HEAD SHA        : 058827e
Half A (7 fixtures)  : 87 pass / 0 fail — 188s dispatch / 195s total, 7 workers
Half B (7 scenarios) : 65 pass / 0 fail —  33s dispatch /  40s total, 7 workers
Fixtures matched: 7 + 7 — each half verified dispatch-free BEFORE dispatching
Fresh / cached  : 7 / 0 for half A; half B reports 0/0 because scenarios are not tallied as
                  fixtures and can never cache-hit (cache_get is gated on kind = fixture)
Tokens          : unmeasured
```

**Failures:** none. Half A covered `budget` ×3, `quick` ×2 and `init`/`doctor` ×2. Half B covered
**all seven scenarios — the first time any scenario has run this cycle.** Every one of the 14 intended
jobs had assertions attributed to its transcript, and no `API Error` appeared in either half.

**Why two foreground halves.** The first attempt at batch 10 ran as a background task and was **stopped
by the host 3.5s after launch, 1.5s after the turn ended**, having judged **zero** assertions. Ruled out
on evidence: not a crash (the notification said `was stopped`, uniquely among 11 launches), not
resources (626 GB disk / 18 GB RAM free, no kernel OOM), not the `rtk` PreToolUse rewrite (identical on
all 11 launches, ten survived), not `run.sh` (its `trap cleanup EXIT` ran, `TMPROOT` removed, no orphan
processes or clones), and not another session (the two other CLI instances were in different projects).
The residual cause is host-side on the Stop/interrupt path. Splitting into two foreground halves, each
well under the tool timeout, avoids that path entirely and costs nothing — no batch writes cache anyway.

**`ledger-gate-complete` ran, and its pass is still not evidence.** The scenario produced a real
1113-byte answer, so the pass is earned on *this* transcript. The assertion remains unfalsifiable: its
regex `proceed|passes|not block|does not block|complete` matches the string `ledger-gate-complete` in
the harness's own header line. Deferred fix item 2 stands unchanged.

### NEW FINDING — the dispatch loop leaks its stdin into the model's prompt

`ledger-gate-complete`'s transcript ends with the model saying *"the trailing `1 2 3 4 5 6 7` in your
message didn't parse as part of the question"*. There were exactly 7 jobs in that half, and the
scheduler's job list is the integers 1..7.

`claude_run` runs `( cd "$repo" && claude -p … "$@" )` with **no stdin redirection**, and it is called
from inside `while read -r idx; do … done <"$JOBS_DIR/schedule"` (`run.sh:780-791`). The child inherits
the loop's stdin — the schedule file — and reads it, so the remaining job indices arrive appended to the
prompt. Two consequences:

1. **Prompt pollution.** A dispatched job can be judged on a transcript whose prompt was not the prompt
   the fixture wrote. Here it only cost some wasted output; it could as easily change a decision.
2. **A silent-skip path, worse than the pollution.** A worker whose child consumed its schedule sees
   EOF and stops claiming. With fewer workers than jobs, a registered job can go undispatched — and
   under `--only`, a missing transcript is counted **skipped**, never failed (`assert_judgeable`). A
   full run fails loudly on a missing transcript; **every partial run in this cycle would have gone
   quietly green.**

**It did not bite this cycle, and that is checked rather than assumed:** every batch's intended fixtures
were confirmed to have assertions attributed to their transcripts, batch by batch, so no job was lost.

Deferred like the rest — the fix is one redirection (`< /dev/null`, or a distinct fd for the loop) and
it touches `run.sh`:

5. **`claude_run` must not inherit the dispatch loop's stdin.** Redirect the child's stdin from
   `/dev/null` and/or read the schedule on a dedicated descriptor, so no job list can ever reach a
   model's prompt and no worker can lose its queue to a child.

**Decision after this batch: all ten batches are green. What remains is the final whole-suite pass —
the one thing ten fragments cannot establish.**

---

## Rules that keep this run valid

1. **Never touch `run.sh` between batch 1 and the final pass.** Not a fixture, not a name, not the
   `FIXTURE_SKILLS` map. Every one of those changes the fingerprint and voids the run.
2. **Verify the selector before dispatching.** `--only 'greenfield'` once matched 3 of 4 fixtures and
   reported success.
3. **Batch 1 is a stop-gate.** Red there means the fix touches `run.sh`, which voids everything — so the
   remaining nine batches would be paid for twice.
4. **Commit before every batch.** The harness clones HEAD; an uncommitted change means the batch tested a
   tree that is not the one you edited.
5. **Write the row before starting the next batch**, not at the end of the run.

---

## Closing entry — after the final pass

```
Suite green at SHA : 
Date               : 
Total jobs         : 126
Total tokens       : 
Batches needed     :        ← including any restart
Restarts           :        ← and what caused each

Defects this cycle found in the HARNESS ITSELF:
  - 
  - 

Fixtures that have now run at least once : n / 119
Skills with zero behavioural coverage    :            ← db-map, version-check as of 1.14.1
```

Append the closing entry to `EVAL-PROFILE.md` too. The 1.14.0 CHANGELOG (§D) records that this repo stored
**no eval results at all** — the only one is from v1.7.6. That is why four assertions shipped never having
run, and why a `grep` bug that made four assertions **unpassable** survived undetected.

A result nobody stores is a result nobody has.

---

# v1.15.0 — the batched run is now provable, and three no-run defects are closed

**Date:** 2026-09-02  ·  **Version:** 1.14.2 → 1.15.0

## What the ten batches actually established, and what they did not

The ten green batches recorded above were real: 126/126 jobs judged, every one of the suite's
transcript assertions judged at least once, 0 failures. The arithmetic composes, and this was verified
rather than assumed — the cache stores a **transcript**, never a verdict, so every assertion is
re-judged from text on every run, and a script confirmed **0** assertions read across two transcripts.

What the ten greens were not was a **counted artifact**. They lived in this file, where nothing could
re-check that no job had been missed, that no green had gone stale, or that every batch had used the
same ruler. And *ruler* was the real gap: the per-fixture skills-hash keys everything a fixture reads
from the skill corpus and deliberately nothing else, so `scripts/*.py`, `plugin.json`, the model and
the `claude` CLI could all have changed across the ~21 hours the ten batches spanned with no hash
noticing. Nothing did change (the only commits in that window touched this log; CLI held at 2.1.258),
but **"nothing changed" and "an artifact proves nothing changed" are different claims**, and this repo
exists to keep them apart.

## What shipped

| | |
|---|---|
| `--verify-suite` | No dispatch, no cost. Learns the suite from the assertion **call sites** (126 jobs, 511 transcript assertions — derived, never hardcoded), then holds the coverage ledger against it. Refuses on: a job with no row, a non-green row, a **stale** skills-hash, a row disagreeing on runner-fp / plugin-tree-fp / model / CLI, a row proven against fewer assertions than the suite now holds, or an owning run whose self-tests failed or never ran. All seven refusals **self-tested non-vacuously** against synthetic ledgers. |
| Coverage ledger | `coverage.<runner-fp>.tsv` + `runs.<runner-fp>.tsv`, one row per job per run, append-only, last-row-wins. Carries the job's skills-hash and all four ruler components. |
| Change A | A `--only` batch now **mints its green fixtures' cache entries**, on per-entry evidence instead of the old suite-wide gate. This is the ~2× cost of a batched suite, removed. |
| Change B | A full pass now clears the same coverage gate before printing its result, so the machinery a batched green depends on cannot rot unnoticed. |
| Fix 1 | A transcript carrying `API Error: …` or an empty body is **not judgeable** — every assertion on it fails loudly, `--only` or not. A no-run is never scored, not as a pass and not as a skip. This is the batch-4 defect, closed. |
| Fix 2 | `ledger-gate-complete` rewritten decision-level. Its old single check could not be failed by any answer. Strictly narrowed. |
| Fix 3 | The harness header is stripped before any regex sees the transcript. |
| Fix 5 | Dispatches run with `</dev/null`; they no longer inherit — and can no longer consume — the worker loop's job schedule. |

## Fix 3's blast radius, counted rather than estimated

Method: run the assert pass twice with no dispatch — once over transcripts containing **only** the
harness header, once over transcripts containing neither the header nor anything else. The difference
is exactly what the header was carrying.

```
passes on a header-only body : 57
passes on a no-header body   : 25   ← assert_absent negative controls, passing by design
HEADER-CAUSED assertions     : 32   ← fully unfalsifiable: passed on ANY transcript
distinct jobs affected       : 31
```

**32 of the suite's 511 transcript assertions were unfalsifiable**, not the "one" the earlier static
audit found. The static audit looked for jobs whose *every* assertion was vacuous; it could not see an
individual check escaping through the harness's own text. The 25 `assert_absent` passes are correct
behaviour for a negative control, and are now safe against a no-run for Fix 1's reason instead.

## The documented bar moved — deliberately, and it narrowed

`CONTRIBUTING.md` and `tests/eval/README.md` previously set the bar at one `--no-cache` full pass.
It is now **every job green under one ruler, proven by `--verify-suite`**. That **widens how the bar
can be reached** (batches, or one invocation) and **narrows what counts as reaching it** — a bare full
pass never recorded the runner, plugin tree, model or CLI version behind its own result, so nobody
could check afterwards which ruler it used. `scripts/validate.py` gained **3 new checks per doc (+6,
2051 → 2057)** pinning the new bar; **no check was removed** and the three old ones still pass.

## State at this entry — read this before the next batch

```
Gates green at this HEAD : validate.py 2057/2057 · envelope 128/128 · --verify-suite 16/17
                           (the 17th is the coverage gate, correctly REFUSING: see below)
Suite size               : 126 jobs · 511 transcript assertions · 71 dispatch-free self-tests
                           (was 55; this version adds 16 non-vacuity proofs) = 582 total
Runner fingerprint       : CHANGED by this version
Plugin-tree fingerprint  : CHANGED by this version (plugin.json version bump)
```

**The ten green batches above no longer count, and cannot be made to count.** Editing `run.sh` changes
the runner fingerprint, which is by design the key that invalidates every reused measurement — and the
coverage ledger did not exist while those batches ran, so there is nothing to migrate. This is the
honest price of the fix, and it is the right price: 32 of those assertions were unfalsifiable at the
time they passed, and Fix 1 means seven fixtures that never ran in batch 4 would now have failed loudly
instead of yielding three vacuous passes. **Those ten greens were measured with a broken ruler.**

Proved end-to-end before this entry, at a cost of one dispatch:

```
run 1  --only '^budget-rtk-wire-guidance$'   1 fresh dispatch, 74/74, 1 ledger row, 1 cache entry minted
run 2  --only '^budget-rtk-wire-guidance$'   1 CACHE-HIT, 0 dispatches, 74/74, 80s → 7s
```

Run 1 minting a cache entry is the thing that had never happened before: every `--only` batch in the
ten above minted nothing, which is why the plan cost ~2×.

---

# Re-run cycle — v1.15.0 ruler

Every batch below is measured under one identity, and each records its own coverage rows. The bar is
`--verify-suite`, not the sum of the `EVAL:` lines.

```
Runner fingerprint  : 82580ae5a8272bb39fd5d0f2fce0e17260d01ee4c85e7d4d8df9e7d33334b492
Plugin-tree fp      : 136caac19f92894859da81a6a1439332d6b1aa173474c52ad4a457b5e79aa5f0
Model / CLI         : cli-default / 2.1.258 (Claude Code)
Suite               : 126 jobs · 511 transcript assertions · 71 dispatch-free self-tests
```

## Batch 1 ↻ — the unknowns, re-run under the new ruler — ✅ GREEN

```
Date            : 2026-09-02
git status      : clean
HEAD SHA        : df45512
Selector used   : ^(autorun-challenger-default-on|autorun-no-challenger-disclosed|epic-scaffold-committed
                  |evidence-provenance-unknown|evidence-stale-tree-refused|greenfield-no-corpus-clean
                  |greenfield-promote-zeros|no-reviewer-challenger-runs|promote-offers-retirement
                  |stale-source-change)$
Selector verified: 10 named in the regex · 10 present on disk · 10 matched · 0 named-but-absent ·
                  0 matched-but-unnamed — checked against the 119 fixture basenames, dispatch-free
Fixtures matched: 10
Result          : 127 pass / 0 fail   (455 assertion(s) skipped — PARTIAL)
                  = 56 fixture assertions + 71 self-tests
Wall clock      : 457s dispatch / 465s total, 8 workers
Fresh / cached  : 10 / 0
Coverage        : 10/10 judged green · 10 ledger rows · 10 cache entries minted
Run id          : 20260902T130931Z-354709   (selftests 71, selftest_fails 0)
Tokens          : unmeasured
```

**Failures:** none.

**The fixture assertion count did not move: 56 before Fix 3, 56 after.** Batch 1's earlier `111 pass`
was the same 56 fixture assertions plus the 55 self-tests of the day; this run is those 56 plus 71.
So for these ten fixtures, stripping the harness header from the judged text removed no assertion and
broke none — the checks that could previously have matched the header were also matching real output,
and now only real output. That is the outcome to want, and it was not the outcome to assume: the header
strip is exactly the kind of change that turns a silent pass into a red.

**What this batch now records that its predecessor could not.** Ten coverage rows, each carrying the
runner fingerprint, plugin-tree fingerprint, model and CLI version it was measured under, plus the
assertion count it was proven against — and ten minted cache entries, so these ten fixtures are paid
for once. The run row vouches for the harness itself: `selftests=71, selftest_fails=0`.

Live checkout untouched afterwards (HEAD `df45512` on `main`, clean); all 8 worker clones disposed; all
10 jobs started from the provisioned baseline; every isolation guard's injected-leak control fired.

## Batch 2 ↻ — `refine` (phase 0), re-run under the new ruler — 🟡 20/21

Split into three parts because a single invocation would have exceeded the 600s tool timeout: batch 1
ran 1.55× slower than its predecessor (457s vs 294s), so batch 2's old 690s projected to ~1070s.
**Splitting is now free** — each part mints its own cache entries and writes its own coverage rows, so
no fixture is dispatched twice. The three parts were verified to partition the 21 exactly: union = 21,
zero duplicates, `diff` against the verified selector empty.

```
Date            : 2026-09-02
git status      : clean
HEAD SHA        : a8c58de
Selector verified: 21 named · 21 present on disk · 21 matched · 0 named-but-absent ·
                  0 matched-but-unnamed · 0 overlap with batch 1 · 0 already-green — dispatch-free
Part A (8 fixtures) : 113 pass / 0 fail — 383s dispatch / 392s total · 8/8 green · 8 minted
Part B (7 fixtures) :  99 pass / 0 fail — 298s dispatch / 307s total · 7/7 green · 7 minted
Part C (6 fixtures) :  90 pass / 1 FAIL — 366s dispatch / 374s total · 5/6 green · 5 minted
Fresh / cached  : 21 / 0
Coverage        : 20 of 21 judged green · 20 ledger rows · 20 cache entries minted
Run ids         : 20260902T135446Z-400577 · 20260902T140124Z-407359 · 20260902T140637Z-412885
Tokens          : unmeasured
```

**One failure, and it is the assertion, not the behaviour.**

`refine-consistency-is-how` → *"refine-consistency: NOT asked as a want-decision"*. The run was correct:
H1 was filed, resolved as *"apply to ALL consumers sharing the recipe"*, carried its citation, and was
flagged for ratification at Gate 1 — and the transcript says so in as many words: **"It was **not** put
to the user as an open want — asking it would have laundered a decision refine could make."** The regex
missed it on window width, not on outcome:

```
regex : not .{0,20}(ask|want-decision|open want)
text  : not** put to the user as an open want
                                   └─ "open want" at offset 25 > 20; the ** emphasis eats 2
```

This is a widen-over-emphasis case, which the rule-book permits; it is **not** an outcome change. It is
recorded in the register below rather than fixed here — see the strategy note.

## Strategy — discovery pass, then proof pass

Editing `run.sh` changes `RUNNER_FP`, which wipes every `.green` and starts a fresh ledger. That is the
design working: the fingerprint is the ruler. But it means **fixing an assertion mid-cycle throws away
every green bought so far**, and the loss grows with each batch — fix at batch 2 and lose 30 fixtures,
fix at batch 8 and lose 100.

So this cycle is deliberately **two passes**:

1. **Discovery (this pass).** Run every batch under runner `82580ae5a827` and record each red. Reds
   stay unfixed; `run.sh` is not touched, so no green is invalidated and no batch is paid for twice.
2. **Proof.** Apply every regex fix in **one** edit — one fingerprint change, one wipe — then run the
   full suite once and prove it with `--verify-suite`.

The considered alternative was to split `DISPATCH_FP` (what determines a transcript) from `RUNNER_FP`
(the ledger's ruler), so an assertion-only edit would keep the transcripts and the proof pass would be a
free re-judge. It is ~$50 cheaper and was **rejected on risk**: it means new cache-invalidation
machinery, and the cache is exactly where a false-green would hide. Paying twice for a blunt, obviously
correct ruler is the cheaper mistake.

**A discovery-pass green is not a green.** Every row written in this pass is measured under a ruler that
the proof pass will replace. Nothing here may be cited as evidence the suite passes.

## Register — reds to fix in the single edit

| # | Job | Assertion | Class | Evidence |
|---|-----|-----------|-------|----------|
| R1 | `refine-consistency-is-how` | `refine-consistency: NOT asked as a want-decision` | wording / emphasis window | behaviour correct; `not** put to the user as an open want`, "open want" at offset 25 vs `.{0,20}` |

Each fix must ship with its paired `selftest_assertion` — a `good` transcript carrying the observed
wording and a `bad` one that actually asked the question, so the widened token still misses wrong
behaviour.

## Batch 3 ↻ — `analysis` (Gate 1), re-run under the new ruler — ✅ GREEN

Split in two on the timeout: the original 360s projected to ~558s at batch 1's observed 1.55× slowdown,
too close to the 600s ceiling to risk. Partition verified exact (union 13, `diff` empty).

```
Date            : 2026-09-02
git status      : clean
HEAD SHA        : 1fd64bf
Selector verified: 13 named · 13 present · 13 matched · 0 absent · 0 unnamed · 0 already-green
Part A (9 fixtures) : 103 pass / 0 fail — 341s dispatch / 350s total · 9/9 green · 9 minted
Part B (4 fixtures) :  86 pass / 0 fail — 352s dispatch / 360s total · 4/4 green · 4 minted
Fresh / cached  : 13 / 0
Coverage        : 13/13 judged green · 13 ledger rows · 13 cache entries minted
Run ids         : 20260902T141815Z-419585 · 20260902T142412Z-425863
Tokens          : unmeasured
```

**Failures:** none. The Gate-1 fixtures include the four `rule-section-*` handle paths and the two
happy-path runs (`full`, `lite`, `freeform`), all judged on header-stripped text.

Coverage after batch 3: **43 of 126 jobs**.

## Next

Batches 4–10 under this same fingerprint. Batch 10 must run **foreground, split in two halves**
(7 fixtures + 7 scenarios): its one background attempt was stopped host-side 3.5s after launch having
judged zero assertions. Batch 10 also has no recorded `Selector used` line, so its selector has to be
rebuilt and verified dispatch-free like any other. Expect to split most batches on the 600s timeout.

Coverage after batch 2: **30 of 126 jobs** hold a green row in the discovery ledger.
