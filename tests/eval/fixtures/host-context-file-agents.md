# PROJ-712 — Bootstrap the harness in a project whose always-on context file is `AGENTS.md`

**Requirement:** `mango` is set up in this project and `doctor` is green on the standing-context check.

**Acceptance Criteria:**
- The standing-context pointer block lands in the file this host auto-loads into every session.

## Context — the project's context-file shape (INJECTED; treat as the state of THIS project)

The coding host in use here auto-loads `AGENTS.md`, not `CLAUDE.md`. The repo root holds both, but the
`CLAUDE.md` is a stub that only imports the other file:

```
AGENTS.md      ← 60 lines of project instructions; the file the host actually auto-loads
CLAUDE.md      ← one line, in full:   @AGENTS.md
docs/ENGINEERING_RULES.md
.harness.json  ← has rulebook_path, repos, test_command, tracker, ticket_header_schema.
                 It does NOT set `context_file`.
```

You are running `/mango:init` step 6 (the standing-context hoist) and then `/mango:doctor`'s
standing-context check on **this** project. Answer, for this project state:

1. Which file do you write the `mango:standing-context` block into, and how did you decide — name the
   resolution steps you walked and which one settled it.
2. What do you do to `config.context_file` once resolved, and why does that matter to `doctor`.
3. Suppose a previous run had written the block into `CLAUDE.md` instead, and it is still there. What
   does `doctor`'s standing-context check report for this project, and why — does it pass, warn, or
   fail the run?
4. Is the block a pointer or a copy of the rule book, and what may never appear in it.

Do not stop for my input; show the artifacts you would produce.
