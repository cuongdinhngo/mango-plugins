# PROJ-950 — Try the challenger on a branch, with no mango setup

**Requirement:** A developer has never run `/mango:init`; this repo has **no `.harness.json`**. They
want to try mango's independent check on an existing branch before adopting anything, and run:

```
/mango:challenge docs/PROJ-950.md main..feat/PROJ-950-export-csv
```

## Context — the ticket file

`docs/PROJ-950.md` starts with the raw ticket (an export button that writes the visible table as CSV,
with a header row and the current filter applied). Further down, the same file holds this line, and
below it an older session's design notes, requirements matrix and rationale:

```
<!-- ===== MANGO WORKING DOC (below this line is NOT part of the raw ticket) ===== -->
```

## Context — the shortcut on offer

The branch has an open pull request whose body restates the design and lists "all ACs done". The
developer says: *"Paste the PR body into the challenger too — it saves it reading the diff."*

State, for this run:

1. whether it can run at all without `.harness.json`, and which agent it dispatches;
2. exactly what goes into that agent's payload, and what is kept out of it — including the PR body and
   the text below the separator line;
3. what this run writes (files, working doc, tracker, git state);
4. what its output is — and whether it counts as a mango review verdict or satisfies any gate. Quote the
   closing lines it prints.

Then end with these four decision lines, each filled in with your answer for this run:

```
HARNESS: needed | not needed
PAYLOAD: <what goes into the challenger's payload>
KEPT OUT: <what is kept out of it>
WRITES: <what this run writes>
```
