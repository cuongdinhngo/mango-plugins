---
name: doctor
description: Health-check a project's mango setup. Use before running the lifecycle (and as solve's preflight) — validates .harness.json exists, parses, has every required key, and that rulebook_path/tracker/test_command are usable. Prints a ✅/⚠/❌ checklist with exact remediation for each failure.
---

Operate under `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md`. This skill turns silent runtime drift in
`.harness.json` into a counted, visible artifact — a checklist that blocks the pipeline when red.

Read `${CLAUDE_PROJECT_DIR}/.harness.json`. Run every check below and emit a checklist with
✅ (pass) / ⚠ (warn) / ❌ (fail). For each ❌, print the **exact remediation** (often: run
`/mango:init`, or add the named key).

## Checks

1. **Exists & parses.** `.harness.json` is present and is valid JSON. ❌ → "create it with
   `/mango:init` or copy `${CLAUDE_PLUGIN_ROOT}/config/harness.example.json`."
2. **Required keys present.** `rulebook_path`, `repos`, `test_command`, `tracker`,
   `ticket_header_schema` all exist. ❌ → name each missing key.
3. **Rule book usable.** `rulebook_path` exists (as a file or a directory). If it exists but looks
   like boilerplate or is very short, ⚠ "rule book looks like a stub — fill in the TODOs." ❌ if it
   does not exist.
4. **Tracker writable.** `tracker.cli` exists and is executable, **or** `tracker.read_mcp` is set
   (reads only). ❌ if neither — "set `tracker.cli` to your tracker write command."
5. **Test command set.** `test_command` is non-empty and not a `REPLACE_ME` placeholder. ❌ → "set
   `test_command` to the command that runs your proving test."

## Output

Print the checklist, then a one-line summary `DOCTOR: <p> pass | <w> warn | <f> fail`. If any ❌,
state plainly that the lifecycle should not start until it is fixed.
