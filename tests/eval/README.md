# mango behavioural eval

`run.sh` is the **real behavioural check** for the mango skills. For each fixture ticket it drives
`claude -p` headless against the **shipped** skills (`--plugin-dir`) inside a throwaway, isolated clone
and asserts the transcript contains the expected load-bearing artifacts. The cheap, always-on guard is
`scripts/validate.py` (offline contract-token checks); this suite is the expensive, end-to-end one and
CI runs it only via the manual `eval.yml` workflow.

Run it (one command, hands-free — needs either `ANTHROPIC_API_KEY` or a `claude /login` session):

```
bash tests/eval/run.sh                   # default workers, cache on
bash tests/eval/run.sh --workers 8       # milestone speed
bash tests/eval/run.sh --workers 1       # sequential — debugging one transcript
bash tests/eval/run.sh --only refine-    # dev loop: affected fixtures only (PARTIAL run)
```

The isolated clone — not a permission flag — is what guarantees a fixture can never touch the live
checkout; everything is torn down on exit.

> **The eval runs against the COMMITTED tree.** Each worker's sandbox is a `git clone` of this repo, so
> it holds **HEAD**, not your working tree: an **uncommitted** skill edit is invisible to every fixture,
> and a fixture asserting the new behaviour will fail while the skills the model actually loaded are the
> old ones. **Commit first** (locally — pushing is separate), then run the suite; amend if it comes back
> red. A model that greps the sandbox will say so plainly — one v1.8.0 fixture run reported "there is no
> premise check in mango's refine phase", which was exactly true of HEAD at that moment.

> **The throwaway project declares its tickets synthetic.** The sandbox is a clone of *this* repo, which
> ships **no application source**, so a fixture ticket about a hypothetical app names sources that can
> never resolve — and `refine`'s premise check would halt every one of them. The generated
> `docs/EVAL_RULES.md` therefore declares the project's tickets **synthetic**, which is the premise
> check's own documented carve-out, stated once for the whole environment instead of in every fixture. The
> two `premise-*` fixtures opt back in by stating that their references are claims about this checkout —
> which is a real ticket's default — so the check is still exercised both ways: it fires and halts on a
> missing named identifier, and stays silent on a to-be-created path.

## Parallel dispatch (where the wall-time went)

A full instrumented run measured the suite at **100% `claude -p` latency**: harness overhead (clone,
sandbox, every grep, all the dispatch-free self-tests) was **~3 s of a 10 590 s run — 0.03%**. So the
only levers are fewer dispatches and *concurrent* dispatches, and concurrency is the whole win:
`--workers 8` **measures 998 s – 1201 s (16.6 – 20 min) over five full runs**, against 2 h 56 m
sequential — 8.8× to 10.6×, an order of magnitude more than every available fixture merge combined.

`run.sh` therefore runs the suite body **twice** over the same code:

1. **collect** — every `run_fixture` / `run_prompt` **registers** a dispatch job (its prompt plus the
   `.harness.json` `test_command` in force at that line); every `assert_*` is a no-op.
2. **dispatch** — the jobs run across `--workers N` workers, longest-first, each worker claiming jobs
   from a shared queue by atomic `mkdir`.
3. **assert** — the same call sites resolve the transcripts the dispatch produced and judge them, in
   script order, so a parallel run's output reads exactly like a sequential one.

Registering and asserting at the *same call site* is what keeps a prompt from drifting away from the
assertions that judge it. An assertion whose dispatch was never registered **FAILS loudly**
(`NO TRANSCRIPT`) rather than reading as coverage.

**Per-worker isolation is mandatory, and asserted.** Each worker gets its own
`git clone --local --no-hardlinks` and writes its own `.harness.json` **per job**. Both hazards this
removes are real: fixtures whose `execute` branches and commits would race inside one shared clone, and
`red-baseline` repoints `config.test_command`, which under concurrency would flip the harness under
another in-flight dispatch. After the run, one assertion proves every worker tree was disposed (proven
non-vacuous against an undisposed tree) alongside the existing live-checkout guard.

