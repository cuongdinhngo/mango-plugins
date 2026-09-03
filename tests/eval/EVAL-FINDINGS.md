# EVAL-FINDINGS.md — harness defects found by running the eval, and the rules they produced

This file is **cross-cycle and permanent.** It holds what stays true after a cycle's numbers stop
counting: defects found in the harness itself, the method that found each one, and the rule each one
left behind. Per-batch statistics do not belong here — they live in
[`EVAL-STATUS.md`](./EVAL-STATUS.md) while a cycle is running and in
[`EVAL-ARCHIVE.md`](./EVAL-ARCHIVE.md) once it is superseded.

**Rule for adding to this file:** a finding is admissible only with the **counted evidence** that
established it and the **method** that produced the count, so a later reader can re-run it. A number
with no method is an assertion, not a finding.

| File | Job |
|---|---|
| [`EVAL-STATUS.md`](./EVAL-STATUS.md) | the current cycle — what is green, what is red, what runs next |
| `EVAL-FINDINGS.md` | this file — permanent findings and rules |
| [`EVAL-ARCHIVE.md`](./EVAL-ARCHIVE.md) | superseded cycles, verbatim |
| `.cache/coverage.<runner-fp>.tsv` | **the authority.** `bash tests/eval/coverage-report.sh` reads it |

---

## The one that matters most — three assertions PASSED on a transcript that never ran

Found 2026-09-01, cycle 1 batch 4. `API Error: 529 Overloaded` meant seven `design` fixtures never
dispatched. Three of them recorded a **PASS** anyway, by three distinct mechanisms:

| Assertion | Why it passed on nothing |
|---|---|
| `blast-radius: folds it in as collateral` | needs `/blast[ -]radius\|collateral/` — the harness's own header line is `== fixture: blast-radius ==`. **The regex matched the fixture's name.** |
| `unanswered: the unanswered handle is named as the cause` | needs `/handle/` AND `/unanswered/` — both present in `== fixture: handle-unanswered-blocks ==` |
| `recurrence: mango does not auto-discharge the overdue class` | `assert_absent` — a transcript with no run contains nothing, so nothing is present to fail it |

