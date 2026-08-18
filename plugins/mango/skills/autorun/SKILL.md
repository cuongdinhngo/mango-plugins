---
name: autorun
description: Runs the existing mango lifecycle UNATTENDED and stops at the PR. Use when a ticket is handed over for an overnight run — it invokes refine → analysis → design → execute → review → finalise and closes each gate from the artifacts those phases already emit, instead of waiting for a human to type "go". Never merges. Writes a RUN CONTRACT before starting, a harness-run RECONCILE at t0 and at close, and a DISCLOSURE list read first in the morning.
---

**`<mango>` = this plugin's root:** `${CLAUDE_PLUGIN_ROOT}` when the host sets it, else the plugin root
this skill file sits in, else a read-only search for a directory holding `PRINCIPLES.md` and
`.claude-plugin/plugin.json` — **more than one hit → take the HIGHEST `version` in its `plugin.json`
(semver compare, never `find` order, never a lexicographic sort) and report the candidate count** —
never a hardcoded path. Unresolvable → say so and use the inline fallback
named at the point of use (`<mango>/PRINCIPLES.md`, *Resolving a mango-shipped path*).

Operate under `<mango>/PRINCIPLES.md`. This skill orchestrates the same four principles `solve` does. It
**does not reimplement any phase** — it invokes `refine`, `analysis`, `design`, `execute`, `review` and
`finalise` and reads their counted artifacts.

**Ground rules.** Read `${CLAUDE_PROJECT_DIR}/.harness.json` first. If it is missing, STOP and tell the
user to create one from `<mango>/config/harness.example.json`. Run the `doctor` checks and **refuse to
start** while any ❌ remains.

## What this changes, stated plainly

**No gate is removed.** Gates 0–4 all still run, including the review seat. What is removed is the
operator sitting at the keyboard to acknowledge each one. **Five waits for a human become one, and that
one is the merge.**

**There is no auto-merge in this skill.** The run stops when the PR exists. `autorun` never merges,
never force-pushes, never deploys, and never writes to shared state beyond the two outward actions the
operator pre-authorised at handover.

## Usage

```
/mango:autorun <KEY>                    # the challenger runs (default)
/mango:autorun <KEY> --no-challenger    # the challenger is waived, and DISCLOSURE says so first
```

### Handover authorisation (required — take it before anything else)

`autorun` performs two outward actions with nobody awake: **push the feature branch** and **open the
PR**. Take **one explicit authorisation naming exactly those two actions** before the run starts, and
record it verbatim in the `RUN CONTRACT`'s **`handover-authorisation`** header field. The contract
script holds that field: a contract with the field **empty or absent does not parse, and the run does
not start** — the run must not begin without the authorisation it claims to have. That authorisation
covers **only** those two, **only** on this ticket's branch. It is not a blanket "go": every other
outward action — a merge, a deploy, a tracker transition, a force-push, a write to any shared ref other
than this branch — is on the abort list below and STOPS the run. Silence is never that authorisation.

## Step 0 — the RUN CONTRACT, written by a script and parsed back

Before any phase runs, build the contract with `<mango>/scripts/run_contract.py`:

```
python3 <mango>/scripts/run_contract.py write <spec.json> --repo <repo> > .mango/run-contract-<KEY>.txt
python3 <mango>/scripts/run_contract.py validate .mango/run-contract-<KEY>.txt --phase t0
```

**If it does not parse, the run does not start.** The script — not you — decides that.

- **Every condition declares a `force-broken` and a `force-holding` case as mandatory grammar fields.**
  A condition missing either does not parse, so an unforceable condition never reaches `RECONCILE` to be
  counted. A predicate never shown to fail is not evidence when it holds; a predicate never shown to
  hold on a clean run is a false-red waiting to happen.
- **Derive every derivable value with a command.** Put the command in `derived-by:` and let the script
  run it and record its real output. Anything you cannot derive is marked `agent-claim (unchecked)` and
  is carried into `DISCLOSURE`. **The contract's guarantee is *well-formed and internally consistent*,
  never *true*** — machine-writing guarantees the grammar, not the values. Do not state a count you did
  not run a command to get.
