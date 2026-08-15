---
name: version-check
description: Opt-in, on-demand check of whether a newer mango version has been published. Reports the running version vs the latest published version and, if newer, PRINTS the exact host /plugin commands to update. It never updates, never installs, and never edits any registry — plugin administration belongs to the host.
---

**`<mango>` = this plugin's root:** `${CLAUDE_PLUGIN_ROOT}` when the host sets it, else the plugin root
this skill file sits in, else a read-only search for a directory holding `PRINCIPLES.md` and
`.claude-plugin/plugin.json` — **more than one hit → take the HIGHEST `version` in its `plugin.json`
(semver compare, never `find` order, never a lexicographic sort) and report the candidate count** —
never a hardcoded path. Unresolvable → say so and use the inline fallback
named at the point of use (`<mango>/PRINCIPLES.md`, *Resolving a mango-shipped path*).

Operate under `<mango>/PRINCIPLES.md`. This skill **detects and informs, never
self-administers.** It does not install, reinstall, reorder a plugin registry, or run `/plugin` on
the user's behalf — that is the host's job. Working around the loader from a restricted or remote
channel where `/plugin` is unavailable is exactly the trap this skill exists to avoid; do not encode
it.

Invoke only on demand (`/mango:version-check`). It runs no network call unless explicitly configured
to.

## Steps

1. **Running version.** Read `<mango>/.claude-plugin/plugin.json` for the running
   `version` and take the base path from `<mango>`. Print `mango <version> @ <base path>`
   (the same authoritative signal `doctor` prints).
2. **Latest published version — only if configured.** Read `${CLAUDE_PROJECT_DIR}/.harness.json`.
   - If `config.update_check_url` is **unset**, report the running version, state that no update
     check is configured, and say where to set it (`config.update_check_url` — an optional raw URL to
     the published marketplace manifest). **Make no network call.** Stop here.
   - If `config.update_check_url` **is set**, fetch that URL (read-only), parse the plugin's published
     `version` from the returned marketplace manifest, and compare it to the running version.
   - **No `version` in the marketplace manifest? Follow `source` to the plugin's `plugin.json`.** A
     marketplace manifest often carries no `version` field — the version lives in the plugin's own
     `plugin.json`. When the manifest has **no `version`** for the plugin, take its `source` path from
     that manifest and read `version` from the plugin's `plugin.json` there (read-only), instead of
     stopping at "not specified". Resolve the source relative to the manifest URL for a remote source,
     or as a repo-relative path for a local one. This is still **detect-and-inform only** — reading a
     `plugin.json` is a read, never a self-update.
3. **Report + print host commands (never run them).**
   - Print: the running version and the latest published version.
   - If the published version is **newer**, print the exact commands to run **on the host**, and say
     plainly that the user must run them there — mango will not:
     - `/plugin marketplace update <marketplace>`
     - `/plugin install <plugin>@<marketplace>`
     (substitute the marketplace and plugin names from the manifest.)
   - If the running version is current, say so.

## Boundary (binding)

This skill only **reads** a manifest and **prints** instructions. It never installs, reinstalls,
reorders a registry, runs `/plugin`, or edits any host plugin registry or `.harness.json`. If you
find yourself tempted to work around the loader from a restricted/remote channel, STOP and update
from the host.
