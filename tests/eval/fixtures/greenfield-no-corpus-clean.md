# PROJ-001 — First ticket on a brand-new project: raise the upload size limit

**Requirement:** the upload size limit rises from 5 MB to 25 MB.

**Acceptance Criteria:**
- AC1: a 20 MB upload is accepted.
- AC2: a 30 MB upload is rejected with the existing "file too large" error.

## The project state (INJECTED) — treat all of this as literal

This is the FIRST ticket ever run on this repository. `/mango:init` has just run:

- `.harness.json` exists, with `real_corpus_path` **absent entirely** (init never wrote it).
- `track` is `backend`. There is no frontend code, no `DESIGN.md`, no surfaces.
- `lessons_path` points at a file that does not exist yet. No rule book beyond init's TODO template.

Run the mango `design` skill against this state and answer all of the following explicitly:

1. What is the fixture provenance of AC1 and AC2?
2. Does the absent corpus configuration add any extra step, any warning, or any block to this run?
   Answer yes or no, plainly.
3. Suppose instead `real_corpus_path` were set to `corpora/anchor` and that path did NOT exist. What
   would be reported, and would anything crash or silently pass as `real-corpus`?
4. Since this project has no frontend track, does anything in the fixture-provenance rule fire?
5. Emit the `EXCLUSIONS:` counted line for this run.

Do not stop for my input; show the artifacts you would produce.