`--only <regex>` filters both the dispatch and the judging. It is a **dev-loop** tool: the run is
reported `PARTIAL`, its skipped assertions are counted, and **no cache entry is written** — a cache
green may only ever be minted by a run that proved the whole suite. CI passes no arguments.

## Assertion convention (standing — practised since v1.0, written down here)

A model's wording varies run to run; the **decision** does not. Every new assertion must therefore be
written to match the *behaviour*, not one transcript's phrasing. The standing rules:

1. **Match the decision, not one phrasing.** Assert the load-bearing **outcome + its reasoning token**
   (use `assert_all` to require both), so a correct decision passes under any wording and a wrong
   *outcome* — which drops one of the tokens — still fails. Never pin an assertion to a sentence you
   saw in one run.
2. **Be emphasis-agnostic.** Tolerate markdown emphasis (`**`, `_`) and spacing/hyphenation variants
   around the token (e.g. `dispatch[ -]count`, `re-?dispatch`). A correct answer wrapped in `**bold**`
   must still match.
3. **Pass 3× fresh before it counts as green.** A new assertion is only "green" once it passes on
   **three independent fresh runs** at the decision level — proving stability across runs, not a regex
   tuned to a single transcript.
4. **Widen over wording/emphasis — never over outcome.** When an assertion misses a *correct* run,
   widen it over phrasing or emphasis only. **Never** widen it so that a *wrong* outcome would also
   pass — that turns a green into a false green. (v1.4's `rtk-wire` fixture legitimately needed widening
   over wording twice; that is the allowed kind of widening.)
5. **Never pin a single glyph, and expect emphasis *inside* a word.** A `❌` may be written into the
   working-doc table rather than the response text, and `**S**mall` / `**I**ndependent` break a
   contiguous substring match — as do `**before**` the gate and `**before**` the first child branch. Use
   the shared `RE_*` tokens at the top of `run.sh` (`RE_INVEST_LETTERS`, `RE_INVEST_SMALL`,
   `RE_NOT_SPLIT`, `RE_ZERO_WANTS`, `RE_LAYER_MISMATCH`, `RE_BEFORE_CHILD`, `RE_BEFORE_GATE`,
   `RE_NO_BLANKET_RERUN`) — each is proven **both ways** by the assertion-convention self-test below, and
   `scripts/validate.py` fails the build if an assertion regex is a bare glyph again.
6. **Never put a bare literal separator between two load-bearing words.** A space in the regex cannot
   match `**not** split`, and a space cannot match a hyphen (`no change` vs `no-change`). Write the
   separator as a class: `not[*_ ]{1,6}split`, `no[ -]change`. This single class caused most of v1.8.0's
   assertion failures, every one of them on demonstrably correct behaviour.
7. **A negative may be stated as a count.** A skill emits `0 want-decisions asked` as readily as "did
   not ask", so an assertion demanding a negation phrase fails on correct behaviour. Accept the
   zero-count form (`RE_ZERO_WANTS`).

## Verify-incremental (build discipline — the Finish flow)

The full suite is expensive (a `claude -p` run per assertion). While **building a fix**, run only the
**affected fixture(s)** — the one or two behaviours the change touches — not the whole suite after every
small edit. Run the **full suite once** at the end, before push. Coverage is unchanged; only the
redundant mid-build re-runs are removed.

The v1.0 green bar is intact and non-negotiable at Finish:

- **full suite once** at the end, green; and
- **each new fixture 3× fresh** (three independent runs, green at the decision level — see rule 3 above).

So: affected-fixture-only during the build, **full suite once** at the end, 3-fresh for anything new.

## Transcript cache (dev-loop speed — never drops coverage)