- **Record the resolved plugin version and path** (`plugin-version`, `plugin-path`). An in-session
  plugin update does not re-resolve the slash-command root, so an overnight run must be able to answer
  "which version did this?".
- **Two-phase binding.** A condition that depends on the change cannot exist at t0 — the tree comparison
  needs the change list, the proving-test command needs the test name. Write those as
  `UNBOUND ${PLACEHOLDER}` and bind them at **Gate 2**:

  ```
  python3 <mango>/scripts/run_contract.py bind <contract> TEST_CMD="<the proving test>" \
      --phase gate2 --out <contract>
  ```

  The bind pass **re-validates and refuses any surviving `UNBOUND`**.

### The fixed floor — three conditions you may not author

The script ships them and refuses a contract that drops, renames, or re-origins any of them:

1. **`PR-EXISTS`** — the PR exists and its state is readable. It carries a real command; `RECONCILE`
   runs it, and your word that the PR exists is not the condition.
2. **`TREE-COMPARISON`** — a **tree** comparison, never a content grep:
   `git diff --quiet <base> <branch> -- <paths>`. A grep looks for content named at t0, and a
   post-merge correction is unnamed then, so a grep returns `HOLDING` on precisely the incident this
   catches. An **ancestry predicate** (`git merge-base --is-ancestor`) is a false-red under a squash
   merge and is refused at contract time.
3. **`LOCAL-HEAD-PUSHED`** — nothing is stranded on this machine: the local branch head equals the
   remote's. Resolve each ref with `git rev-parse --verify` **before** comparing — when both lookups
   fail, a bare `test "$(…)" = "$(…)"` compares empty to empty and reports `HOLDING`. Live for the whole
   run, not only after a merge.

### Merge-strategy detection

Read it from **recent first-parent topology** — the commits between the newest merge commit on the
default branch and its tip:

```
python3 <mango>/scripts/reconcile.py merge-strategy --repo <repo> --base <base>
```

**Never** the host's allowed-strategy flags (they say what is *permitted*, never what is *used*) and
**never** a whole-history merge count (which returns the pre-change answer when a repo switched strategy
mid-history, in the dangerous direction). State in the run's output that this **narrows the judgement
rather than removing it**: a direct commit to the default branch looks the same as a squash merge.

## Step 1 — RECONCILE at t0, before any work exists

```
python3 <mango>/scripts/reconcile.py run <contract> --phase t0 --repo <repo>
```

Every **bound** condition should be in its **failing** state against the real world here. A condition
that reports `HOLDING` on an empty run is describing something other than this run's work: the script
strikes it and the run does not start until it is replaced. One command, about two seconds.

## Step 2 — run the lifecycle, closing each gate on artifacts

Invoke the phases in the same order `solve` does — `refine` → `analysis` → `design` → `execute` →
`review` → `finalise` — honouring `TIER` (a `TIER: lite` ticket routes through `quick` exactly as under
`solve`). Close each gate **from the artifact the phase already emitted**. Invent no new gate condition:

| Gate | Closes when |
|---|---|
| 0 | `CLARIFICATION: … j = 0` — and `j` **includes any unresolved `refine` want-decision** (see below) |
| 1 | `SECTIONS` found = decomposed · `RULE SECTIONS` every applicable section checked or N/A-with-reason · `BASELINE` captured |
| 2 | `HANDLES: u = 0` and `h == t + x` · the verification plan carries no `❌` (or every `❌` is a recorded, human-approved exclusion carrying a checkable `expiry:`) · `EXCLUSIONS: e == n`, no third-occurrence class silently re-recorded · the proving test is named and runnable |
| 3 | execute's verification sweep · `diff ⊆ approved list` · the design-conformance self-check |
| 4 | the reviewer verdict is `LGTM`, or a conditional LGTM whose named findings have landed |

**Read the artifact against its shipped grammar and let the match decide. Do not announce that a gate
passed.** Reading your own counted line and declaring it satisfied is the adherence defect this whole
lane works around. **If the line does not parse against the shipped grammar, the gate does not close** —
a line that is *narrated* rather than emitted, that carries a count contradicting its own row list, or
that names an artifact mango does not produce, is a **non-closing** gate. Stop and report it as such;
never repair it by re-typing the line yourself.

