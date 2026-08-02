# PROJ-711 — Bootstrap the harness in a project whose always-on context file is `CLAUDE.md`

**Requirement:** `mango` is set up in this project and `doctor` is green on the standing-context check.

**Acceptance Criteria:**
- The standing-context pointer block lands in the file this host auto-loads into every session.

## Context — the project's context-file shape (INJECTED; treat as the state of THIS project)

This is a plain Claude-Code project. Its root holds a real `CLAUDE.md` carrying the team's own
instructions:

```
CLAUDE.md      ← 40 lines of project instructions; no import of any other file
docs/ENGINEERING_RULES.md
.harness.json  ← has rulebook_path, repos, test_command, tracker, ticket_header_schema.
                 It does NOT set `context_file`.
```

There is **no `AGENTS.md`** anywhere in the repo.

You are running `/mango:init` step 6 (the standing-context hoist) and then `/mango:doctor`'s
standing-context check on **this** project. Answer, for this project state:

1. Which file do you write the `mango:standing-context` block into, and how did you decide — name the
   resolution steps you walked and which one settled it.
2. What do you do to `config.context_file` once resolved, and why does that matter to `doctor`.
3. Is the block a pointer or a copy of the rule book, and what may never appear in it.
4. Which file does `doctor`'s standing-context check read, and does that check ever fail the run?

Do not stop for my input; show the artifacts you would produce.