The runner caches each fixture's last **GREEN** transcript keyed on `(fixture-id + skills-hash)`. On a
run, a fixture whose exercised skill files are **provably unchanged** is a **cache-hit** — its cached
green transcript is reused and **no `claude -p` is dispatched**; a fixture whose skills-hash changed (or
any uncertainty — missing cache, unreadable hash, changed runner) runs **fresh**. The cache is
**fail-safe to run**: it only ever avoids a re-run it can prove unnecessary (skills unchanged ⇒ behaviour
unchanged — the same prose-is-behaviour invariant mango relies on), and it **never** drops a fixture from
coverage. `PRINCIPLES.md`, every agent brief, and every template are always in the hash (a change to any
invalidates every cache); editing `run.sh` itself invalidates the whole cache. `RATIONALE.md` is
deliberately **not** in the hash — no skill loads it, so it cannot change behaviour and must never
invalidate a cache.

```
bash tests/eval/run.sh              # dev loop: cache-hits for unchanged fixtures
bash tests/eval/run.sh --no-cache   # milestone/release: every fixture dispatches fresh
```

**`--no-cache` forces a full fresh run** — this is the milestone/release bar. The cache accelerates the
dev loop; it does **not** replace a true full suite at a milestone. The final line reports `cache-hit(s)`
vs `fresh run(s)`. The cache lives outside the committed tree (`tests/eval/.cache/`, git-ignored) and is
never committed. A runner **self-test** (no `claude -p`) asserts the three guarantees each run: hash-match
→ skip, hash-change → run, `--no-cache` → all run.

The hit/fresh tallies live in **ledger files**, not shell variables: every fixture is invoked as
`t="$(run_fixture …)"` — a command substitution, i.e. a subshell — so a `VAR=$((VAR+1))` inside
`run_fixture` is discarded when that subshell exits. That once lost both the printed counters *and* the
fresh-fixture list the end-of-run cache **write** iterates, so nothing was ever cached (v1.7.5 Fix 4).
Any new per-fixture tally must use the same ledger pattern.

## Dispatch-less self-tests (free coverage)

These checks run each suite with **no `claude -p` dispatch**, so they cost nothing and are
deterministic:

- **transcript-cache self-test** — hash-match → skip, hash-change → run, `--no-cache` → all run.
- **assertion-convention self-test** — every widened `RE_*` token is judged against two synthetic
  transcripts: it must **match** the correct wording that used to fail it and still **miss** the wrong
  behaviour. A token that matches the wrong transcript fails as `VACUOUS`; one that misses the correct
  transcript fails as still brittle. This is what makes "widen over wording, never over outcome"
  checkable instead of a promise.
- **per-worker-isolation guard** — every worker clone the parallel dispatcher created was disposed and
  is gone from disk, proven non-vacuous against a synthetic undisposed tree.
- **validator jargon-guard self-test** — injects each banned phrase (`v1 — …`, `enough to run and
  learn`, `n=1`, `v1-learning`) into a shipped operational file **inside the sandbox clone** and asserts
  `scripts/validate.py` **FAILS**, then that removal restores green. This is the teeth of the v1.7.5
  false-green fix: a validator that passes while its own claim is false is the worst defect class mango
  can ship, so this guard is proven by **injection**, never by assertion.
- **validator no-rationale-guard self-test** — injects a rationale marker (an `(Observed failure: …)` /
  `(Field-observed: …)` war-story, an `exists because` justification, a `Historically …` note) into a
  runtime `SKILL.md` and asserts `validate.py` **FAILS**; also asserts that a `SKILL.md` referencing
  `RATIONALE.md` fails, so the "why" can never be pulled back onto the runtime path. Teeth for the
  v1.7.6 *skills are directive-only* rule — same injection discipline as the jargon guard.

Prefer this shape for anything a deterministic check can prove — reserve `claude -p` fixtures for
behaviour only a model run can demonstrate. A change that is a **pure deletion of non-behavioural
text** — no directive reworded — is proven by `validate.py` plus a marker audit of the deleted
segments; it needs no fresh fixture run, because the existing fixtures are already the regression net
for every gate it left untouched.

Keep fixtures **generic** (`PROJ-*` keys; no real project, ticket, library, framework, formatter, or
brand). The suite's coverage is catalogued in the header comment of `run.sh`.
