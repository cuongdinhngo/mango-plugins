---
name: doctor
description: Health-check a project's mango setup. Use before running the lifecycle (and as solve's preflight) — validates .harness.json exists, parses, has every required key, and that rulebook_path/tracker/test_command are usable. Prints a ✅/⚠/❌ checklist with exact remediation for each failure.
---

**`<mango>` = this plugin's root:** `${CLAUDE_PLUGIN_ROOT}` when the host sets it, else the plugin root
this skill file sits in, else a read-only search for a directory holding `PRINCIPLES.md` and
`.claude-plugin/plugin.json` — **more than one hit → take the HIGHEST `version` in its `plugin.json`
(semver compare, never `find` order, never a lexicographic sort) and report the candidate count** —
never a hardcoded path. Unresolvable → say so and use the inline fallback
named at the point of use (`<mango>/PRINCIPLES.md`, *Resolving a mango-shipped path*).

Operate under `<mango>/PRINCIPLES.md`. This skill turns silent runtime drift in
`.harness.json` into a counted, visible artifact — a checklist that blocks the pipeline when red.

**First output line — the authoritative running-version signal.** Before any check, read the
running manifest at `<mango>/.claude-plugin/plugin.json` for `<version>` and take
`<base path>` from `<mango>`, then print as the very first line:

`mango <version> @ <base path>`

**Report HOW `<mango>` resolved, on this same line** — `${CLAUDE_PLUGIN_ROOT}` / located from this skill
file / found by search / **UNRESOLVED**. On a host that never sets `${CLAUDE_PLUGIN_ROOT}`, resolution
continues down the order rather than stopping; if it reaches **UNRESOLVED**, print
`mango <unknown> @ UNRESOLVED` plus a ⚠ naming which resolution steps were tried, and **continue to the
checks below** — every one of them reads `.harness.json` and the project, not the plugin, so an
unresolved plugin root never blocks the checklist. Never guess a path to fill this line in.

State plainly, right there: *"This is the version that will run. A green doctor does not prove it is
the version you intended — if this line is not the version you expect, resolve it from the host with
`/plugin` (do not work around the loader from a restricted/remote channel)."* If — and only if — the
base path contains a version segment that **differs** from the manifest version, emit a ❌
("loaded path/manifest version mismatch — reinstall from the host"). This signal is purely
**locally observable**: doctor stays **offline**, makes no network call, and never reads or edits any
host plugin registry. doctor detects and informs; it never installs or reinstalls anything.

Then read `${CLAUDE_PROJECT_DIR}/.harness.json`. Run every check below and emit a checklist with
✅ (pass) / ⚠ (warn) / ❌ (fail). For each ❌, print the **exact remediation** (often: run
`/mango:init`, or add the named key).

## Checks

1. **Exists & parses.** `.harness.json` is present and is valid JSON. ❌ → "create it with
   `/mango:init` or copy `<mango>/config/harness.example.json`."
2. **Required keys present.** `rulebook_path`, `repos`, `test_command`, `tracker`,
   `ticket_header_schema` all exist. ❌ → name each missing key.
3. **Rule book usable.** `rulebook_path` exists (as a file or a directory). If it exists but looks
   like boilerplate or is very short, ⚠ "rule book looks like a stub — fill in the TODOs." ❌ if it
   does not exist. In either the ⚠ (thin/boilerplate) or the ❌ (missing) case, **suggest**
   `/mango:codify` to facilitate defining the rule book and database conventions — *suggest only;
   never run it automatically.*
4. **Tracker writable.** `tracker.cli` exists and is executable, **or** `tracker.read_mcp` is set
   (reads only). ❌ if neither — "set `tracker.cli` to your tracker write command."
5. **Test command set.** `test_command` is non-empty and not a `REPLACE_ME` placeholder. ❌ → "set
   `test_command` to the command that runs your proving test."
