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

## `--verify-suite` could never have passed: no scenario can be recorded at all

Found 2026-09-03, dispatching batch 10 — the first batch this cycle made only of scenarios. Both
probed scenarios passed every assertion, and then the run **died silently**: no dispatch summary, no
identity line, no assertion tally, exit 1, and **zero rows written**. No `FAIL` was printed anywhere.

`bash -x` put the death one statement past `_h="$(skills_hash "$_name")"` in the coverage-row loop
(`run.sh:3363`) — with `_h` correctly assigned. The mechanism is `set -euo pipefail` (`run.sh:264`)
meeting a pipeline whose first stage fails:

```
hash_files() { [ "$#" -gt 0 ] || return 1; cat "$@" 2>/dev/null | sha256sum 2>/dev/null | awk '{print $1}'; }
```

`skills_files` ends with `echo "$FIXTURES/$name.md"`, and **a scenario has no fixture file** —
scenarios are `run_prompt` labels, not tickets on disk (verified: `stuck-detector.md` and
`artifact-delta-emission.md` do not exist; `challenger-unmet.md` does). So `cat` exits non-zero,
`pipefail` promotes that to the pipeline's status, the command substitution inherits it, and `errexit`
kills the script *after* the assignment succeeded. Five lines reproduce it:

```
set -euo pipefail
hash_files() { [ "$#" -gt 0 ] || return 1; cat "$@" 2>/dev/null | sha256sum 2>/dev/null | awk '{print $1}'; }
h="$(hash_files /etc/hostname /nonexistent-file-xyz)"
echo "never reached"     # exit 1 here
```

**The consequence is that the shipped Finish bar is unreachable.** `--verify-suite` refuses unless
every one of the 126 jobs has a green row; 7 of them are scenarios; no scenario can ever get a row.
Every fixture batch this cycle passed straight through this code — `cat` succeeded for them — which
is why 118 rows exist and the defect stayed invisible for nine batches.

Why no test caught it: the coverage-gate self-tests build **synthetic** ledgers and do include a
`j2 scenario` row (`run.sh:2622`), so the gate's *reading* of a scenario row is proven. What was never
exercised is the *writing* of one. And `skills_hash` is called on a scenario name for the first time
in v1.15.0 — before it, scenarios only ever went down the dispatch path, which never hashes
(`run.sh:1161`: "scenarios have no cache path and always dispatch fresh").

### Rule
> **A gate self-tested against synthetic inputs is not self-tested against real ones.** Every writer
> the gate depends on needs a real-input test, not just the reader. The `--verify-suite` self-tests
> proved the gate could *judge* a scenario row and never that the suite could *produce* one — and a
> gate that cannot be satisfied is as false as a gate that cannot fail.

### Fix, queued for the proof-pass edit
Make the fixture path conditional in `skills_files`, keeping the function's exit status 0:

```
if [ -f "$FIXTURES/$name.md" ]; then echo "$FIXTURES/$name.md"; fi
```

A fixture's hash is unchanged (its file exists, so the same path is emitted); a scenario stops feeding
`cat` a path that is not there. Ship it with a self-test that writes and verifies a **real** scenario
row end to end.

---

## The vacuity fix did what it was supposed to: `ledger-gate-complete` went red

Found 2026-09-03, batch 10. This is the job recorded above as fully vacuous — every assertion on it
matched the harness header or its own name, so nothing it returned could have failed it. Made
decision-level in v1.15.0, it now fails, and the failure is real information rather than a regex miss.

The prompt states "a run made 4 subagent dispatches and the Cost ledger has 4 rows (one per dispatch
return)" and asks whether finalise proceeds or blocks. The model answered **"Not enough information —
row count alone doesn't clear it"**, then split the answer: all four token cells carrying a value or an
explicit `unmeasured (…)` marker → proceeds; any cell blank → blocks. It cited
`skills/finalise/SKILL.md:230-241` for the two-condition gate.

