# mango per-skill smoke guard

**mango has no behavioural regression suite.** This directory holds a smoke guard: six fixtures, run
when a skill is edited, answering one question —

> *Does the skill I just edited still behave?*

It does **not** answer *"is mango green?"*. Nothing here should be cited as though it did.

```bash
bash tests/eval/run.sh                                        # all six  (~6 dispatches, ~$3)
bash tests/eval/run.sh --only '^(multi-clause-want)$'         # the fixtures for the skill you edited
bash tests/eval/run.sh --workers 1                            # sequential — debugging one transcript
bash tests/eval/run.sh --no-cache                             # full fresh run: nothing is reused
```

## The two stated limits

Written down here rather than left to be discovered later:

- **No cross-skill regression detection.** Editing `design` and breaking `finalise` is not caught.
  This is accepted, not overlooked: it never once happened in this repo's recorded history — searched
  across the archive, the findings register, the status register, the CHANGELOG and the git log.
- **`RETIRE:` is uncovered.** It has no assertion here, and it had none in the retired suite's 511
  either. `promote` emits it at the ratify step; the `promote` fixture kept below is the zero case,
  which by construction never reaches a ratify.

## The six

| Fixture | Skill(s) | What it is for |
|---|---|---|
| `refine-want-unattended-stops` | `refine`, `autorun` | **Gate 0.** The worked example of a claim bound to a **counted line**: an unresolved want-decision counts toward `j`, autorun stops, and it is never a silent `ASSUMED` — judged against the `REFINE:` line's own arithmetic. |
| `multi-clause-want` | `analysis` | **Gate 1.** A two-clause want-decision becomes two matrix rows and two proof rows; the injected single-row certification is flagged. Three `all` assertions, no `contains` to pass through. |
| `provenance-authored-blocks` | `design` | **Gate 2.** An AC about a grouping heuristic proven on authored fixtures alone blocks the gate; anchors on `EXCLUSIONS:`. This gate exists because of four real-data defects the retired fixture suite never saw. |
| `execute-commit-before-review` | `execute`, `review` | **Gates 3–4.** Commit ordering across two skills, plus the empty-diff fallback. |
| `lesson-claim-split` | `finalise` | **Gate 4.** Anchors on `CLAIMS:`, a counted line with internal arithmetic — ticket 099's `CLAIMS:` summed to 4 while stating 3, and `check_lines.py` catches that with no grammar judgement. `finalise` emits 6 of the 20 counted grammars, more than any other skill. |
| `greenfield-promote-zeros` | `promote` | **The negative control.** An empty corpus emits zeros, proposes nothing and writes nothing: `absent  rules written[ *_:=]*[1-9]`. |

Every fixture is mapped in `FIXTURE_SKILLS` in `run.sh`. **That map is the trigger mechanism** — a
fixture that is not mapped cannot be selected by a skill edit, and `validate.py`'s `eval-guard`
validator fails if any of the six loses its key.

## Anchor every `--only` selector

Write `^(name-a|name-b)$`. An unanchored `--only` once dispatched a scenario *inside* a fixture name
and reported success on a job nobody meant to run.

## Assertion convention (standing — practised since v1.0, written down here)

This is the part of the retired suite that was worth keeping, and it is unchanged:

- **Match the DECISION, not one phrasing.** An assertion encodes outcome *and* reasoning — `assert_all`
  with two tokens — so a correct behaviour passes under any wording while a wrong outcome, which drops
  one of the tokens, still fails.
- **Be emphasis-agnostic.** `**S**mall` breaks a contiguous substring match; so does a count-form
  negative (`0 want-decisions asked` where a regex demanded a negation phrase). Tolerate the markdown.
- **Never pin a single glyph.** A `❌` may land in the working doc rather than the response text.
- **Widen over wording or emphasis — NEVER over outcome.** If a red is the model expressing the right
  outcome differently, widen. If it is the model doing the wrong thing, that is the finding; fix the
  behaviour, not the token. Widening over outcome is how a suite goes quietly vacuous.
- **A new assertion passes 3× fresh before it counts green.** One green is a draw from a distribution.
- **Every regex reaches `grep` after `--`.** A regex starting with `-` (the fixtures assert on literal
  flags: `--tree`, `--no-reviewer`) is otherwise parsed as an option: `grep` exits 2, which reads as
  "no match" on `assert_contains`/`assert_all` and as "absent" on `assert_absent` — a permanent red on
  one side and a permanent silent green on the other. Four assertions were unpassable this way from
  the day they shipped.
- **Never pipe into a short-circuiting `grep`.** Under `set -o pipefail`, `grep -q` exits at the first
  match, the writer takes SIGPIPE and exits 141, and the caller reads a **present** token as missing —
  measured at 3.3% of evaluations on a 14.5 KB body and 100% on 250 KB. Use a herestring. `run.sh`
  carries a structural check that fails if the piped shape reappears.

## Dispatch-free self-tests (free coverage)

`run.sh` runs a set of self-tests that cost nothing and dispatch nothing. They are what keeps the
harness itself honest, and they run on every invocation — including one that selects no fixtures:

```bash
bash tests/eval/run.sh --only '^__none__$'    # every self-test, zero dispatches, zero cost
```

- **matcher-under-pipefail** — four counted assertions, judged through the shipped `assert_all` and
  `assert_contains` twenty times each against a 250 KB body, plus the structural check above. The
  defect is a race, so a check that ran once would have passed on the broken code about half the time.
- **assertion-convention** — every shared token proven **both** ways against synthetic transcripts: it
  must match the correct wording and still miss the wrong behaviour. A token that matches both is
  vacuous and fails here.
- **transcript-cache** — hash-match → cache-hit; hash-change → run fresh; `--no-cache` → all fresh.
- **isolation** — the live-checkout guard, the per-worker tree disposal guard, and the per-job clean
  start, each proven **non-vacuous** against an injected leak.
- **no-run detection** — an `API Error:` or empty body is not judgeable and fails loudly. Seven
  fixtures once never ran and three wrote PASS; that is what this exists to prevent.

## Where a run's results live

- `tests/eval/.transcripts/` — the full model transcript per job, cleared on every run (gitignored).
- `tests/eval/.archive/<run-id>/` — kept, never wiped, with an `IDENTITY.tsv` recording the runner
  fingerprint, plugin-tree fingerprint, model and CLI version that produced it.
- `tests/eval/.cache/` — one cached green transcript per fixture, keyed on the hash of the skill files
  that fixture reads. Wiped whenever `run.sh` itself changes (fail-safe: a coarse key can only err
  toward running fresh).

## Transcript cache

The cache stores a **transcript**, never a verdict, so an edited assertion does not invalidate it —
the transcript is re-judged from scratch on every reuse. Fixing a token in a passing fixture is
therefore free. It is fail-safe to run: an unhashable fixture, a `--no-cache` run, or any doubt runs
fresh. A fixture only mints a cache entry if it passed **all** of its own assertions and every
dispatch-free self-test passed too.

## History

`history/` holds the record of the 126-job behavioural suite retired in v1.16.0 — its status and
archive registers, the 24 harness defects it surfaced, and the one stored full run. It is kept because
deleting it invites someone to rebuild the same thing in a year. The short version: over its whole
life it produced 30 reds, **zero** of them mango behaving wrongly, and it never caught a cross-skill
regression.
