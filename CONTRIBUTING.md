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

## Skills are directive-only — put the "why" in the CHANGELOG, not the skill

Skill text is **runtime-loaded and IS behaviour** (prose-IS-behaviour), so every token of a `SKILL.md`
is paid on every ticket run. A `SKILL.md` therefore carries **directives only** — no rationale, no
"observed failure" war-stories, no historical justification. When a field lesson motivates a new rule:

- the **RULE** goes in the skill;
- the **REASON** goes in `plugins/mango/CHANGELOG.md`, and the incident itself (if a future maintainer
  needs it) in `plugins/mango/RATIONALE.md` — a file **no skill loads at runtime**.

`scripts/validate.py` enforces this (`validate_no_rationale_in_skills`): the build fails if a rationale
marker (`observed failure`, `field-observed`, `exists because`, `the reason …`, `historically`,
`war-story`, `retro-#N`) appears in any `plugins/mango/skills/*/SKILL.md`, and fails again if a skill
ever references `RATIONALE.md` (which would put the why back on the runtime path). See `PRINCIPLES.md`
→ *Skills are directive-only*.

**Trimming a skill is a behaviour change unless the removed text is provably non-behavioural.** The
test for any candidate cut: *"if I delete this, does any instruction, gate, condition, count, format,
or escalation disappear?"* If yes or unsure — **keep it**.

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

**Commit before you run it.** The fixtures execute against a `git clone` of this repo, i.e. **HEAD** —
an uncommitted skill edit is not in the sandbox, so a fixture for it fails against the old shipped text.
Commit locally first (pushing stays a separate, approved step), then run the suite and amend if needed.

It works with **either** an exported `ANTHROPIC_API_KEY` **or** an OAuth/subscription login
(`claude /login`) — the guard verifies the *capability* to run `claude -p`, not a specific credential.
The script sets up its own throwaway environment (an isolated clone + a temp `.harness.json` + a
minimal rule book), runs the fixtures against the **shipped** skills via `--plugin-dir`, and tears it
all down on exit — your working tree is never touched. It prints the `PASS`/`FAIL` lines and a final
`N/N assertions pass`, exiting non-zero on any failure.

Assertions match at the **decision level** and are **emphasis-agnostic** (tolerant of markdown and
phrasing variants around the load-bearing token), so a green result reflects stability across
independent fresh runs, not a regex tuned to one transcript.

**It dispatches in parallel.** `--workers N` (default a safe value; `--workers 8` is the milestone
setting, `--workers 1` the sequential debugging mode) runs the fixtures concurrently, each worker in
**its own throwaway clone** with **its own per-job `.harness.json`** — so a fixture that branches and
commits, or one that repoints `test_command`, cannot affect another in flight. Assertions are still
judged in script order, so the output reads like a sequential run. See
[`tests/eval/README.md`](./tests/eval/README.md) for the two-pass structure and the isolation guards.

**Verify-incremental (build discipline).** The suite is expensive, so while building a fix run only the
**affected fixture(s)** — `bash tests/eval/run.sh --only <regex>`, which reports the run as `PARTIAL`
and writes nothing to the cache; run the **full suite once** at the end before push. Coverage is
unchanged — only redundant mid-build re-runs are removed. The Finish bar is unchanged: **full suite
once** green, and each **new fixture 3× fresh** at the decision level.

The eval also runs a post-run **safety guard**: because every fixture executes inside a throwaway clone,
the guard asserts the **live checkout** is untouched afterwards (HEAD on `main`, no stray `PROJ-*` branch,
no leftover work doc), and it is self-tested against an injected leak so it can never pass vacuously.

## Publish

For a fresh fork or a new marketplace of your own:

1. Create the GitHub repo under your account.
2. `git remote add origin git@github.com:<user>/<repo>.git`
3. `git push -u origin main`
4. Users install with `/plugin marketplace add <user>/<repo>` then `/plugin install mango@<repo>`.

### Release checklist

Every release touches four places. Only the first two are validator-enforced, so the last two are the
ones that silently go stale — check them by hand:

1. **`plugins/mango/.claude-plugin/plugin.json`** — bump `version` (semver; enforced).
2. **`plugins/mango/CHANGELOG.md`** — add a `## [<version>]` entry. It ships *inside* the plugin,
   alongside `plugin.json` / `README.md`; `scripts/validate.py` fails if the entry is missing.
3. **Root `README.md` version badge** — `![version](…/badge/version-<version>-blue)`. **Not**
   enforced, and it is the *only* place the version appears in that README, so nothing else
   contradicts it when it drifts. It has silently sat two versions behind before.
4. **Root `README.md` → *Maturity*** — the "Field-proven on…" claims. Also not enforced, and they
   carry no version, so they never *look* stale. Re-read them for claims that have aged: usage,
   stacks, eval coverage, API stability.

Every claim in that blockquote must map to a repo source (API stability ↔ CHANGELOG, eval coverage ↔
`tests/eval/`). Maturity labels (**Stable** / **Experimental**) live only in
`plugins/mango/PRINCIPLES.md` → *Maturity* — the README no longer repeats them, so that section is the
single source and must stay current. A README that over- **or** under-claims is the same defect class
mango exists to prevent — a claim that does not match reality.

**Retro convention — read the CHANGELOG, not a prior retro.** An independent field retro reads
`plugins/mango/CHANGELOG.md` as the **neutral source** of "what changed this version" — never a previous
retro's write-up (which would compound one reviewer's framing). Keep each entry concise, evidence-first
(state what was observed and how many times, in plain words), and English-only. Use the
**Stable / Experimental** maturity vocabulary — never internal shorthand.