6. **Finalise checklist (if set).** If `config.pr_checklist_path` is set, the file it points at must
   exist. ⚠ if set but missing — "`pr_checklist_path` is set but the file is absent; finalise will
   have no checklist to walk." Skip silently if the key is unset (it is optional).
7. **Token optimizer — informational only (never gates).** Print **one informational line** noting
   whether RTK is detectable on the system (e.g. `command -v rtk`) and the recorded
   `config.token_optimizer` choice. This is a **note, not a ✅/⚠/❌** — it never blocks the pipeline.
   mango tolerates RTK's compact Bash output but **never depends on it**: RTK absent, everything runs
   identically (only the saving is lost). To adopt or review an optimizer with its safety trade-offs,
   run `/mango:budget`; `doctor` never installs one.

8. **Standing context reachable from the host's ALWAYS-ON context file — informational, never blocks.**
   **Resolve that file first, exactly as `init` does — do not assume `CLAUDE.md`:** `config.context_file`
   if set; otherwise, if the project has an `AGENTS.md` and its `CLAUDE.md` is absent or merely
   **imports** another file (e.g. `@AGENTS.md`), the always-on file is the imported one (`AGENTS.md`);
   otherwise `CLAUDE.md`. **Print the resolved path** on this check's line so the human can see which
   file was judged.

   Then check whether `${CLAUDE_PROJECT_DIR}/<resolved context file>` carries the
   `mango:standing-context` block (the marker pair) and that it still names a `rulebook_path` pointer.
   ✅ when present; ⚠ when absent, when the block holds no rule-book pointer, **or when the block exists
   only in a file the host does not auto-load** (e.g. written into `CLAUDE.md` on an AGENTS-first
   project — reachable via an import chain counts as reachable, a block in an unloaded file does not) —
   "run `/mango:init` to write it into `<resolved context file>`; without it every session re-derives
   the harness basics." Never ❌: the block is persistent context, not a prerequisite — mango reads
   `.harness.json` and the rule book at runtime either way. If the block contains anything that looks
   like a secret or token, ⚠ loudly: the context file is committed context and carries pointers only.

9. **Learning-loop destinations — informational, never blocks.** For each **set** loop-destination key
   (`lessons_path`, `skill_gap_path`, `gotchas_path`, `drift_path`, `agent_brief_path`) print one line
   noting whether the file exists. ⚠ when a key is set but the file is absent — "the loop will report the
   destination as not configured and surface the claim instead of writing it"; skip a key that is unset.
   Never ❌: every destination is created on first write, and the lifecycle runs fully without any of
   them. Two things this check **does** assert, because they are the loop's safety boundary: every
   configured destination path is **inside the project repo** (a path outside it, or any path under a
   mango plugin directory, is a ❌ — no loop output may leave the project or reach mango), and
   `rulebook_path` is reachable from the resolved always-on context file per check 8, since a promoted
   rule lives in the rule book and the context file carries only the pointer.

10. **Cross-ticket promotion is reachable — informational, never blocks.** Print one line stating that
    `/mango:promote` is the **cross-ticket** pass over `config.lessons_path` (recurrence ≥ 2 on a **type-2**
    handle), that it **proposes only** and writes nothing without a per-candidate human ratify, and that a
    ticket's `finalise` never stands in for it. Then check its two prerequisites and report each:
    - `config.lessons_path` is **set** — ⚠ when unset ("`/mango:promote` has no corpus to read; it will
      report zeros and stop").
    - at least one of `config.rulebook_path` (code subject) / `config.agent_brief_path` (process subject)
      is **set** — ⚠ when neither is ("a recurring type-2 claim will be surfaced as
      `cannot promote: destination key unset` rather than routed").
    Never ❌: promotion is opt-in and off the lifecycle, and the lifecycle runs fully without it.

## Output

Print the checklist, then a one-line summary `DOCTOR: <p> pass | <w> warn | <f> fail`. If any ❌,
state plainly that the lifecycle should not start until it is fixed.
