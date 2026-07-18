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

Keep fixtures **generic** (`PROJ-*` keys; no real project, ticket, library, framework, formatter, or
brand). The suite's coverage is catalogued in the header comment of `run.sh`.
