# mango behavioural eval

`run.sh` is the **real behavioural check** for the mango skills. For each fixture ticket it drives
`claude -p` headless against the **shipped** skills (`--plugin-dir`) inside a throwaway, isolated clone
and asserts the transcript contains the expected load-bearing artifacts. The cheap, always-on guard is
`scripts/validate.py` (offline contract-token checks); this suite is the expensive, end-to-end one and
CI runs it only via the manual `eval.yml` workflow.

Run it (one command, hands-free — needs either `ANTHROPIC_API_KEY` or a `claude /login` session):

```
bash tests/eval/run.sh
```

The isolated clone — not a permission flag — is what guarantees a fixture can never touch the live
checkout; everything is torn down on exit.

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
invalidates every cache); editing `run.sh` itself invalidates the whole cache.

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

Two checks run each suite with **no `claude -p` dispatch**, so they cost nothing and are deterministic:

- **transcript-cache self-test** — hash-match → skip, hash-change → run, `--no-cache` → all run.
- **validator jargon-guard self-test** — injects each banned phrase (`v1 — …`, `enough to run and
  learn`, `n=1`, `v1-learning`) into a shipped operational file **inside the sandbox clone** and asserts
  `scripts/validate.py` **FAILS**, then that removal restores green. This is the teeth of the v1.7.5
  false-green fix: a validator that passes while its own claim is false is the worst defect class mango
  can ship, so this guard is proven by **injection**, never by assertion.

Prefer this shape for anything a deterministic check can prove — reserve `claude -p` fixtures for
behaviour only a model run can demonstrate.

Keep fixtures **generic** (`PROJ-*` keys; no real project, ticket, library, framework, formatter, or
brand). The suite's coverage is catalogued in the header comment of `run.sh`.
