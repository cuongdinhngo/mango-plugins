## Skills are directive-only — no rationale in a SKILL.md

> **Skill text is runtime-loaded and IS behaviour (prose-IS-behaviour). A `SKILL.md` contains
> DIRECTIVES ONLY — no rationale, no "observed failure" war-stories, no historical justification, no
> why-this-exists commentary. The "why" belongs in the CHANGELOG or `RATIONALE.md`, never in a
> `SKILL.md`.**

Every token of a `SKILL.md` is paid on **every ticket run** that loads it, so non-behavioural text is
a permanent tax that instructs nothing. Concretely:

- **When a lesson motivates a new rule, add the RULE to the skill and the REASON to the CHANGELOG**
  (and, if a future maintainer needs the incident itself, to `<mango>/RATIONALE.md` —
  which is **not** loaded at runtime).
- **Keep, always:** every instruction, gate, STOP condition, MUST/NEVER, counted artifact line,
  threshold, escalation, conditional, output-format spec, and anything marked binding.
- **Never trade a directive for brevity.** Trimming a skill is a behaviour change unless the removed
  text is *provably* non-behavioural — the test is *"if I delete this, does any instruction, gate,
  condition, count, format, or escalation disappear?"* If yes or unsure, **keep it**.

Guarded by `scripts/validate.py` (`validate_no_rationale_in_skills`): the build **fails** if a
rationale marker appears in any `plugins/mango/skills/*/SKILL.md`.