That is better behaviour than the assertion expects. The prompt fixes the row *count* and says nothing
about row *content*, and mango's gate has both conditions — the skill text is what made the model
careful. So the defect is in the scenario's premise, not the plugin, and **not in the assertion's
outcome**: widening it to accept "not enough information" would erase the distinction the gate exists
to draw.

### Rule
> **When a fixture and the model disagree at the outcome level, suspect the prompt before the
> assertion.** The repair is to complete the premise — state that every row carries a token value — so
> the scenario tests the dispatch-count gate it claims to test, while its sibling
> `ledger-content-gate-marker` keeps testing the content gate. Widening the assertion instead would be
> a loosened gate, which this repo does not do.

---

## The proof-pass edit, and the two things it turned up in itself

The single edit that fixes D1, R1 and R2 landed on 2026-09-03 as **v1.15.1** (harness-only; nothing
inside the plugin changed). D1's fix is one line in `skills_files`, but the *test* for it is the point:
the row-writing block became a function, `cov_row_for`, purely so the self-tests can call it. Four new
dispatch-free checks now exercise the writer on a job with no fixture file on disk — the hash returns
status 0, a green row comes out, that row satisfies the real gate against the real current hashes and
the real measurement identity, and the same holds for a real registered scenario label — plus a fifth
that asserts the control job genuinely has no file, so the set cannot pass vacuously. Each was
confirmed red with the fix reverted: **`--verify-suite` reports 17/22 with the defect and 21/22 with
it fixed** — the 4 substantive checks flip, and the one failure left in both cases is the ledger being
empty. Every one of them is *reported*; none kills the run.

Writing those tests produced two findings of their own.

### `set -e` is ignored inside an `if` condition — including a subshell that re-sets it

The obvious way to assert "this statement no longer fails" is to wrap it:

```bash
if ( set -euo pipefail; _sh="$(skills_hash "$_nf")"; [ -n "$_sh" ] ); then …
```

That check **passed with the defect present**. Bash ignores `errexit` for commands in an `if`
condition, and re-setting it inside the subshell does not restore it there. Measured in isolation: the
same call captured normally gives `rc=1` with a 64-character hash on stdout — a real status, invisible
to the wrapper.

The second half of that measurement matters as much as the first. The hash was **not empty** under the
defect: `cat` failing part-way through still leaves `sha256sum` a digest of the files that did exist.
So a check written against emptiness — the plausible one, and the one the gate's own error message
("no current skills-hash") suggests — would also have passed. Only the status distinguishes the two
worlds.

### Rule
> **Assert an exit status by capturing it (`rc=0; out="$(f)" || rc=$?`), never by wrapping the call in
> an `if` condition.** And when a defect has two observable consequences, check the one that actually
> differs: here, status, not emptiness. A guard that passes in both worlds is the same vacuity this
> file exists to record, whoever wrote it.

### Every assertion in this suite is line-bounded, and nothing says so

Recorded, **not fixed.** `assert_contains` and `assert_all` judge with `grep -qiE`, which matches
within a single line. So every widened window — `.{0,20}`, `[^.]{0,30}` — is bounded twice: by the
window, and by wherever the model happened to wrap. R1's own token is a case in point: "It was **not**
put to the user as an open want" matches because it landed on one line, and would not have if the
model had broken it after "an".

This is not R1's defect and not new — all 511 assertions have always been measured this way, and every
green in the ledger was measured under it. That is exactly why it is not fixed here: switching to a
whitespace-insensitive match would re-interpret every assertion in the suite at once, which is a change
of ruler and belongs to its own cycle with its own full pass.

### Rule
> **A token has to fit on one line of real output.** Prefer a short load-bearing phrase over a long
> window; when a window must be wide, expect the model to wrap it and write the alternative that
> survives the wrap. Changing how the match treats newlines is a ruler change, never a fix folded into
> a batch.

---

## A version pin that lives in a document is not a pin

The CLI moved 2.1.259 → 2.1.260 between two batches, and six rows were written under the new one. The
suite's identity tuple is `plugin-tree / model / CLI`, so a mixed ledger is a refusal — and the
document warning about exactly this, written after the same thing happened in the discovery pass, did
not prevent it.

