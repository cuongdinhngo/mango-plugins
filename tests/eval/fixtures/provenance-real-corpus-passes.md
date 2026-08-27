# PROJ-521 — Rank the modules an onboarding summary should mention first

**Requirement:** `rank_modules` orders indexed modules by how central they are, so the summary leads
with the ones that matter.

**Acceptance Criteria:**
- AC1: `rank_modules` returns every module exactly once (no duplicates, no drops).
- AC2: the ranking is **useful** — the modules a newcomer would need first appear near the top, and
  vendored dependency code does not outrank first-party code.

## The design state (INJECTED) — treat all of this as literal

Assume Gate 1 cleared. `.harness.json` sets `real_corpus_path: "corpora/anchor-index"`, and that path
**exists**. Two candidate plan rows for AC2 are proposed:

**Candidate A**

```
| AC2 | logic | unit + corpus run | real-corpus | ✅ |
```

with this recorded beside it:

```
corpus: corpora/anchor-index (resolved)
$ python -m atlas.rank --index corpora/anchor-index --top 10
 1 app/http/router      first-party
 2 app/domain/billing   first-party
 3 app/domain/accounts  first-party
 ...
10 vendor/psr/log       dependency
```

**Candidate B**

```
| AC2 | logic | unit | real-corpus | ✅ |
```

with nothing recorded beside it — the cell simply reads `real-corpus`. No corpus path is named, no
command is shown, no output is pasted.

Run the mango `design` skill against this state and answer all of the following explicitly:

1. For candidate A, is `real-corpus` established? Does AC2's layer-match pass and does Gate 2 close?
2. For candidate B, is `real-corpus` established? What does the skill say a cell like this reads as,
   and what happens to AC2's layer-match?
3. State the difference between the two in one sentence — what makes one checkable and the other not.
4. Emit the `EXCLUSIONS:` counted line for candidate A and for candidate B.

Do not stop for my input; show the artifacts you would produce.
