---
name: init
description: Bootstrap mango in a project. Use once per repo before the lifecycle skills — detects the stack read-only, interviews the user only for what can't be detected, writes .harness.json, and scaffolds a starter engineering rule book if none exists. Marks every guessed value UNVERIFIED.
---

**`<mango>` = this plugin's root:** `${CLAUDE_PLUGIN_ROOT}` when the host sets it, else the plugin root
this skill file sits in, else a read-only search for a directory holding `PRINCIPLES.md` and
`.claude-plugin/plugin.json` — **more than one hit → take the HIGHEST `version` in its `plugin.json`
(semver compare, never `find` order, never a lexicographic sort) and report the candidate count** —
never a hardcoded path. Unresolvable → say so and use the inline fallback
named at the point of use (`<mango>/PRINCIPLES.md`, *Resolving a mango-shipped path*).

Operate under `<mango>/PRINCIPLES.md`. This skill makes mango's hardest prerequisite —
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
   `<mango>/config/harness.example.json` as the shape. **Never overwrite an existing
   `.harness.json` without explicit confirmation.** Put no secrets in it (note that tokens live in a
   gitignored `.env`).

   **Write every learning-loop destination key explicitly, with its default — never omit one.** A loop
   destination that is absent from the file leaves a promoted claim with nowhere to go, so `init` writes
   **all six** by name, each defaulting inside `config.docs_dir`-adjacent project paths:
   `lessons_path` (`docs/LESSONS.md`), **`agent_brief_path` (`docs/AGENT_BRIEF.md`)** — the destination for
   a **process** heuristic, which must never land in the code rule book — `skill_gap_path`
   (`docs/SKILL_GAP_CANDIDATES.md`), `gotchas_path` (`docs/gotchas.md`), `drift_path` (`docs/DRIFT.md`),
   and `design_doc_path` (`DESIGN.md`). Each is a path **inside this project repo**; none may point at a
   mango directory. The files themselves are created on first write — `init` writes the **keys**, and
   `doctor` reports which files do not yet exist.
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
   `<mango>/skills/init/rulebook-template.md` there as a **single file** (e.g.
   `docs/engineering-guide.md`). Then:
   - **Pre-fill only what was observed** from the codebase (detected language, test command,
     directory layout, obvious conventions).
   - **Leave a clear `TODO` for everything the team must decide.** Do **not** invent rules —
     observed patterns only; everything else is a TODO.
   - `rulebook_path` may point at a file or a directory; one file is the default (the reviewer reads
     it every run, so a single file guarantees the whole rule set loads).
6. **Hoist the standing context into the host's ALWAYS-ON context file — a POINTER block, never a copy.**
   So the basics survive phase boundaries instead of being re-derived each session, write a
   fenced, regenerable block into the file **this host auto-loads into every session**.

   **Resolve that file first — do not assume `CLAUDE.md`.** In order:
   1. `config.context_file` if set — the explicit answer always wins.
   2. Otherwise detect: if the project has an `AGENTS.md` **and** its `CLAUDE.md` is absent or merely
      **imports** another file (e.g. a one-line `@AGENTS.md`), the always-on file is the **imported**
      one — target `AGENTS.md` (or whatever `CLAUDE.md` imports).
   3. Otherwise default to `CLAUDE.md`.

   Write the block into `${CLAUDE_PROJECT_DIR}/<resolved context file>`, **record the resolved path in
   `config.context_file`** so `doctor` and every later phase read the same answer, and **name it in the
   confirmation**. A block written into a file the host never loads is invisible — the same failure as
   not writing it at all. **Create the file if it is absent.** If it already exists, **ask first**, then
   touch **only** the text between the markers and leave everything else byte-for-byte:

   ```
   <!-- mango:standing-context (regenerate with /mango:init — do not hand-edit) -->
   …
   <!-- /mango:standing-context -->
   ```

   The block carries, each with a short **when/why** framing so a reader knows when it applies — not a
   bare dump:
   - **which harness governs** — `.harness.json` at the repo root — plus the handful of values a phase
     needs before it can act: `test_command`, `rulebook_path`, `tickets_dir` / `work_dir`,
     `branch_strategy`.
   - a **POINTER to `config.rulebook_path`**, never its rules. The rule book is read at runtime and is
     often long; a copy in the context file goes stale and competes with the source. Name the path,
     state that every rule judgment reads that file, and stop there.
   - the **standing constraints** that hold in every phase: the human holds every ✋ gate (silence ≠
     approval); no outward action without a separate explicit approval per action; tracker writes go
     through `config.tracker.cli`, never MCP; stay inside the approved change list; every claim is a
     counted artifact.
   - the pointer to `/mango:doctor` for validating the setup, and to `/mango:solve` to run a ticket.

   **Never write a secret, token, or credential into `CLAUDE.md`** — or into whichever context file was
   resolved. It names the config file and the rule-book path only — secrets live in a gitignored `.env`.
   The context file is committed context, so the same no-secrets rule as `.harness.json` applies, with
   no exception.
7. **Confirm.** Show the written `.harness.json`, list every `UNVERIFIED` value, state the chosen
   commit policy (committed, or gitignored), **name the resolved always-on context file** and say
   whether its standing-context block was written or skipped, and tell the user to run `/mango:doctor`
   to verify the setup is all-green.
