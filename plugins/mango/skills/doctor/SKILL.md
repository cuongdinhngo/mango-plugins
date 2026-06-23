---
name: doctor
description: Health-check a project's mango setup. Use before running the lifecycle (and as solve's preflight) — validates .harness.json exists, parses, has every required key, and that rulebook_path/tracker/test_command are usable. Prints a ✅/⚠/❌ checklist with exact remediation for each failure.
---

Operate under `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md`. This skill turns silent runtime drift in
`.harness.json` into a counted, visible artifact — a checklist that blocks the pipeline when red.

**First output line — the authoritative running-version signal.** Before any check, read the
running manifest at `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` for `<version>` and take
`<base path>` from `${CLAUDE_PLUGIN_ROOT}`, then print as the very first line:

`mango <version> @ <base path>`

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
   `/mango:init` or copy `${CLAUDE_PLUGIN_ROOT}/config/harness.example.json`."
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

## Output

Print the checklist, then a one-line summary `DOCTOR: <p> pass | <w> warn | <f> fail`. If any ❌,
state plainly that the lifecycle should not start until it is fixed.
