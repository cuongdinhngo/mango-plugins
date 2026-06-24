---
name: init
description: Bootstrap mango in a project. Use once per repo before the lifecycle skills — detects the stack read-only, interviews the user only for what can't be detected, writes .harness.json, and scaffolds a starter engineering rule book if none exists. Marks every guessed value UNVERIFIED.
---

Operate under `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md`. This skill makes mango's hardest prerequisite —
a real engineering rule book and a filled `.harness.json` — exist, so the reviewer/challenger
produce grounded, project-specific output instead of generic noise.

## Steps

1. **Detect the stack (read-only).** Inspect, without modifying anything:
   - Languages + test runner from `package.json`, `pyproject.toml`, `composer.json`, `go.mod`,
     `Gemfile`, etc. → propose `test_command`.
   - The git remote → guess `tracker.base_url` and `tracker.project_key`.
   - The existing branch naming convention → propose `branch_strategy`.
   - Existing docs that look like a rule book → propose `rulebook_path`.
2. **Interview only for the undetectable.** Ask the user only for what cannot be observed: the
   rule-book location (if none found), `tracker.cli` (the write command), `tracker.read_mcp`, and
   the `ticket_header_schema` (header → C/R/G/AC). **Mark every guessed value `UNVERIFIED`** in the
   output for the user to confirm.
3. **Write `.harness.json`.** Write `${CLAUDE_PROJECT_DIR}/.harness.json` using
   `${CLAUDE_PLUGIN_ROOT}/config/harness.example.json` as the shape. **Never overwrite an existing
   `.harness.json` without explicit confirmation.** Put no secrets in it (note that tokens live in a
   gitignored `.env`).
4. **Resolve the config-file commit policy — ask the user.** `.harness.json` sits at the repo root,
   so honouring "don't commit it" must not be left to manual vigilance on every `git add`. After
   writing the file, **ask** whether `.harness.json` should be **committed** (shared team config) or
   **kept local**:
   - **kept local** → add `.harness.json` to `.gitignore` (creating `.gitignore` if absent) and tell
     the user it is now ignored.
   - **committed** → leave `.gitignore` untouched, but **warn**: never put secrets in `.harness.json`
     — secrets live only in a gitignored `.env`.
   Do **not** hard-gitignore by default — the config is often a shared team file, so the human
   decides. Either way, `init` **never writes secrets into `.harness.json`.**
5. **Scaffold a starter rule book if missing.** If `config.rulebook_path` does not exist, copy
   `${CLAUDE_PLUGIN_ROOT}/skills/init/rulebook-template.md` there as a **single file** (e.g.
   `docs/engineering-guide.md`). Then:
   - **Pre-fill only what was observed** from the codebase (detected language, test command,
     directory layout, obvious conventions).
   - **Leave a clear `TODO` for everything the team must decide.** Do **not** invent rules —
     observed patterns only; everything else is a TODO.
   - `rulebook_path` may point at a file or a directory; one file is the default (the reviewer reads
     it every run, so a single file guarantees the whole rule set loads).
6. **Confirm.** Show the written `.harness.json`, list every `UNVERIFIED` value, state the chosen
   commit policy (committed, or gitignored), and tell the user to run `/mango:doctor` to verify the
   setup is all-green.
