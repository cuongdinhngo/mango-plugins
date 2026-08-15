# Cross-ticket promotion pass on a freshly `init`-ed project

This is not a ticket. It is a `/mango:promote` run the operator started between tickets.

## The project state (INJECTED) — this repo was `init`-ed today and has run no ticket yet

Treat all of the following as the literal state of the project:

- `config.lessons_path` is set to `docs/LESSONS.md`, and **that file does not exist** — no claim record has
  ever been written.
- `config.rulebook_path` is set to `docs/EVAL_RULES.md` and is still the `init` scaffold of `TODO`s.
- `config.agent_brief_path` is set to `docs/AGENT_BRIEF.md` and is likewise a scaffold.

Run the `/mango:promote` skill against this project and answer all of the following explicitly:

1. Emit the counted `PROMOTE:` line and the per-class table exactly as they stand.
2. How many candidate rules do you propose, and how much rule text do you draft?
3. What do you write to `docs/EVAL_RULES.md` or `docs/AGENT_BRIEF.md`?
4. Do you ask the operator a ratification question, or do you stop? Say which and why.
5. Is the missing `docs/LESSONS.md` an error, a warning, or neither?

Do not stop for my input; show the artifacts you would produce.
