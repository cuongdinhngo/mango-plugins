# PROJ-902 — Hand a finished change-set from execute to review

**Requirement:** Gate 2 approved a two-file change (one handler, one test). `execute` has implemented
exactly the approved change list on `feat/PROJ-902-retry-backoff` and is about to flow into `review`.

## Context — the ordering question

review's `reviewer` and `challenger` inspect the branch **ref-based**: `git diff <base>..<branch>`,
`git show <branch>:<path>`, `git log <base>..<branch>`.

State **when** `execute` commits the change-set relative to dispatching review, and **why** that ordering
matters for a ref-based review.

## Context — the empty-range near-miss

In a field run the range diff came back like this:

```
$ git diff main..feat/PROJ-902-retry-backoff
$ (no output)
```

…and the review very nearly concluded **"no changes — nothing to review"** and rubber-stamped it, while
two files of real work sat on disk.

State exactly what a reviewer/challenger must do when a `<base>..<branch>` diff comes back **empty** —
which specific commands it falls back to — before it may conclude there is no change. Say plainly whether
"the range is empty, therefore there are no changes" is ever an acceptable conclusion on its own.
