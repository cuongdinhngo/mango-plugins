---
name: spec
description: Write a spec from a brief, notes or a conversation, one section at a time with the user approving each, the user choosing every architecture decision. Use when the user asks to write a spec or design document before any ticket or epic exists. Advisory; closes no gate.
---

**`<mango>` = this plugin's root:** `${CLAUDE_PLUGIN_ROOT}` when the host sets it, else the plugin root
this skill file sits in, else a read-only search for a directory holding `PRINCIPLES.md` and
`.claude-plugin/plugin.json` — **more than one hit → take the HIGHEST `version` in its `plugin.json`
(semver compare, never `find` order, never a lexicographic sort) and report the candidate count** —
never a hardcoded path. Unresolvable → say so and use the inline fallback
named at the point of use (`<mango>/PRINCIPLES.md`, *Resolving a mango-shipped path*).

Operate under `<mango>/PRINCIPLES.md`. **READ `<mango>/principles/spec-review.md` NOW** (unconditional)
for the conduct rules. This skill is **not a lifecycle phase**, closes no gate, and never creates a
ticket or an epic. `.harness.json` is **not required**; without it, `specs_dir` is `docs/specs/`.

**Usage:** `/mango:spec [<brief path> | <notes>]`

## Steps

1. **Find the input.** A path given → read it. Else a `<specs_dir>/*.brief.md` the user named. Else
   ask for a brief or notes — one question. Author: the brief's, else `git config user.name`, else ask.
   Ask where to save it (default `<specs_dir>/<slug>.spec.md`).
2. **Draft one section at a time**, in the order of `<mango>/templates/spec.md`, into that file.
   After each section, stop and ask **one question**: approve, or what to change. Never paste a long
   section into chat; point at the file.
3. **Decisions.** A question with more than one reasonable answer → at most three options, each with
   how it works, its trade-off and when it fails; **no ranking and no default**. The user chooses. Asked
   to choose for them → restate the trade-offs and ask again. Decide mechanical choices (a file name, a
   format) yourself.
4. **Implementation**: every step decided, nothing left for the implementer to choose; every file in the
   boundary with a reason; no production code (pseudocode, signatures and schemas are fine). Every CUJ
   gets a test and a command in the verification plan.
5. **Compare with the brief** (when there is one) before finishing. A **contradiction** (the spec decides
   against the brief) or an **addition** (the spec adds a goal or scope the brief does not have) is
   listed contradictions first, each quoting the brief and the spec. The user settles each one.
   **Never edit the spec to match the brief on your own.**
6. **Finish.** Fill both lines in the spec:

   `SPEC: <d> decision(s) | <h> decided by human | <o> open question(s) | <c> CUJ(s) | <t> CUJ(s) with a planned test | <f> file(s) in boundary`

   `DIVERGENCE: <c> contradiction(s) | <a> addition(s) | <r> resolved by human`

   Run `python3 <mango>/scripts/check_lines.py check <spec> --phase spec`. Its **exit status** is the
   verdict: 0 ready, 2 not ready (an open question, a decision not made by the user, a CUJ with no test,
   an unresolved divergence) or off-grammar, 3 not checkable. Cannot run → say so; never read it as
   ready.
7. **Hand off** with two suggestions, and choose neither for the user: review it with
   `/mango:spec-review <path>`, and add `Spec: <path>` to whichever epic or ticket it belongs to.

## Never

- Never choose an architecture decision for the user, rank options, or mark one as the default.
- Never resolve a divergence or an open question on the user's behalf.
- Never create, edit or route a ticket or an epic; never call a lifecycle skill.
- Never write any file other than the spec.
