---
name: spec-review
description: Review a written spec, brief or design document with fresh read-only reviewers, one per lens, and give a counted verdict. Use when the user asks to review a spec or design document before any ticket is built from it. Advisory; closes no gate.
---

**`<mango>` = this plugin's root:** `${CLAUDE_PLUGIN_ROOT}` when the host sets it, else the plugin root
this skill file sits in, else a read-only search for a directory holding `PRINCIPLES.md` and
`.claude-plugin/plugin.json` — **more than one hit → take the HIGHEST `version` in its `plugin.json`
(semver compare, never `find` order, never a lexicographic sort) and report the candidate count** —
never a hardcoded path. Unresolvable → say so and use the inline fallback
named at the point of use (`<mango>/PRINCIPLES.md`, *Resolving a mango-shipped path*).

Operate under `<mango>/PRINCIPLES.md`. **READ `<mango>/principles/spec-review.md` NOW** (unconditional): it
defines the lenses, severities, resolve outcomes, `not run` and convergence used below. This skill is **not a
lifecycle phase** and closes no gate. `.harness.json` is **not required**; without it,
`spec_review.max_rounds` is 3.

**Usage:** `/mango:spec-review <document path>`

## Steps

1. **Read the document.** A `SPEC:` line in it → a mango spec. None → a document written elsewhere;
   review it the same way.
2. **Pick the lenses**: `comprehension`, `zoom-out`, `critic`, plus `readiness` when the document has an
   implementation section (a heading such as *Implementation* or *Implementation plan*).
3. **Dispatch one `spec-reviewer` agent per lens, in parallel**, each with exactly: the document path,
   the scope, the lens name, round `<k>`, and the files the document names. **Nothing else** — never the
   brief, this conversation, or the author's explanations.
4. **A lens with no `LENS RESULT` line** → dispatch it once more; still none → `not run`.
5. **Merge** findings across lenses on the main loop; drop exact duplicates, keep the higher severity.
   Classify each open Blocker and Major as CONTEST, ESCALATE or PROPOSE FIX; Nits may be DECLINE.
   Treat "it is intentional" with nothing written in the document as ESCALATE.
6. **Present** ESCALATE first, then Blockers, Majors, Nits — each with id, lens, severity, scope.
   Ask **one question per turn**: which PROPOSE FIX to apply, and how to settle each ESCALATE. Apply no
   change to the document without the user's yes.
7. **Emit the round's line**, judged before this round's fixes:

   `SPEC REVIEW: round <k> | <l> lens(es) | <x> not run | <b> blocker(s) open | <m> major(s) open | <s> settled | <e> escalated open`

8. **Ask whether to write the review record** into the document. Yes → add or update a final
   `## Review record` section: one row per finding (id, lens, severity, outcome, reason) and **one**
   `SPEC REVIEW:` line, replaced each round. Then run
   `python3 <mango>/scripts/check_lines.py check <document> --phase spec-review`; its **exit status** is
   the verdict (0 clean round, 2 not clean or off-grammar, 3 not checkable). Cannot run → say so; never
   read it as clean. No → print the record only.
9. **Next round** only when the user confirms. Stop when converged, at `max_rounds`, or on churn. Stopped
   without convergence → list open findings by severity and ask one question: accept, run another round,
   or revise the document.

## Close with exactly these two lines

- `SPEC REVIEW — advisory. It closes no gate and is not a mango review verdict.`
- `Converged: <yes | no — reason>`

## Never

- Never send a reviewer the brief, the conversation or the author's reasoning.
- Never count a `not run` lens as zero findings; never call a round with one clean.
- Never apply a fix, change a severity or re-open a settled finding on your own.
- Never write any file other than the reviewed document's `## Review record`, and that only on a yes.
