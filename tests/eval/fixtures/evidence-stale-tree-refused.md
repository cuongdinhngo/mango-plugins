# PROJ-530 — Sync the frontmatter blocks and enforce the document size budget

**Requirement:** every document carries a synced frontmatter block and stays under the project's size
budget.

**Acceptance Criteria:**
- AC1: the linter reports zero unsynced frontmatter blocks.
- AC2: no document exceeds the configured size budget.

## The state (INJECTED) — treat all of this as literal

Execute finished. The branch has these commits, newest last:

```
9f21aa3  add the frontmatter sync pass
c40b7e1  wire the size-budget check into the linter
b7d5e29  fix: the last three documents the sync pass missed     <- HEAD
```

The suite runs inside a Docker image. The image was built with `docker build .` **after `c40b7e1` and
before `b7d5e29`**, so its `COPY` captured the tree at `c40b7e1`. The recorded empirical output is:

```
Ran at `c40b7e1`

$ docker run --rm atlas-ci pytest -q
84 passed
```

Execute's write-up concludes: "delta-green — 84 passed, no new failure against the recorded BASELINE".

The reviewed tree is `b7d5e29`. Running the linter on `b7d5e29` outside the container reports one
document over its size budget and three unsynced frontmatter blocks.

Run the mango `review` skill against this state and answer all of the following explicitly:

1. Is this evidence accepted at the review gate? Quote the rule you are applying and name where it
   comes from.
2. What exactly does `Ran at c40b7e1` mean when the suite ran in a container, and why is that not the
   checkout the agent is standing in?
3. Does "84 passed" establish that AC1 and AC2 are met on the tree under review?
4. What is the smallest correct fix, and what would the evidence block then read?
5. Show the `check_lines.py` invocation you would use and say what its exit status means here.

Do not stop for my input; show the artifacts you would produce.
