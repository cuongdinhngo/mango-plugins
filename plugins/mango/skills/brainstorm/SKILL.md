---
name: brainstorm
description: Turn a raw idea into a brief through open questions, one per turn, then read-only reviewer lenses once the user is ready. Use when the user asks to brainstorm or explore an idea before any spec, ticket or epic exists. Advisory; closes no gate.
---

**`<mango>` = this plugin's root:** `${CLAUDE_PLUGIN_ROOT}` when the host sets it, else the plugin root
this skill file sits in, else a read-only search for a directory holding `PRINCIPLES.md` and
`.claude-plugin/plugin.json` — **more than one hit → take the HIGHEST `version` in its `plugin.json`
(semver compare, never `find` order, never a lexicographic sort) and report the candidate count** —
never a hardcoded path. Unresolvable → say so and use the inline fallback
named at the point of use (`<mango>/PRINCIPLES.md`, *Resolving a mango-shipped path*).

Operate under `<mango>/PRINCIPLES.md`. **READ `<mango>/principles/spec-review.md` NOW** (unconditional)
for the lenses, conduct and `not run`. This skill is **not a lifecycle phase**, closes no gate, and never
creates a ticket or an epic. `.harness.json` is **not required**; without it, `specs_dir` is
`docs/specs/`.

**Usage:** `/mango:brainstorm [<idea>]`

## Steps

1. **Take the idea**; none given → ask for it. Author: `git config user.name`, else ask.
2. **Explore with open questions, one per turn, and offer no ready-made options** while exploring: the
   problem; who has it; hard constraints; scope edges; how it is handled today and why that is not
   enough; how success is measured. A **want** question (what the user wants) goes to the user. A
   **how** question (how the code works) you answer yourself from the code and cite `path:line`.
3. **Readiness gate.** Summarise the hypothesis in two or three sentences and ask one question:
   *review it with the lenses* or *clarify further*. **Dispatch nothing until the user chooses review.**
4. **Dispatch one `spec-reviewer` per lens, in parallel**: `zoom-out`, `critic`, `ergonomics`. Each gets
   the hypothesis (written to the brief file first, at the path the user confirms — default
   `<specs_dir>/<slug>.brief.md`), the files it names and the absolute path of
   `<mango>/principles/spec-review.md`; never this conversation. A lens with no
   `LENS RESULT` line → dispatch it once more; still none → `not run`, named in the brief's *Analysis*.
5. **Write the brief** from `<mango>/templates/brief.md`: merge and de-duplicate findings into
   *Analysis*, and fill goals, non-goals, alternatives weighed, decisions and open questions from the
   conversation. Fill its line:

   `BRIEF: <g> goal(s) | <n> non-goal(s) | <a> alternative(s) rejected | <d> decision(s) | <q> open question(s)`

   Run `python3 <mango>/scripts/check_lines.py check <brief> --phase brief`; its **exit status** is the
   verdict (0 well-formed with at least one goal, 2 not, 3 not checkable). Cannot run → say so; never
   read it as passed. In chat give only the two or three strongest challenges and the file path.
6. **Repeat 2–5** when the user changes direction or narrows scope.
7. **Hand off** with one question: write a spec with `/mango:spec <brief>`, keep brainstorming, or stop
   and keep the brief. Open questions travel into the spec's *Open questions* verbatim.

## Never

- Never dispatch a reviewer before the user chooses review at the readiness gate.
- Never ask more than one question per turn, and never offer options while exploring.
- Never send a reviewer this conversation; send the written hypothesis.
- Never write any file other than the brief.