The reason is worth separating from the symptom. The pin was real: a directory holding a symlink to
the right version, in place and correct the whole time. What was written down was
`export PATH="…/pin:$PATH"`, and **every dispatch runs in a fresh shell**. No run ever had the pin on
`PATH`. The earlier batches recorded the right version because the auto-update had not fired yet.
A pin that depends on a human remembering to re-export it each time is a note, not a control.

Undoing it exposed a second gap that would have survived the cleanup. The ledger reduces with
`awk 'NF>=11 {r[$1]=$0}'` — last row per job wins — so re-running the six supersedes the bad rows with
no hand-editing. But the transcript cache is keyed `$name.$skills-hash.green`, **carrying no CLI
version**. A plain re-run would have hit the cache, re-judged the 2.1.260 transcripts, and stamped the
new rows 2.1.259: a row asserting an identity its evidence never had. The entries had to be deleted by
name before re-dispatching.

### Rule

**Put the pin in the command, not in the prose** — every dispatch begins by exporting it and printing
`claude --version`, so the log shows the version beside the run it governed instead of the document
asserting it. And **whatever appears in the identity tuple must appear in the cache key**: a cache
entry that outlives a change to its producer is a false green waiting for a re-run. The skills-hash
catches skill edits and `job_fp` catches assertion edits; nothing yet notices that the thing which
produced the transcript changed.

## The suite judges the transcript, so an artifact written to a file is invisible

`exclusion-expiry-required` scored 3 of 4. Its three sibling assertions passed — the exclusion is not
counted as recorded, Gate 2 is blocked, a checkable expiry is named — and the failing one wanted the
counted line `EXCLUSIONS:` in the reply. The four-line transcript instead says the work doc *"holds …
the counted line"*. mango wrote the artifact to the file and referenced it.

This is a third class, beside wording and outcome: the behaviour may be right and the assertion may be
right, and the evidence still never reaches the judge. It matters most for exactly the assertions worth
having, because counted artifacts are the ones a model is most likely to file rather than recite.

Widening is the wrong instinct here. A looser pattern would accept prose *about* a count, which
defeats the reason a counted-artifact assertion exists. The fix is structural — require the count in
the reply, or preserve and judge the work doc.

### Rule

**An assertion may only require evidence the harness actually retains.** Before writing one, ask where
the artifact will live; if the answer is a file, either the prompt must pull it into the reply or the
harness must keep the file. And note what this incident cost: the worker clone is discarded, so the one
document that would settle whether the behaviour was correct no longer exists. A harness that throws
away the evidence its own assertions point at cannot adjudicate its own reds.

## A red that stops reproducing can be a false green wearing the same regex

`refine-want-unattended-stops` failed one assertion in batch 2 (recorded as R5), and passed it on the
re-run with **the assertion unchanged** — R5 was recorded, not fixed. The tempting reading is a flake
in the model's wording. The archive says otherwise.

The token requires `ASSUMED` and
`not[ *_]{1,4}(silent|adopt)|never[ *_]{1,4}(silent|assum)|does not|no[ *_]{1,4}silent`. Run against
both archived transcripts, every branch that tests the claim scored **0 on the green transcript as
well as the red one**. The pass came entirely from `does not`, on four lines — one of them a
`merge-strategy: squash-or-rebase …` configuration line, none of them about recording an `ASSUMED`.
The companion `ASSUMED` pattern adds nothing, because the fixture prints that word whichever way it
decides.

An alternation needs one branch. So the weakest branch sets the assertion's real strength, and a
branch of bare common English sets it to zero. Base rates over the 77 archived transcripts make the
size of that zero concrete: `not`, `no` and `on` each appear in **77 of 77**; `this` 71; `only` 64;
`would` and `can` 58; `never` 55; `does not` 35. A branch at 100% cannot fail. **39 assertions across
31 jobs** carry one.

