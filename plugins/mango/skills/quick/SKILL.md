---
name: quick
description: The lite lane of the mango lifecycle, for trivial tickets (SCOPE=S, single file/row, no universal requirement, not security-tagged). Use to ship a one-line fix without the full five gates — a single combined pre-code gate, then execute, a reviewer-only check, and the final gate. Skips the full matrix, challenger, and fan-out.
---

**`<mango>` = this plugin's root:** `${CLAUDE_PLUGIN_ROOT}` when the host sets it, else the plugin root
this skill file sits in, else a read-only search for a directory holding `PRINCIPLES.md` and
`.claude-plugin/plugin.json` — **more than one hit → take the HIGHEST `version` in its `plugin.json`
(semver compare, never `find` order, never a lexicographic sort) and report the candidate count** —
never a hardcoded path. Unresolvable → say so and use the inline fallback
named at the point of use (`<mango>/PRINCIPLES.md`, *Resolving a mango-shipped path*).

Operate under `<mango>/PRINCIPLES.md`. This is the right-sized lane: it still enforces
surgical changes (diff ⊆ approved change) and goal-driven execution (a green **proving test**), but
drops the ceremony that a trivial ticket does not need.

**Ground rules.** Read `${CLAUDE_PROJECT_DIR}/.harness.json` and ground rules in
`config.rulebook_path`. If `.harness.json` is missing, STOP and tell the user to create one from
`<mango>/config/harness.example.json`. Use only on a ticket that qualifies for
`TIER: lite` (SCOPE=S, single file / single requirement row, no universal "all/every/no"
requirement, not security-tagged). If it does not qualify, route to `solve` (full tier) instead.
**The lite lane always skips fan-out** regardless of `config.explore_fanout`, and **runs on a single
model** — no delegation overhead (see `<mango>/PRINCIPLES.md`).

## Steps

0. **Hard entry check (REFUSE non-qualifying tickets).** Before anything else, confirm the ticket is
   genuinely trivial. **STOP and route the user to `/mango:solve` (full tier)** — do not proceed — if
   ANY of these hold:
   - the ticket is **security-tagged**;
   - the change touches **more than one file**;
   - the ticket contains a **universal ("all/every/no") requirement that resolves to N > 1** — judged
     on the resolved inventory denominator N, **not** on the wording alone. A requirement that sounds
     universal but resolves to **N = 1** (a single affected site) does **not** disqualify the ticket.
   This is a refusal, not a "should": lite exists only for single-file, single-requirement,
   non-security fixes. A direct `/mango:quick <KEY>` on a ticket that fails this check is rejected
   here.
1. **The two reads — the ONLY additions the lite lane carries (both reuse existing mechanisms).**
   `quick` is reached two ways: routed from `solve` after `analysis` declared `TIER: lite`, or invoked
   **directly** as `/mango:quick <KEY>`. On the routed path `analysis` already emitted both lines below —
   **carry them forward verbatim** and re-run nothing. On a **direct** invocation neither has run, and
   without them a lite ticket **writes lessons at `finalise` and never reads one** — a one-way
   contributor to a lesson file that only grows. So run, at minimum, these two reads:

   - **Advisory recall** — `refine`'s advisory recall, the **same mechanism** (do **not** invent a
     parallel one): read the claim records in `config.lessons_path`, surface the claims this ticket
     matches (type 1 by symbol, **type 2 by handle**, type 5 by area, type 6 by the re-raised finding),
     skip any marked `retired:`, and emit the counted line verbatim, **every run, zero included**:

     `RECALL: <n> claim(s) surfaced | <s> by symbol | <h> by handle | <a> by area | <f> by finding | <r> retired skipped — advisory (blocks nothing)`

   - **Rule-section coverage** — `analysis` step 11, the **same mechanism**: the applicable sections of
     `config.rulebook_path` are the **union** of those derived from the change TYPE and those carrying a
     `handle:` this run's `RECALL:` line surfaced. Answer each by **naming what in this change the rule
     constrains** or `N/A because <reason>` (a bare `✅` with nothing named is not an answer), and emit:

     `RULE SECTIONS: <n> applicable — <k> by change-type | <m> by recalled handle — §<id> (<source>) ✅ / N/A (reason), …`

   **Both lines close with zeros and add no step.** No `config.lessons_path` (or an empty one) → `RECALL:`
   with zeros, `<m> = 0` handle-matched sections, and the lane continues unchanged; a rule book that is
   still the `init` template of `TODO`s contributes `<k> = 0` and is not a finding. Recall stays
   **advisory** here exactly as everywhere else: it injects no requirement, adds no row, blocks no gate.
   A `PROVISIONAL` section is surfaced, never gate-blocking as if codified.

   **This is all the lite lane gains — the cheapness is the point of it existing.** `quick` still runs
   **no challenger, no requirements matrix, no fan-out, no baseline capture**, and keeps its two human
   gates. Two reads, two lines, no extra step.
2. **Minimal working doc.** Create the working doc `<config.work_dir>/<KEY>.work.md` (default
   `work_dir` = `tickets_dir`) from the template — a **separate file** from the ticket spec, never
   appended to the raw ticket — but fill only the **single goal row**, the **one change**, and the
   **proving test**. Set `TIER: lite`.
3. **Single combined gate (✋).** Present, together, the one change AND the proving test, and STOP
   for one approval before any code. This is the lite lane's **single combined gate** — there is no
   separate design gate. Silence ≠ approval.
4. **Execute.** On an approved branch, make ONLY that change; match surrounding style; never
   reformat untouched lines. Add the proving test. Run the **surgical/diff-scope check**: the diff
   must be ⊆ the approved change. Commit (no AI co-author trailer).
5. **Reviewer-only check.** Run the `reviewer` agent on the diff. **No challenger, no full matrix.**
   Confirm the proving test is green via `config.test_command`. If the reviewer reports Critical or
   the test is red, loop back and STOP. **Stuck-detector:** after **K** failed attempts against the
   same proving artifact / same failing-test signature (default `K=3`, configurable as
   `config.stuck_threshold` in `.harness.json`), STOP and escalate to the user with what was tried
   and the options instead of retrying further; the counter resets when the failing signature
   changes.
6. **Finalise.** Hand off to `finalise`'s final gate: dry-run by default, one separate approval per
   outward action. Update `Session status` with a concrete next action.

**Two human gates total:** the combined pre-code gate and the final gate.
