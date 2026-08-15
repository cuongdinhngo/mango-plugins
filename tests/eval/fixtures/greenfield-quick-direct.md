# PROJ-728 — Fix a typo in the CLI help text

**Requirement:** The export command's help text reads "reccords"; it must read "records". One string, one
file. Not security-tagged.

This ticket is being started by a **direct `/mango:quick PROJ-728`**. Neither `refine` nor `analysis` has
run for it.

## The project state (INJECTED) — this repo was `init`-ed today and has run no ticket yet

Treat all of the following as the literal state of the project:

- `config.lessons_path` is set to `docs/LESSONS.md`, and **that file does not exist**.
- `config.rulebook_path` is set to `docs/EVAL_RULES.md`, and it is still the `init` scaffold — every
  section reads `TODO`, and none carries a `handle:`:

```
# Engineering rule book

## Naming
TODO

## Testing
TODO
```

- No claim record exists. No rule has been ratified. The change is one string literal in one file.

Run the mango `quick` skill on this ticket through its pre-code gate. Emit every counted line the lane
emits, then answer all of the following explicitly:

1. What are the values on the `RECALL:` line, and does the missing lessons file stop, warn, or block the
   lane?
2. What is on the `RULE SECTIONS:` line, and what does the all-`TODO` rule book contribute to it?
3. Does the lane now run a challenger, a requirements matrix, an Explore fan-out, or a baseline capture?
4. How many human gates does this ticket have, and how many extra steps did the two reads add on this
   project?

Do not stop for my input; show the artifacts you would produce.
