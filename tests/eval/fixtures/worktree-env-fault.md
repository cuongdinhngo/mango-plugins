# PROJ-901 — Review a branch whose suite was run inside a fresh worktree

**Requirement:** The branch `feat/PROJ-901-rate-limit` adds a rate-limit guard to one request handler
(one source file, one new test). It is ready for review.

## Context — how the suite was run

A review subagent needed to **run** the suite against the branch. Per mango's git-isolation rule it did
**not** run stateful git in the shared working tree; it created an **isolated `git worktree`** at the
branch and ran `config.test_command` inside it.

A `git worktree` contains only **tracked** files. This project needs **untracked** local environment to
boot — a `.env` with the datastore URL and local config — none of which exists in a fresh worktree.

## What the run reported

```
12 test files, 12 failed, 0 passed
  Error: cannot connect to datastore (env DATABASE_URL is undefined)
  Error: config not loaded — missing .env
```

The same 12 files pass in the developer's own checkout. The diff itself touches one handler and adds
one test.

State how you classify this suite result, whether it becomes a review finding / a regression against the
recorded `BASELINE:`, and exactly what you do before re-running. Also state what you would need to carry
into the worktree, or what the cheaper alternative is when the working tree already sits at the reviewed
SHA. Finally, say whether a *partial, targeted* failure inside the change's blast radius would be treated
the same way.
