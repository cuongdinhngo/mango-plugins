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
| 5 | `execute` | ~12 | ⬜ not run | | | | | | | |
| 6 | `review` + `challenger` | ~13 | ⬜ not run | | | | | | | |
| 7 | `finalise` + learning loop | ~13 | ⬜ not run | | | | | | | |
| 8 | `autorun` + contract + reconcile | ~13 | ⬜ not run | | | | | | | |
| 9 | `promote` + `codify` + `breakdown` | ~13 | ⬜ not run | | | | | | | |
| 10 | supporting skills + greenfield controls | ~13 | ⬜ not run | | | | | | | |
| — | **Final pass** (whole suite, expect all cached) | 126 | ⬜ not run | | | | | | | proves green *together*, not in ten fragments |

**Status values:** ⬜ not run · 🟡 running · ✅ green · 🔴 red · ⚠️ void (fingerprint changed)

**Tokens:** record what the host actually reports. If it reports nothing, write `unmeasured` — never an
estimate dressed as a measurement. Dispatch totals are the one figure the ledger does give.

---

## Running total

```
Batches green      : 4 / 10   (1 — stop-gate; 2 — refine; 3 — analysis; 4 — design, on re-run)
Fixtures proven    : 61 / 119.  Scenarios run: 0 / 7 — no scenario has run this cycle.
Jobs proven green  : 61 / 126
Dispatches spent   : 78  (10 + 21 + 13 + 17 red + 17 re-run) — 17 of them paid twice, to a 529
Assertions passed  : 476 / 476 across the four green batches, 0 failures
Tokens spent       : unmeasured (the host reports none; 78 dispatches, ~37 min at 8 workers)
Estimated remaining: 58 jobs (51 fixtures + 7 scenarios) — but no batch writes cache, so the
                     remaining work is still one full 126-job pass
Run still valid    : yes — fingerprint unchanged at e23452eb…1da28. Batches 1-3 validated by the
                     vacuity audit; batch 4 re-proved on fresh transcripts with no API error.
```

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
