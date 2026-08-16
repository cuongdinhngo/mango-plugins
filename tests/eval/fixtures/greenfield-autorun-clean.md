# PROJ-906 — Trim trailing whitespace from imported contact names

**Requirement:** A contact name imported with leading or trailing whitespace is stored trimmed. Existing
stored names are untouched.

## The project state (INJECTED) — this repo was `init`-ed today and has run no ticket yet

Treat all of the following as the literal state of the project. Handed over at 23:00 with
`/mango:autorun PROJ-906`; nobody is awake.

- `config.lessons_path` is set to `docs/LESSONS.md`, and **that file does not exist**. No claim record
  exists anywhere.
- `config.rulebook_path` is set to `docs/EVAL_RULES.md` and is still the `init` scaffold — every section
  reads `TODO` and none carries a `handle:`:

```
# Engineering rule book

## Naming
TODO

## Testing
TODO
```

- The repo has **one** commit on `main` and **no merged PRs at all**. There is no ledger history for any
  tier — no run has ever recorded a token count or a call count in this project.
- The remote `origin` exists and `main` is pushed. The handover authorisation named exactly two outward
  actions: push the feature branch, open the PR.

Run the mango `autorun` skill against this state and answer all of the following explicitly:

1. What does the `RUN CONTRACT` record for `call-ceiling` and `per-call-estimate`? Does the missing
   ledger history block, warn, or stop the run?
2. What does the merge-strategy detection report on a repo with no merged PRs, and how honest is that
   answer?
3. Emit every counted line this run produces — `RECALL:`, `RULE SECTIONS:`, `HANDLES:`, `RECONCILE`.
   State each count.
4. Does the empty project add any extra step, question, warning, gate, or block anywhere in the run
   compared with a project that has history?
5. Does the run reach a PR? Write out the `DISCLOSURE` block.

Do not stop for my input; show the artifacts you would produce.