**Root cause.** `assert_judgeable` asked only whether the transcript was **non-empty**. A 529 produces
a file that exists and is non-empty yet contains no run — a third state the harness did not model.
mango itself added exactly that state in 1.14.0 for test evidence (`provenance-unknown`, "never a
pass"); its own harness had no equivalent for a dispatch that did not happen.

**Closed by** Fix 1 (a transcript carrying `API Error: …` or an empty body is not judgeable — every
assertion on it fails loudly, `--only` or not) and Fix 3 (the header is stripped before any regex sees
the transcript), both shipped in v1.15.0.

**Confirmed closed** 2026-09-02: the same 17 `design` fixtures re-ran with zero failures and no
`API Error` in any transcript.

### Rule
> **A no-run is never a result.** Not a pass, not a wording failure, and not a skip — a skip is what
> `--only` used to record for a missing transcript, which is how a partial run could go quietly green.

---

## Fix 3's blast radius — 32 unfalsifiable assertions, counted rather than estimated

**Method** (re-runnable, costs nothing): run the assert pass twice with no dispatch — once over
transcripts containing **only** the harness header, once over transcripts containing neither the header
nor anything else. The difference is exactly what the header was carrying.

```
passes on a header-only body : 57
passes on a no-header body   : 25   ← assert_absent negative controls, passing by design
HEADER-CAUSED assertions     : 32   ← fully unfalsifiable: passed on ANY transcript
distinct jobs affected       : 31
```

**32 of the suite's 511 transcript assertions were unfalsifiable** — not the "one" an earlier static
audit had found. That audit looked for jobs whose *every* assertion was vacuous, so it could not see an
individual check escaping through the harness's own text. The 25 `assert_absent` passes are correct for
a negative control and are now safe against a no-run for Fix 1's reason instead.

A separate static pass over 510 assertions (cycle 1, batch 4) found **`ledger-gate-complete`** the one
*fully* vacuous job: its single check looked for `/proceed|passes|not block|does not block|complete/`
and its own name contains **complete**, so it could not fail on any transcript, ever. Closed by Fix 2,
rewritten decision-level and strictly narrowed.

### Rule
> **Count a blast radius; do not estimate it.** The estimate in this repo's own notes was "~54"; the
> measured answer was 32, and the method that produced it is a script anyone can re-run. A number that
> reaches a public doc needs a method that survives being checked.

---

## The dispatch loop leaked its stdin into the model's prompt

Found 2026-09-02, cycle 1 batch 10. `ledger-gate-complete`'s transcript ended with the model saying
*"the trailing `1 2 3 4 5 6 7` in your message didn't parse as part of the question"*. There were
exactly 7 jobs in that half, and the scheduler's job list is the integers 1..7.

`claude_run` ran `( cd "$repo" && claude -p … "$@" )` with **no stdin redirection**, called from inside
`while read -r idx; do … done <"$JOBS_DIR/schedule"`. The child inherited the loop's stdin — the
schedule file — and read it, so the remaining job indices arrived appended to the prompt.

Two consequences, the second worse:

1. **Prompt pollution.** A job can be judged on a transcript whose prompt was not the prompt the
   fixture wrote. Here it cost some wasted output; it could as easily have changed a decision.
2. **A silent-skip path.** A worker whose child consumed its schedule sees EOF and stops claiming. With
   fewer workers than jobs a registered job can go undispatched — and under `--only` a missing
   transcript was counted **skipped**, never failed. **Every partial run in cycle 1 would have gone
   quietly green.**

It did not bite, and that was **checked rather than assumed**: every batch's intended fixtures were
confirmed to have assertions attributed to their transcripts, batch by batch.

**Closed by** Fix 5: dispatches run with `</dev/null`.

### Rule
> **A guard that reports "skipped" is a guard that can be satisfied by absence.** Prefer a loud failure
> over a silent omission in every partial mode.

---

## `--only` minted no cache, so batching cost ~2×

Found 2026-09-01, pre-flight, by source-read only. The cache gate was
`[ "$CACHE_ENABLED" -eq 1 ] && [ "$fails" -eq 0 ] && [ -z "$ONLY" ]` — a partial run never minted a
`.green`, by design: *"a cache entry may only ever be minted by a run that proved the whole suite
green."* Ten batches under `--only` = 126 fresh dispatches, and the final full pass re-dispatched all
126 again: **~2× a single full run, not 1×**.

**Closed by** Change A: a `--only` batch now mints its green fixtures' cache entries on **per-entry**
evidence. Proved end-to-end at a cost of one dispatch:

```
run 1  --only '^budget-rtk-wire-guidance$'   1 fresh dispatch, 74/74, 1 ledger row, 1 cache entry minted
run 2  --only '^budget-rtk-wire-guidance$'   1 CACHE-HIT, 0 dispatches, 74/74, 80s → 7s
```

### Rule
> **Per-entry evidence beats a suite-wide gate.** The old gate was not wrong about the risk — a batch's
> `fails -eq 0` does not mean the suite passed — it was wrong about the granularity. What a batch
> actually proved is one fixture at a time, and that is what it may now record.

---

## The ruler was invisible to every hash

Found 2026-09-02, reasoning about what ten green batches could and could not establish. The batches
were real: 126/126 jobs judged, 0 failures, and the arithmetic composes — verified, not assumed, since
the cache stores a **transcript** and never a verdict, so every assertion is re-judged from text on
every run (a script confirmed **0** assertions read across two transcripts).

What they were not was a **counted artifact**. They lived in a markdown file where nothing could
re-check that no job had been missed, that no green had gone stale, or that every batch had used the
same ruler. And *ruler* was the gap: the per-fixture skills-hash keys everything a fixture reads from
the skill corpus and deliberately nothing else, so `scripts/*.py`, `plugin.json`, the model and the
`claude` CLI version could all have changed across the ~21 hours the ten batches spanned with no hash
noticing. Nothing did change — the only commits in that window touched the log, and the CLI held at
2.1.258.

### Rule
> **"Nothing changed" and "an artifact proves nothing changed" are different claims.** This repo exists
> to keep them apart. The measurement identity — runner fp, plugin-tree fp, model, CLI version — is now
> recorded in every ledger row, and `--verify-suite` refuses if any two rows disagree.

---

## What v1.15.0 shipped in response

| | |
|---|---|
| `--verify-suite` | No dispatch, no cost. Learns the suite from the assertion **call sites** (126 jobs, 511 transcript assertions — derived, never hardcoded), then holds the coverage ledger against it. Refuses on: a job with no row, a non-green row, a **stale** skills-hash, a row disagreeing on runner-fp / plugin-tree-fp / model / CLI, a row proven against fewer assertions than the suite now holds, or an owning run whose self-tests failed or never ran. All seven refusals **self-tested non-vacuously** against synthetic ledgers. |
| Coverage ledger | `coverage.<runner-fp>.tsv` + `runs.<runner-fp>.tsv`, one row per job per run, append-only, last-row-wins. Carries the job's skills-hash and all four ruler components. |
| Change A | A `--only` batch mints its green fixtures' cache entries, on per-entry evidence. |
| Change B | A full pass clears the same coverage gate before printing its result, so the machinery a batched green depends on cannot rot unnoticed. |
| Fix 1 | A transcript carrying `API Error: …` or an empty body is **not judgeable**. |
| Fix 2 | `ledger-gate-complete` rewritten decision-level. Strictly narrowed. |
| Fix 3 | The harness header is stripped before any regex sees the transcript. |
| Fix 5 | Dispatches run with `</dev/null`. |

### The documented bar moved — deliberately, and it narrowed

`CONTRIBUTING.md` and [`README.md`](./README.md) previously set the bar at one `--no-cache` full pass.
It is now **every job green under one ruler, proven by `--verify-suite`**. That **widens how the bar can
be reached** (batches, or one invocation) and **narrows what counts as reaching it** — a bare full pass
never recorded the runner, plugin tree, model or CLI version behind its own result, so nobody could
check afterwards which ruler it used. `scripts/validate.py` gained **3 new checks per doc (+6, 2051 →
2057)** pinning the new bar; **no check was removed** and the three old ones still pass.

---

## The selector-derivation script under-counted the fixture map by 46%

Found 2026-09-02, deriving batch 6's selector. `FIXTURE_SKILLS` is a bash associative array written
several `[key]="value"` pairs to a line, for readability. My extraction was
`sed -n 's/^[[:space:]]*\[\([^]]*\)\]="\([^"]*\)".*/\1\t\2/p'` — a substitution, so it rewrites
**one match per line** and silently drops the rest. It reported **64** entries where the map holds
**119**, and a coherent-looking skill histogram on top of them (`6 review`, not the true `12`).

Nothing flagged it. The block is 64 lines long, so "64 entries" agreed with the line count and looked
like a clean parse; the count is also close enough to the 64 green rows then in the ledger to pass a
glance. Re-extracting with `grep -oE '\[[a-zA-Z0-9_-]+\]="[^"]*"'` gives 119 keys, 119 distinct —
matching the 119 fixtures on disk, which is the cross-check that catches it.

The cost was zero only because the derived batch was checked against an independent number: this
cycle's own status file already recorded `review 11`, and the corrected derivation reproduced it
(12 pure-`review` fixtures, 1 already green). Under the wrong parse, six of the eleven would have gone
unrun and the batch would have reported green.

### Rule
> **A derivation that feeds a dispatch must reproduce a number it did not compute.** Every selector is
> derived fresh — from `FIXTURE_SKILLS` re-parsed with `grep -oE`, intersected with
> `coverage-report.sh --remaining` — then proven an exact partition with zero named-but-absent and zero
> over-matched jobs *before* dispatch. Copying a recorded selector skips the check that a rebuild
> performs. This is the third silent-corruption-in-a-text-pipeline defect in this cycle; the first two
> were an empty `sed` regex reusing its predecessor and a glob matching its own generated output.

---

## The CLI updated itself mid-cycle, and the ledger was the only thing that noticed

Found 2026-09-03, in batch 7 part A's identity line: `CLI 2.1.259 (Claude Code)` where every row
before it read `2.1.258`. Nothing announced the upgrade. The ledger now splits **76 rows at .258, 17
at .259**, and `coverage-report.sh` reports `distinct rulers among rows 2 (NOT uniform)`.

This is the *exact* scenario the invisible-ruler finding described as possible but unobserved: "the
model and the `claude` CLI version could all have changed across the ~21 hours the ten batches spanned
with no hash noticing. Nothing did change." This cycle, it did. The difference is that v1.15.0 had
already made the CLI version part of every row, so the split is a **counted fact** rather than a thing
nobody could have known.

Two consequences, separated because they are not the same claim:

- **The discovery pass is unharmed.** Its rows were never proof — `EVAL-STATUS.md` says so in its own
  blockquote — and the proof pass is a single full run under one CLI by construction.
- **The cache does not key on the CLI.** The wipe at `run.sh:631` triggers on `RUNNER_FP` (the
  `run.sh` hash) alone, so a transcript produced by .258 stays a cache hit under .259. That is safe
  here only because the proof-pass edit fixes R1 *inside* `run.sh`, which moves `RUNNER_FP` and wipes
  every entry. Read, not assumed — the block is nine lines and does exactly that.

The upgrade route is worth naming, because the obvious guard was already set and did not hold: the
install is native (`~/.local/bin/claude` is a symlink into `~/.local/share/claude/versions/`),
`~/.claude.json` has `"autoUpdates": false`, and it also has `"autoUpdatesProtectedForNative": true`.
Both 2.1.258 and 2.1.259 remain on disk, so pinning is available.

### Rule
> **A run long enough to matter is long enough for its tooling to change under it.** The proof pass is
> one uninterrupted full run; pin the CLI for its duration by putting the chosen
> `~/.local/share/claude/versions/<v>` first on `PATH`, and record the version. Turning off
> auto-update in config is not sufficient evidence that it is off — the version on disk is.

---

## Rules that keep a cycle valid

These are process rules, learned the hard way, and they cost nothing to follow.

1. **Never touch `run.sh` mid-cycle.** Not a fixture, not a name, not the `FIXTURE_SKILLS` map. Every
   one of those changes the runner fingerprint, which wipes every `.green` and starts a fresh ledger —
   so a fix applied at batch 2 throws away 30 greens, and one applied at batch 8 throws away 100.
   Record the red, fix them all in **one** edit, then run the proof pass. See
   [`EVAL-STATUS.md`](./EVAL-STATUS.md) → *Strategy*.
2. **Verify the selector before dispatching.** `--only 'greenfield'` once matched 3 of 4 fixtures and
   reported success. Check it dispatch-free: every name in the regex present on disk, every match
   named, nothing extra.
3. **Commit before every batch.** The harness clones HEAD; an uncommitted change means the batch tested
   a tree that is not the one you edited.
4. **Record the row before starting the next batch**, not at the end of the cycle.
5. **Split a batch that would exceed the tool timeout.** Splitting is free now that each part mints its
   own cache entries and writes its own coverage rows — no fixture is dispatched twice.
6. **Scenarios run foreground.** The one background attempt was stopped host-side 3.5s after launch
   having judged zero assertions; the residual cause is on the Stop/interrupt path.

---

## A result nobody stores is a result nobody has

The 1.14.0 CHANGELOG (§D) records that this repo stored **no eval results at all** — the only one was
from v1.7.6. That is why four assertions shipped having never run, and why a `grep` bug that made four
assertions **unpassable** survived undetected.

The coverage ledger is the answer to that, and it is a machine artifact on purpose: a markdown file
cannot be asked whether a job was missed.