### `j > 0` stops the run until morning

A clarification for human decision is not something to guess at 03:00. **`j > 0` stops the run.**

**`j` includes an unresolved `refine` want-decision.** `refine` may raise a **want-decision** — a
product/intent question only the user can answer. Attended, the user answers it; unattended, nobody is
awake to. An unanswered want-decision is **not** silently adopted as an `ASSUMED` (that would ship a PR
on an unratified assumption with `j` still `0`): it is an **unresolved clarification**, so it **counts
toward `j`**, and the `j > 0` rule above stops the run. A ticket `refine` **self-skipped** on (fully
locked, nothing to expose → `REFINE: … skip: yes`, `a = 0`) raises no want-decision and leaves `j`
untouched — the self-skip is correct behaviour and is preserved; the fix is the routing of an
*unresolved* want-decision, not `refine`'s judgement.

**Stopping is not dying.** Finish every part that does not depend on the answer, then report precisely
what is missing with the open question stated verbatim. The operator wakes to a run that got as far as
it honestly could.

### Abort list — stop and report

- credentials or auth;
- a write to shared state beyond the pre-authorised branch push and PR-open: a shared DB, a deploy, a
  merge, a force-push, a tracker transition;
- a rule conflict needing a policy decision;
- **the fix turns out to be a product decision**;
- a gate still red after three honest attempts.

On any of these: finish every unaffected part, write `RECONCILE` and `DISCLOSURE`, and stop.

## Step 3 — the challenger flag

**Default: the challenger runs.** `--no-challenger` turns it off explicitly. It is an argument rather
than an improvised instruction, so the choice is recorded rather than remembered. Pass the flag through
to `review` — `review` owns the single challenger-dispatch decision and this skill adds no parallel one.

**A disabled challenger is the FIRST LINE of `DISCLOSURE`.** At `solve` the operator types the flag and
remembers it. At `autorun` they typed it at 23:00 and read the PR at 08:00, and a clean result is
uninterpretable without knowing whether anything independent looked at it. Record the flag state in the
`RUN CONTRACT` too, so a later comparison across runs is possible: *do runs with the challenger have
fewer defects reaching the PR?*

## Step 4 — token budget, because the operator is asleep

Running out mid-run leaves a half-finished branch nobody is awake to rescue. That is worse than
finishing without a subagent.

**Budget by the proxy the harness can count: call count.** mango's ledger measures **subagent dispatch
only**, so main-loop spend — the larger term — is invisible to the harness at runtime on at least one
host, and a check gating on "remaining tokens" cannot see what is actually being spent. Say so plainly:
**a call-count ceiling is a proxy, not a measurement.**

At t0, record in the `RUN CONTRACT` a **call-count ceiling** and the **per-call estimate** used to
derive it, both traceable to this project's ledger history for this tier:

```
python3 <mango>/scripts/budget.py ceiling --rows "<fresh>/<calls>,…" --budget <tokens>
python3 <mango>/scripts/budget.py check --ceiling <n|unknown> --calls <n> --projected <n> --at t0
```

Where the host **does** surface usage, record the token budget too and prefer it. **No ledger history
for this tier → the ceiling is `unknown`: record it as unknown, do not block, do not invent a number.**
Track calls during the run; approaching the ceiling triggers the ladder below — **never** a mid-phase
death, and an estimate already over the ceiling is reported **at t0**, not discovered mid-run.

### Degradation ladder — a declared choice, not a surprise

Ordered by measured cost against measured value. `python3 <mango>/scripts/budget.py ladder` prints it.

1. **Reduce main-loop work first** — narrow the scope, drop optional exploration fan-out, stop at the
   smallest complete change list. This is roughly 90% of run cost and the only lever that matters at
   scale.
2. **Challenger** — about 58k per run. Cheapest thing to lose, and it saves little; skipping it is a
   **disclosure** event more than a budget one.
