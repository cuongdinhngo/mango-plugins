# PROJ-727 — Add a `--dry-run` flag to the export command

**Requirement:** The export command gains a `--dry-run` flag that prints what would be written and writes
nothing.

## The project state (INJECTED) — this repo was `init`-ed today and has run no ticket yet

Treat all of the following as the literal state of the project:

- `config.lessons_path` is set to `docs/LESSONS.md`, and **that file does not exist** — nothing has been
  written to it yet, because the key is created on first write.
- `config.rulebook_path` is set to `docs/EVAL_RULES.md`, and it is still the `init` scaffold, verbatim:

```
# Engineering rule book

<!-- Scaffolded by /mango:init. Every section below is a TODO for a human to fill in. -->

## Naming
TODO

## Database conventions
TODO

## Testing
TODO
```

- No rule-book section carries a `handle:`. No claim record exists anywhere. No rule has been ratified.
- The change touches one command file and its test. It is not a migration, not a schema change, and adds
  no UI surface.

Run the mango refine and analysis phases for this ticket through the Gate-1 self-audit. Emit every counted
line the two phases emit — `PREMISE:`, `RECALL:`, `REFINE:`, `SECTIONS:`, `RULE SECTIONS:`, `TRACK:`,
`SCOPE:`, `TIER:` — and then answer all of the following explicitly:

1. What are the values on the `RECALL:` line, and does the missing `docs/LESSONS.md` stop, warn, or block
   anything?
2. What is on the `RULE SECTIONS:` line — how many sections are applicable by change type, how many by a
   recalled handle, and what does the all-`TODO` rule book contribute?
3. Does this ticket carry any extra step, question, trace, matrix row, warning, or gate **because** the
   project has no lessons file and an unfilled rule book? Answer yes or no and list any.
4. Does Gate 1 clear?

Do not stop for my input; show the artifacts you would produce.
