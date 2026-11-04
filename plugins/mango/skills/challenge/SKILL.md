---
name: challenge
description: Run mango's ticket-blind challenger once on a diff, outside the lifecycle. Use to try mango's independent check on any branch — it needs only a ticket file (or a ticket KEY when .harness.json exists). Writes nothing; its output is advisory and never a review verdict.
---

**`<mango>` = this plugin's root:** `${CLAUDE_PLUGIN_ROOT}` when the host sets it, else the plugin root
this skill file sits in, else a read-only search for a directory holding `PRINCIPLES.md` and
`.claude-plugin/plugin.json` — **more than one hit → take the HIGHEST `version` in its `plugin.json`
(semver compare, never `find` order, never a lexicographic sort) and report the candidate count** —
never a hardcoded path. Unresolvable → say so and use the inline fallback
named at the point of use (`<mango>/PRINCIPLES.md`, *Resolving a mango-shipped path*).

Operate under `<mango>/PRINCIPLES.md`. This skill dispatches the existing **`challenger` agent**
(`<mango>/agents/challenger.md`) **once**, on a raw ticket and a diff, and prints what it returns. It is
**not a lifecycle phase**: no requirements matrix, no gate, no working doc. Never dispatch a second
challenger agent or a modified challenger brief.

**Usage:** `/mango:challenge <ticket-file-or-KEY> [<base>..<branch>]`

## Steps

1. **Resolve the raw ticket.** `.harness.json` is **not required** for a ticket file.
   - **A file path** → read that file. A `*.work.md` file is a working doc, not a raw ticket → STOP
     and say so. If the file holds the raw-ticket separator line
     `<!-- ===== MANGO WORKING DOC (below this line is NOT part of the raw ticket) ===== -->`, take
     **only** the text above it.
   - **A KEY** → needs `${CLAUDE_PROJECT_DIR}/.harness.json`. Under `config.tracker.mode: "local"`,
     read `<config.tickets_dir>/<KEY>.md` (same separator rule). Otherwise read the ticket through
     `config.tracker.read_mcp` (a read only). No `.harness.json` → STOP: "pass a ticket file path, or
     run `/mango:init` to look tickets up by KEY." Not local mode **and** no `config.tracker.read_mcp`
     → STOP: "no ticket read is configured; pass the ticket as a file path." Never read the ticket
     through `config.tracker.cli` — it is the write channel.
   - **Never** take the ticket from a PR body, a PR comment, a working doc, or a summary of the change.
2. **Resolve the range.** Given → use it as passed. Absent → `<default>...HEAD`, where `<default>` is
   the branch `refs/remotes/origin/HEAD` points at, else `main`. HEAD **is** the default branch, or
   the range has no commits **and** `git status --porcelain -uall` is empty → STOP and ask for a
   range. Print `CHALLENGE: ticket <path or KEY> | range <base>..<branch>`.
3. **Dispatch the `challenger` agent** as a fresh subagent. **READ `<mango>/principles/git-isolation.md`
   NOW**, before dispatching; it inspects the range **ref-based**. Build its payload as exactly:
   *(a)* the raw ticket text from step 1, and *(b)* the range from step 2 — **nothing else**. Never
   add the **PR body** (never run `gh pr view` or any equivalent to build the payload), the working
   doc, a design, or your own account of the change.
4. **Print the challenger's output in full** — the numbered table (each requirement **met** /
   **not met** / **can't tell** with `path:line`) and its one-line summary. Never compress,
   re-summarise, or re-judge it.
5. **Close with exactly these two lines:**
   - `CHALLENGER ONLY — advisory. No reviewer, no requirements matrix, no proving-test check, no gate: this is not a mango review verdict.`
   - `Want this on every ticket, with gates? Run /mango:init.`

## Writes nothing

`challenge` **writes nothing**: no file, no working doc, no `Reviewed at <sha>` marker, no tracker write
or comment, no PR comment. It runs **no** git command that moves HEAD or changes the index or working
tree (no checkout, switch, stash, commit or push). Its output never satisfies a `review` criterion: a
later `/mango:review` dispatches its own challenger.
