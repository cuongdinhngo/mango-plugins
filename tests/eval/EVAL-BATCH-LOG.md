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
| 2 | `refine` | ~12 | ⬜ not run | | | | | | | |
| 3 | `analysis` | ~12 | ⬜ not run | | | | | | | |
| 4 | `design` | ~13 | ⬜ not run | | | | | | | |
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
Batches green      : 1 / 10   (batch 1 — the stop-gate)
Jobs run           : 10 / 126
Tokens spent       : unmeasured (the host reports none; 10 dispatches, ~5 min at 8 workers)
Estimated remaining: 116 jobs — but see the pre-flight finding: no batch writes cache,
                     so the remaining work is one full 126-job pass, not 116 batched jobs
Run still valid    : yes — fingerprint unchanged at e23452eb…1da28
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
