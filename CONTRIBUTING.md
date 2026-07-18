# Contributing to mango-plugins

This repo is a Claude Code **marketplace** whose root *is* the marketplace; the `mango` plugin lives
in [`plugins/mango/`](./plugins/mango). This doc covers developing, validating, and publishing it.
For using mango, see the [marketplace README](./README.md) and the
[plugin README](./plugins/mango/README.md).

## Validate locally

The required gate is deterministic, stdlib-only, and needs no network or auth:

```
python3 scripts/validate.py
```

It runs structural checks plus per-skill contract tokens (it fails if a skill loses its load-bearing
artifact). CI (`.github/workflows/validate.yml`, on every push/PR) runs the same script, then
`claude plugin validate ./plugins/mango --strict` and `claude plugin validate . --strict` as a
**best-effort, non-blocking** step.

## Behavioural eval

The behavioural eval (`tests/eval/run.sh`) drives the model over fixture tickets (one per behaviour,
so a red run is diagnosable) and asserts the expected artifacts — the analysis happy path plus the
behaviours that matter most: proof at the risk layer, the ticket-blind challenger catching an unmet
AC, the design-invalidated escalation, the stuck-detector, the frontend surface-coverage and
layer-match gates, the cost-ledger completeness gate, and the verify-only re-review.

It costs tokens, so CI runs it only via the manual `eval.yml` workflow (`workflow_dispatch`, needs the
`ANTHROPIC_API_KEY` secret). Run it yourself with one command from a fresh clone:

```
bash tests/eval/run.sh
```

It works with **either** an exported `ANTHROPIC_API_KEY` **or** an OAuth/subscription login
(`claude /login`) — the guard verifies the *capability* to run `claude -p`, not a specific credential.
The script sets up its own throwaway environment (an isolated clone + a temp `.harness.json` + a
minimal rule book), runs the fixtures against the **shipped** skills via `--plugin-dir`, and tears it
all down on exit — your working tree is never touched. It prints the `PASS`/`FAIL` lines and a final
`N/N assertions pass`, exiting non-zero on any failure.

Assertions match at the **decision level** and are **emphasis-agnostic** (tolerant of markdown and
phrasing variants around the load-bearing token), so a green result reflects stability across
independent fresh runs, not a regex tuned to one transcript.

**Verify-incremental (build discipline).** The suite is expensive, so while building a fix run only the
**affected fixture(s)**; run the **full suite once** at the end before push. Coverage is unchanged — only
redundant mid-build re-runs are removed. The Finish bar is unchanged: **full suite once** green, and each
**new fixture 3× fresh** at the decision level.

The eval also runs a post-run **safety guard**: because every fixture executes inside a throwaway clone,
the guard asserts the **live checkout** is untouched afterwards (HEAD on `main`, no stray `PROJ-*` branch,
no leftover work doc), and it is self-tested against an injected leak so it can never pass vacuously.

## Publish

For a fresh fork or a new marketplace of your own:

1. Create the GitHub repo under your account.
2. `git remote add origin git@github.com:<user>/<repo>.git`
3. `git push -u origin main`
4. Users install with `/plugin marketplace add <user>/<repo>` then `/plugin install mango@<repo>`.

Bump the version in `plugins/mango/.claude-plugin/plugin.json` and add an entry to the **shipped
CHANGELOG** at `plugins/mango/CHANGELOG.md` (it ships *inside* the plugin, alongside `plugin.json` /
`README.md`) for every release; `scripts/validate.py` enforces semver on the manifest **and** that the
shipped CHANGELOG carries an entry matching the manifest version.

**Retro convention — read the CHANGELOG, not a prior retro.** An independent field retro reads
`plugins/mango/CHANGELOG.md` as the **neutral source** of "what changed this version" — never a previous
retro's write-up (which would compound one reviewer's framing). Keep each entry concise, evidence-first
(what was observed, `n=`), and English-only.