3. **The review seat degrades in three steps, and never to zero:**

   | Step | What it is | Cost per round | Grounds findings in the rule book? |
   |---|---|---|---|
   | `reviewer-max` | mango agent, Opus | — | yes |
   | `reviewer` | mango agent, Sonnet | about 108k | yes — every finding cites the violated section |
   | the host's native `/code-review` on the PR | **not a mango skill** | about 62k | **no** — it does not read `.harness.json`, so it does not know the project has a rule book |

   The third step is **not a smaller version of the second**: it trades rule-book coverage for cost,
   checking general standards rather than this project's codified rules. **Record which step ran in
   `DISCLOSURE`** — a run reviewed by the native command is not a run reviewed against the rule book.

**Never degrade the review seat away.** A degraded run without a review is not a cheaper run; it is a
run whose defects are found later by the operator. **Never degrade the envelope** — it is a small
fraction of run cost and the only thing watching outside the diff.

A degraded run still completes and still reports. **Every degradation is recorded in `DISCLOSURE`** —
scaling down is an event, not a silence.

## Step 5 — finalise, push, open the PR, then RECONCILE at close

Run `finalise` as usual — the stale-review guard, the PR body, the cost-ledger completeness gate, the
durable lesson and the learning loop all run unchanged. Its per-action approval is satisfied **only**
for the two actions the handover authorisation named (push the branch, open the PR) and for nothing
else; every other enumerated action is deferred to the morning and listed in `DISCLOSURE`.

Then, **after the last push**:

```
python3 <mango>/scripts/reconcile.py run <contract> --phase close --repo <repo> --prove
```

**The harness runs the commands; you read the verdict.** Do not run the checks yourself and type the
output — transcribe the two counted lines the script printed:

```
RECONCILE
  conditions: <n> declared | <m> re-run | <p> holding | <q> BROKEN | <u> UNBOUND | <c> could-not-run
  proven    : <b> shown BROKEN when forced | <h> shown HOLDING on a clean run
```

`--prove` is the **forced-case positive control**: each condition must be observed to FLIP —
`force-holding` produces `HOLDING`, then `force-broken` produces `BROKEN`. A case that does not flip is
reported `FORCE-UNPROVEN` and **is not counted**, because a mutation that silently did not apply reports
a green that means nothing.

**`could-not-run` is a third state**, distinct from `HOLDING` and `BROKEN`: the check's named shell
(`bash`) was not on PATH, so the check did not run at all. **A check that cannot run never reports
holding** — it is `UNVERIFIED`, counted on its own axis, and re-run where the shell exists. A conditions
line with `c > 0` at close means those floor conditions were **not verified**, not that they hold.

**`q > 0` does not block a merge** — this version stops at the PR and the human merges. It means **read
this first**.

## Step 6 — DISCLOSURE

Seed it from the contract, then append:

```
python3 <mango>/scripts/run_contract.py disclosure-seed <contract>
```

The seed carries line one (the challenger flag state), every unchecked agent claim from the contract,
and the budget line. Append to it everything mango already produces as raw material: coverage-gap
exclusions, every `unmeasured` ledger cell, baseline exclusions, recorded design deviations, unexercised
paths, every degradation taken from the ladder, which review step ran, and every outward action deferred
to the morning.

**This is the one artifact nothing can check.** Only you know what you chose not to verify, so it is the
weakest thing in the run — say so in the output. **A near-empty disclosure list on a long run is a
reason to distrust the run, not to trust it.**

## Non-negotiables

- **No auto-merge, ever, in this skill.** The run stops when the PR exists.
- **No gate is removed** — including the review seat, at any budget.
- **The harness decides a gate, not the agent's announcement.** A counted line that does not parse
  against its shipped grammar does not close its gate.
- **Never repair a counted line by re-typing it.** Report it as non-closing.
- **Never invent a number** — not a token count, not a ceiling, not a condition's value. `unknown` and
  `unmeasured (<reason>)` are correct answers; a plausible figure is a false-green.
- **One ticket per run**, and `finalise`'s outward actions stay limited to the two the handover
  authorisation named.
- **Lessons never modify mango.** A phase that demonstrably skipped a doable check is a type-3
  skill-gap **signal** in `config.skill_gap_path`, exactly as under `solve`.
