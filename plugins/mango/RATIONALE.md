# RATIONALE.md — the "why" behind the rules, off the runtime path

**This file is not loaded at runtime.** No `SKILL.md`, agent brief, or template references it, and
nothing should ever make one do so — that would put the "why" back on the path a skill pays for on
every ticket run.

Per `PRINCIPLES.md` ("Skills are directive-only"), a `SKILL.md` carries **directives only**. When a
field incident motivates a rule, the **rule** goes in the skill and the **reason** goes here (and in
`CHANGELOG.md`, which records which version shipped the rule). Every entry below was removed verbatim
from a skill in **v1.7.6**; the rule each one motivated is still in force in the file named.

Nothing here is normative. If this file and a `SKILL.md` ever disagree, the `SKILL.md` wins.

---

## analysis — why the raw ticket must stay above the separator

**Rule (still in `skills/analysis/SKILL.md`, step 2):** the raw ticket portion stays above the
separator line and the working doc below it; never mix design/matrix/rationale into the raw ticket.

**Observed failure (pre-v0.3):** when the ticket file doubled as the working doc with no separator,
the challenger's independence rested on a manual "withhold" convention rather than on structure.

---

## design — why an unresolved `novel-untested` assumption blocks Gate 2

**Rule (`skills/design/SKILL.md`, step 3):** a `novel-untested` third-party/runtime assumption must be
de-risked by a spike or an integration-shaped proving test; Gate 2 may not pass with one unresolved.

**Observed failure:** a design leaned on an untested "two live rich-text editors coexist" assumption —
the exact thing that broke — because nothing forced de-risking a novel runtime assumption.

## design — why the blast radius must trace real producers/consumers

**Rule (`skills/design/SKILL.md`, step 4):** trace to real producers/consumers — grep a shared type by
name *and* its factory/fixture patterns across **every** test root, run `typecheck`, and enumerate
**every** builder call site. A shallow-grep-only estimate that misses a known consumer is a Gate-2
finding.

**Observed failures:** a change reworded a heading an existing shell test asserted and the change list
never mentioned it; a migration/type change missed the type factories across all test roots; a
data-fan-in change missed the actual builder call sites — each surfaced only as an execute deviation.

## design — why the layer-match is a hard gate

**Rule (`skills/design/SKILL.md`, step 6):** a proof artifact below its AC's risk layer is a
layer-match `❌` and blocks Gate 2 unless upgraded or recorded as a human-approved coverage-gap
exclusion.

**Observed failures:** a named proving test was a store unit test that mocked the integration layer, so
it stayed green while the real integration-layer behaviour was broken; separately, an "in-browser
confirm" acceptance criterion had no planned proof and surfaced only at Gate 4. And: a requirement
whose real risk sat at an integration/behavioural tier was only unit-proven, so the challenger's later
"not met" read as a hard failure when it was a proof-tier mismatch that should have been a recorded
exclusion.

---

## execute — why every clause of a multi-clause M-gate needs its own assertion

**Rule (`skills/execute/SKILL.md`, "One assertion PER CLAUSE"):** one proof-manifest row per clause; a
clause with no assertion blocks the gate exactly as a missing surface does.

**Observed failure:** an M4 proof asserted only the size clause and shipped green while a real 0 px-gap
spacing failure went unproven — the reviewer had to catch it by measuring the DOM.

## execute — why "design invalidated" re-opens Gate 2

**Rule (`skills/execute/SKILL.md`, Escalations):** when a test proves the approved Gate-2 approach
cannot work, STOP, record the finding, and re-open Gate 2 with a revised approach.

**Observed failure:** execute discovered a Gate-2 "reuse the per-tab mounting for two panes" design was
unworkable; mango had no defined transition, so the operator had to improvise stop → ask → re-approve.

## execute — why the stuck-detector has a threshold

**Rule (`skills/execute/SKILL.md`, Escalations):** after `config.stuck_threshold` failed attempts
against the same failing signature, STOP and escalate; the counter resets when the signature changes.

**Observed failure:** ~7 attempts ran against the same failing e2e before anyone escalated; nothing
bounded repeated attempts at one proof.

---

## finalise — why the durable lesson is asked for on every run

**Rule (`skills/finalise/SKILL.md`, step 8):** ask for a durable lesson on **every** run, independent of
deferred (⚠) rows, and write it to `config.lessons_path` as a repo artifact.

**Observed failure:** a run discovered a durable constraint — two live rich-text editors corrupt each
other — but had no deferred rows, so it nearly never reached the repo's shared `LESSONS.md`.

## finalise — why the lesson must land on a shared ref

**Rule (`skills/finalise/SKILL.md`, step 8):** the durable-lesson / bookkeeping write reaches a shared
ref either folded into the approved branch-push before PR-open, or as its own enumerated "push
bookkeeping" outward action.

