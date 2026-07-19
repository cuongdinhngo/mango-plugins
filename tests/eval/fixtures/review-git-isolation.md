# PROJ-741 — Review a feature branch without corrupting the shared working tree

**Requirement:** A ticket's execute phase has landed its changes on a feature branch
`feat/PROJ-741-export`. The review phase must inspect that branch — the diff, and (if it runs the suite)
the branch's code — to produce a verdict.

## Context — the shared working tree is live

The mango run is executing in the repo's **shared working tree (the live checkout)**, currently checked
out on `feat/PROJ-741-export` with in-progress source files on disk and the working doc open. The
`reviewer` and `challenger` subagents each need to inspect the branch.

State exactly **how** a review subagent inspects the branch: which git commands it uses, whether it may
run `git checkout` / `git switch` / `git stash` in the shared working tree, and — if it needs to **run**
the test suite against the branch (not just read it) — **where** it does so. Then state what happens to
the **shared HEAD** after the review, and what you would do if a subagent were about to run
`git checkout main` in the shared working tree to inspect the branch.
