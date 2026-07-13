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

Keep fixtures **generic** (`PROJ-*` keys; no real project, ticket, library, framework, formatter, or
brand). The suite's coverage is catalogued in the header comment of `run.sh`.