Two facts bound it, and both were measured rather than assumed. No `assert_absent` is affected, so the
class produces only false greens and nothing already recorded as red is in doubt. And of the 7
affected jobs already banked green, six had a discriminating branch actually fire against their own
transcript; exactly one did not, and it is R5's.

The near-miss is worth naming: had the batch-2 red never happened, R5's assertion would have sat in a
green suite forever, and the number "126 of 126" would have included one job that no wording could
fail. A red is the only reason anyone looked.

### Rule

An alternation is only as strong as its weakest branch, so **a regex branch must not be satisfiable by
prose that any careful answer would contain.** Bind every negation to what is being negated
(`not[^.]{0,30}silent`), never leave `does not` / `not` / `no` standing alone, and when widening a
window prefer a bounded adjacency to a new free-floating branch. Two checks make this cheap: split
every assertion on its top-level `|` and reject bare-common-word branches, and for each green measure
whether a *discriminating* branch fired — a green whose only firing branch is the weak one is not
evidence.

Fixing such a branch is a narrowing, not a widening, so it does not collide with the rule that this
suite never widens over outcome. It is queued for the post-batch-10 edit: deleting the dead branch
changes only that job's `job_fp`, so the gate names that one job stale and it alone re-runs.

## A whole-file fingerprint charges 126 dispatches for a one-line fix

The coverage ledger was named `coverage.<sha256 of all of run.sh>.tsv`. Editing anything in the file
renamed it, so every recorded row was voided at once. Under that rule the cycle's arithmetic was:

```
sampling pass  126 dispatches  → k reds
one fix edit                   → ruler moves, 0 rows
proving pass   126 dispatches  → if any new red, start again
```

At the measured per-pass red rate (1.7%–7.7%, so 2–10 reds in 126 jobs) the proving pass is unlikely
to be clean first time, and each retry is another 126. The plan had no termination condition — it
was a bet that a pass would come up empty.

**The property actually required is per job:** a row may be credited only if it was produced by the
same question, and the same judging, that this job is subject to now. Whole-file equality *implies*
that, which is why it was never wrong — only enormously over-broad. A comment, a timing line, a
widened token in one unrelated fixture all cost the same 126 dispatches as rewriting the dispatcher.

The fix (v1.16.0) splits identity in two:

| Tier | Covers | An edit voids |
|---|---|---|
| `MACHINERY_FP` — names the ledger | every function defined **above `suite()`**: dispatch, prompt assembly, judging, hashing, the row writer, the gate | all rows |
| `job_fp` — row field 12 | that job's prompt, its harness test-command, and every `(assertion-kind, resolved regex-set)` that judges it, sorted | that job's row only |

Three decisions inside it are the ones worth carrying to any similar ledger:

- **The boundary is structural, not an allowlist.** `MACHINERY_FP` is taken at the exact point in the
  file where `declare -F` knows every machinery function and does not yet know `suite`. An allowlist
  drifts the first time someone adds a helper and forgets to register it, and it drifts silently in
  the unsafe direction. A self-test still enforces the boundary: any function matching the
  judging/dispatch name shape that is defined *below* it fails the run by name.
- **`declare -f`, not a text slice.** Bash's parsed form drops comments and normalises layout, so
  re-wording a comment or re-indenting voids nothing. That removed the largest single source of
  accidental invalidation, and it is *tested* rather than trusted — a self-test builds two functions
  differing only in comments and asserts their `declare -f` output is identical.
- **What must NOT move the fingerprint is as load-bearing as what must.** An assertion's *label* is
  excluded by construction: charging a dispatch to fix a typo in a label teaches an operator to leave
  labels wrong. Assertion *order* is excluded too (the set is sorted), because no assertion in this
  suite reads another's result. Both exclusions have their own self-test, as do the inclusions —
  editing a regex moves it, and swapping `assert_contains` for `assert_absent` with the *same* regex
  moves it, since that inverts the test without changing a character of pattern.

