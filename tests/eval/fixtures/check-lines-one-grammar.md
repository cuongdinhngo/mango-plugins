# PROJ-540 — Recall the claim corpus for a shared-vocabulary change

**Requirement:** the change renames a shared generated enum consumed by four call sites.

**Acceptance Criteria:**
- AC1: every consumer of the renamed enum is updated.

## The state (INJECTED) — treat all of this as literal

`config.lessons_path` holds eight claim records. Matching this change: none by symbol, four by handle
(the change touches a shared vocabulary), four by area, none by finding, none retired.

Run the mango `refine` skill's advisory recall against this state and answer all of the following
explicitly:

1. Emit the `RECALL:` counted line for this run, verbatim, in the exact shipped grammar.
2. How many fields does that line carry, and what is each one?
3. Is there more than one shipped form of the `RECALL:` line? Answer yes or no and say how you know.
4. If the working-doc template you copy showed a form with fewer fields than the skill you are
   executing, which one governs, and why?

Do not stop for my input; show the artifacts you would produce.