**Observed failure (#12):** the lesson/BACKLOG write rode a branch never pushed before the human merged
the PR, so the lesson never reached `main`.

---

## breakdown — why the epic scaffold is committed before any child branches

**Rule (`skills/breakdown/SKILL.md`, step 6):** commit the child stubs + epic BACKLOG to a shared ref
before any child ticket starts its own branch.

**Field-observed:** the scaffold was created but **not committed**, so a later child's challenger could
not distinguish a genuine retarget-edit from net-new authorship and had to caveat.

## breakdown — why a changed split must be re-ratified

**Rule (`skills/breakdown/SKILL.md`, step 7, Experimental):** if the ticket list changes after the
split-gate, surface the delta as a counted artifact and get an explicit human re-approve at the
breakdown level.

**Field-observed:** after the split ratified, the epic gained a 7th ticket and reversed a
previously-ratified decision — both rode in on a child's Gate 1 with no breakdown-level re-approval.

---

## refine — why the acceptance bar is a want-decision

**Rule (`skills/refine/SKILL.md`, step 2 tie-breaker (a)):** a decision about the acceptance BAR is a
want-decision by default — ask it, or mark it `ASSUMED (awaiting ratification)`; never silently resolve
it as a cited how-decision.

**Observed failure:** settling an acceptance-bar sourcing standard as a how-decision leaked downstream
to a later gate, where it surfaced as the challenger's "AC not met."

## refine — why convention-answerable scope questions are how-decisions

**Rule (`skills/refine/SKILL.md`, step 2 tie-breaker (b)):** when a documented recipe / rulebook / the
ticket text dictates the answer, resolve-by-citation and flag for ratification — do not put it to the
user as an open want.

**Observed failures:** a scope question "one consumer or all?" was asked as a want when the documented
shared recipe already answered "all"; a "permanent vs reversible?" was asked as a want when the
ticket's literal "insert" already leaned the answer.

---

## review, reviewer, challenger — where the git-isolation rule came from

**Rule (`skills/review/SKILL.md` + both critic briefs + `PRINCIPLES.md`):** inspect branches ref-based
or in an isolated worktree; never run `checkout`/`switch`/`stash` in the shared working tree.

**History:** this is the same root cause the v1.6.1 eval-isolation invariant fixed for the eval path (a
process running stateful git in a shared cwd) — one principle, two surfaces.

---

## codify, budget, db-map — why these skills exist

- **`codify`:** the rule book is the single thing the whole plugin grounds in; when it is absent, thin,
  or genuinely inconsistent, the reviewer and challenger produce generic, low-value output.
- **`budget`:** field cost was always an estimate, never measured per-phase (`context ≠ correctness`
  applied to optimization: don't optimize what you haven't measured).
- **`budget`, Caveman guardrail:** brevity applied where a false-green could hide is the retro-#5
  failure class — which is why critic output is never compressed.
- **`db-map`:** the database is where the costliest mistakes live and where the reviewer/challenger are
  blindest — but a schema map is the most stack-specific thing of all, so it is opt-in and never core.

---

## autorun — why the review seat stays in an unattended run

**Rule (`skills/autorun/SKILL.md`, the degradation ladder):** the review seat degrades in three steps
and never to zero; the envelope is never degraded at all.

**History:** every defect measured across the field runs so far was *inside* the diff, not outside it.
Field test 1: two real defects, both found by the reviewer subagent, none by the envelope. Field test
2: four regressions caught by CI, none by the envelope. Ticket 016: reviewer and challenger both
returned clean and a human then found four AC1 failures. Review was waived on both code-atlas tickets
where it was optional, and both times a later review found real defects; waiving it is measured against
defects reaching the PR on seven field tickets (064, 065, 068, 071, 073, plus PRs #102 and #103). The
envelope watches the world *outside* the diff, so `RECONCILE` is a floor under `finalise` and never a
substitute for review.

---

## autorun — why `--no-challenger` is an argument, and why M7 was WITHDRAWN

**Rule (`skills/review/SKILL.md` step 2, `skills/solve/SKILL.md`, `skills/autorun/SKILL.md`):** the
challenger runs by default; `--no-challenger` waives it explicitly, and under `autorun` the waiver is
line one of `DISCLOSURE`.

**History:** the challenger is effective but expensive (about 58k per run across five measured runs),
and turning it off as a token limit approaches is a deliberate safety decision rather than a shortcut.
Making it an argument records the choice instead of relying on someone remembering an improvised
instruction.

**Withdrawn:** an earlier proposal in this line of work — *refuse to start the run when the challenger
is waived* — is **withdrawn** and was never shipped. Two field tests ran with the challenger waived
both times and it was dispatched on neither: **a directive waived twice is not a mechanism**. Shipping
it would have added a refusal nobody honours, in place of the disclosure line that actually reaches the
morning reader.

---

## autorun — why the tree comparison is a tree comparison

**Rule (`plugins/mango/scripts/run_contract.py`, the fixed floor):** `TREE-COMPARISON` refuses a
content grep and refuses an ancestry predicate.

**History:** a content grep looks for text named at t0, and the incident this condition exists to catch
— a correction committed to the branch after the merge — is unnamed then, so the grep returns HOLDING
on precisely that case. An ancestry predicate (`git merge-base --is-ancestor`) is a false-red under a
squash merge, which sank an earlier version of this condition. The merge-strategy question is read from
recent first-parent topology rather than the host's allowed-strategy flags (which say what is permitted,
never what is used) or a whole-history merge count (which returns the pre-change answer when a repo
switched strategy mid-history, in the dangerous direction).

**Also measured:** one contract stated "the last 17 commits are single-parent" when it was 18 — perfect
format, false fact. Machine-writing guarantees the grammar, not the values, which is why every derivable
value is derived by a command and everything else is marked an unchecked agent claim.

---

## autorun — why the budget mechanism is a proxy and does not guard the big term

**Rule (`plugins/mango/scripts/budget.py`, `skills/autorun/SKILL.md` step 4):** the ceiling is a call
count, named as a proxy, and the ladder cuts main-loop work before any subagent.

**History:** from the code-atlas ledger, the challenger runs about 58k and the reviewer about 108k per
round, while a fresh main loop ran 217.7k–689.2k plus millions of cache reads; ticket 003 recorded
dispatch at 7.6% of the run. Dropping a subagent therefore saves roughly a tenth of a run. mango's
ledger measures subagent dispatch only, so on at least one host the largest term is invisible to the
harness at runtime and a "remaining tokens" gate cannot see what is being spent. Call count is
countable live and ran roughly 1.5–4.2k fresh tokens per call across four ledger rows.