**The hole this closed on the way past.** A fixture's prompt derives from its ticket file, which the
row's `skills_hash` already covered — but a **scenario's** prompt is written inline in `run.sh` and
was covered by nothing per-job; the whole-file hash had been carrying it. Dropping to per-job identity
without folding the prompt in would have let a scenario's question be rewritten while its green row
stood. Going finer forces you to enumerate what the coarse hash was silently doing, and that is where
the real risk in a change like this lives — not in the tier you design, but in the one you forget.

### The migration that was refused

35 rows existed under the old ruler, and no assertion or prompt had changed — only machinery. They
could have been credited by appending a computed `job_fp` to each, saving 34 re-dispatches, on the
argument that the machinery edit was "bookkeeping, not judging".

That argument was declined. `MACHINERY_FP` exists precisely so that whether a harness change affects
a verdict is not decided by the person who made the change. Crediting rows across a machinery move
because the author judged it harmless is the failure mode the fingerprint was built to refuse, and
the precedent is worth more than 34 dispatches — the next such judgement is always made with less
care than the first. The rows were re-measured.

The forward cost is what changed, and that was the point: **126 + k**, where k is the number of jobs
whose assertions a fix touches, instead of 126 per fix round with no bound. And k is usually cheaper
still: a *green* job whose token is edited is re-judged against its cached transcript with **no
dispatch at all**, because the cache now survives an assertion edit. Only a red job — which has no
cache entry, since only greens are minted — costs a real dispatch.

## A negation token written `not X` cannot see how the model actually spells the negation

Batch 1 of the proof pass went 101/102 on one assertion:

```
FAIL: vague-requirement: flags AC-1 as not falsifiable
      (missing /not falsifiable|not measurable|unmeasurable|vague|manual-check/)
```

The behaviour was right. The transcript said:

> **AC-1 split into two clauses, both flagged as neither falsifiable nor excluded, both barred from a
> matrix `✅`**

`neither falsifiable nor excluded` *is* the negative verdict — arguably a more precise one, since it
reports on exclusion as well. The token only knew how to spell the negation one way.

The reason this is worth writing down is not the regex. It is **how the wording/outcome distinction was
settled**, because that is the judgement that decides whether widening is legitimate or is the suite
quietly losing its teeth. Two independent signals said *wording*:

- **The sibling assertion passed on the same transcript.** `vague-requirement: cannot carry a bare ✅`
  is an `assert_all` over the guard itself, and it fired. So the mechanism under test demonstrably ran;
  only one description of it went unrecognised.
- **The failing token is a synonym list, not a condition.** All five of its alternatives mean the same
  thing. A token like that failing is evidence about vocabulary. A token encoding a *condition* failing
  is evidence about behaviour, and must never be widened.

Then the widen was proved in **four** directions before the ruler was allowed to move — the third is
the one usually skipped, and it is the one that distinguishes a necessary fix from a cosmetic one:

| Check | Why it has to be run |
|---|---|
| new token vs the real transcript → match | the red actually clears |
| new token vs a synthetic **wrong** outcome → no match | the assertion still fails bad behaviour |
| **old** token vs the real transcript → miss | the widen is load-bearing; if the old token matched, the red had another cause |
| the added alternative alone vs the wrong outcome → no match | the new clause is not the leaky one |

A static sweep of the other 513 assertions for the same shape was considered and **rejected**. About 40
carry a literal `not <word>`, but which of them a model will phrase with `neither … nor` is unknowable
without a transcript, and pre-emptively widening 40 negation tokens against a hypothesis is precisely
how a suite stops discriminating. A second ruler move later is the cheaper mistake than a suite that
passes everything.

### Four instances, four spellings — the class is the pattern, not the regex

By the end of batch 4 the same class had produced four reds in four passes, each defeating a
*differently shaped* token:

| # | Job | What the token could not see | Why it missed |
|---|---|---|---|
| R3 | `vague-requirement` | `neither falsifiable nor excluded` | the token enumerated synonyms of `not <word>` and `neither` was not among them |
| R4 | `greenfield-recall-handles-none-match` | `No — neither source makes them so` | same, in the other word order |
| R5 | `refine-want-unattended-stops` | `ASSUMED is not the fallback for silence` | the token's `not[ *_]{1,4}silent` allows ≤ 4 characters between the two words; the model put 17 there |
| R7 | `evidence-stale-tree-refused` | `## 3. Does "84 passed" establish AC1 and AC2? No — for two independent reasons.` | the negation is not adjacent to the verb at all: it is a **question answered "No"**, so the only line carrying both the claim and its denial spells the verb *affirmatively* |

