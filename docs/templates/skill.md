---
name: <skill-name>
description: <One sentence: what it does and when to use it. ≤ 40 words.>
---
<!-- TEMPLATE: Skill (runtime text) · budget 2,000 words for a new skill · directive-only:
     no rationale, no history, no war stories (those go to CHANGELOG / RATIONALE).
     Keep the order of sections; omit a section only if it is truly empty. -->

**`<mango>` = this plugin's root:** `${CLAUDE_PLUGIN_ROOT}` when the host sets it, else the plugin root
this skill file sits in, else a read-only search for a directory holding `PRINCIPLES.md` and
`.claude-plugin/plugin.json` — **more than one hit → take the HIGHEST `version` in its `plugin.json`
(semver compare, never `find` order, never a lexicographic sort) and report the candidate count** —
never a hardcoded path. Unresolvable → say so and use the inline fallback
named at the point of use (`<mango>/PRINCIPLES.md`, *Resolving a mango-shipped path*).
<!-- Required in every skill except `promote`; validate.py `validate_path_resolution` checks its two anchors
     (`<mango>` = this plugin's root, and `${CLAUDE_PLUGIN_ROOT}`). Keep the paragraph as is. -->

Operate under `<mango>/PRINCIPLES.md`.

## Inputs
<!-- What must exist before this skill runs: files, config keys, prior gates. One line each. -->

## Steps
<!-- A skill with no smoke-guard fixture gets one (3 fresh passes) BEFORE it is edited, or the PR
     says `not covered`. Numbered, imperative, ≤ 12 steps. Each step ≤ 5 lines. Name the command the harness runs;
     never ask the model to judge what a script can count. -->
1. **<Verb>.** <directive>
2. …

## Emits
<!-- The counted lines this skill writes, by name only — the grammar lives in check_lines.py. -->
- `<LINE>` — <one line: when>

## Stop when
<!-- Conditions that end the skill and hand control back to the human. -->

## Never
<!-- Hard prohibitions, one line each. -->