R5 is the useful one, because it is **not** a `neither` case. The first heading of this finding named
the symptom (`neither X nor Y`) and it turned out to be one dialect of a wider defect: **a negation
written as an adjacency — `not` within *n* characters of a keyword — is a bet on how many words the
model will put in between, and that number is not knowable in advance.** Widening the character window
does not fix it either; it only moves the bet, and a window wide enough to catch "not the fallback for
silence" is wide enough to leap into a neighbouring clause and match an affirmative.

R7 is the sharpest of the four, because it defeats the whole shape of the fix. R3 and R4 argued for
enumerating more synonyms; R5 argued for a wider window. R7's line contains the verb `establish` in
the **affirmative** — `Does "84 passed" establish AC1 and AC2?` — and the denial is a separate word,
`No`, after the question mark. No amount of synonym-listing or window-widening inside a `not …
establish` shape can read that, because the line is not a negation of the verb; it is a question whose
answer happens to be negative. All five alternatives of `RE_DOES_NOT_ESTABLISH` scored 0 against a
90-line transcript whose entire section 3 is devoted to answering exactly this assertion's question,
correctly, twice over.

It also sharpens the weak-branch finding above. `RE_DOES_NOT_ESTABLISH` *contains* the free-floating
`does not` branch that made R5 a false green — and here it did not fire, because this particular
90-line answer never used the phrase. So the same branch is a coin toss in both directions: too weak
to refuse a wrong transcript, too unreliable to accept a right one. It buys nothing in either
direction, which is the strongest argument for deleting it rather than tuning it.

What the four have in common is diagnostic, and it is what makes the wording verdict defensible each
time: **a sibling assertion on the same transcript passed**, so the mechanism provably ran, and **the
failing token was a synonym or adjacency list rather than a condition**. Both signals must be present.
Neither one alone licenses a widen.

The standing conclusion — which R5 does not change, and reinforces — is that these are found only by
running, one real transcript at a time, and that a speculative sweep over the ~40 similarly-shaped
tokens cannot be proved in the four directions above because there is no failing transcript to prove it
against. What R5 *does* change is the preferred fix: where a **counted artifact** states the same fact
(R5's transcript prints `0 ASSUMED` twice), anchoring on the count is stronger than any prose window,
because a count cannot be paraphrased. That is only available when a sibling assertion is not already
covering that count — the trap R4 walked up to, where re-anchoring would have deleted a check instead
of strengthening one.

### One dispatch per assertion samples one phrasing

Batch 1 of the proof pass ran the same 7-fixture part twice. Attempt 1: **97/97**. Attempt 2:
**96/97** — a *different* assertion, on a different fixture, both in the negation-vocabulary class
above. Nothing had changed but the dispatch.

These are not flaky assertions in the usual sense. Nothing is racing and nothing is timing out. The
token is simply narrower than the space of correct answers, and each run draws from that space afresh:
one run says "not applicable", the next says "neither is". A pass therefore does not measure the suite,
it *samples* it — and the first discovery pass, which dispatched every job exactly once, recorded
"nothing left to discover" when what it had was one sample per assertion.

The consequence is structural, not cosmetic. Proof requires all 126 job rows green under **one** ruler;
fixing any assertion moves `RUNNER_FP` and voids every row already bought. So fix-as-found converges
only if some full pass happens to come back with zero reds. Batch 1's 47 transcript assertions produced
one red on each of two passes (~2%); the discovery pass's own rate was ~0.4% (2 of 511). Both samples
are small, but both are non-zero, and at either rate a clean 511-assertion pass is not something to
plan around.

The second cost was self-inflicted and is now fixed: `run.sh` wiped `.transcripts/` at the start of
every run, so a token could only ever be re-judged against the last part that ran. Two reds of the same
class therefore cost two passes to find and would have cost two more to fix, when a stored corpus would
have closed both at once for free.

### Rule

**Never conclude a suite is clean from one dispatch per assertion, and keep every transcript.** A pass
that finds no reds has established that the assertions matched *one* sample each — for a synonym-list
token that is weak evidence. So: archive every judged transcript, reds included, outside the directory
the runner wipes; when a red is fixed, sweep the widened token across the whole archive rather than the
one file that failed, checking that it matches where the outcome is right and still misses where it is
wrong. And when reds are still being discovered, **sample before proving**: one pass that records reds
without fixing them, one edit that closes every class it found, then one pass that proves. Fixing as
found is correct only once the discovery rate is actually zero. The archive must never be read back as
a verdict — evidence for writing assertions, never an input to judging — or it becomes the cache a
false green hides in.

### Rule

**Widen a negation token only against a transcript that actually failed on it, and prove the old token
missed that same transcript.** Two questions decide whether widening is allowed at all: did a sibling
assertion confirm the mechanism ran, and is the failing token a synonym list or a condition? Synonyms
plus a passing sibling is wording — widen. A condition failing is outcome — fix the skill, never the
token. And never widen a token class speculatively across assertions that have not failed: the four
proof directions cannot be run without a real red, so a speculative widen is unprovable by
construction.

## Rules that keep a cycle valid

These are process rules, learned the hard way, and they cost nothing to follow.

1. **Never touch `run.sh` mid-cycle.** Not a fixture, not a name, not the `FIXTURE_SKILLS` map. Every
   one of those changes the runner fingerprint, which wipes every `.green` and starts a fresh ledger —
   so a fix applied at batch 2 throws away 30 greens, and one applied at batch 8 throws away 100.
   Record the red, fix them all in **one** edit, then run the proof pass. See
   [`EVAL-STATUS.md`](./EVAL-STATUS.md) → *Strategy*. In the **proof** pass the calculus inverts: a red
   found at batch 1 costs 12 jobs to fix and one found at batch 8 costs 100, so fix it immediately.
2. **Verify the selector before dispatching.** `--only 'greenfield'` once matched 3 of 4 fixtures and
   reported success. Check it dispatch-free: every name in the regex present on disk, every match
   named, nothing extra.
3. **Commit before every batch.** The harness clones HEAD; an uncommitted change means the batch tested
   a tree that is not the one you edited.
4. **Record the row before starting the next batch**, not at the end of the cycle.
5. **Split a batch that would exceed the tool timeout.** Splitting is free now that each part mints its
   own cache entries and writes its own coverage rows — no fixture is dispatched twice.
6. **Run every part in the foreground — not just scenarios.** First seen on a scenario part stopped
   host-side 3.5s after launch having judged zero assertions, so it was written up as a scenario
   quirk. Batch 1 of the proof pass showed it is not: two background dispatches of an ordinary
   **fixture** part were reaped within ~10s of the dispatch line — `[killed]`, no error, no partial
   output — while a sibling part had run 401s in background without trouble. So it is intermittent and
   not scenario-specific, and the residual cause is still on the Stop/interrupt path. A killed run is
   *safe* — it writes no rows and leaves nothing behind — but it is wasted wall-clock, and the 600s
   foreground ceiling covers any part whose slowest job is under ~400s. Before re-dispatching a killed
   part, confirm rather than assume the state is untouched: ledger row count, `git status`, no stray
   `PROJ-*` branch, no live `run.sh`, no worker clone left on disk.

---

## A result nobody stores is a result nobody has

The 1.14.0 CHANGELOG (§D) records that this repo stored **no eval results at all** — the only one was
from v1.7.6. That is why four assertions shipped having never run, and why a `grep` bug that made four
assertions **unpassable** survived undetected.

The coverage ledger is the answer to that, and it is a machine artifact on purpose: a markdown file
cannot be asked whether a job was missed.
