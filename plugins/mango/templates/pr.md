# <KEY> — <short title>

## Summary

<What changed and why, derived from the working doc. Do not paste raw commit messages.>

**Ticket:** <KEY> · <tracker link>

## Changes

- <change 1, traced to its requirement>
- <change 2>

## Testing

- **Proving test:** <name / location>
- **Risk layer / layer-match:** <the layer where the requirement can fail (logic / integration / runtime-3p / e2e); the proof sits at that layer ✅>
- **Invocation:** `<config.test_command ...>`
- **Result:** <pass/fail output summary>
- **Would it fail without the change?** <yes — evidence>

## Data / DB

<Any data or schema change, and the migration workflow used. "None" if not applicable.>

## Risk & rollback

- **Risk:** <blast radius, affected repos>
- **Rollback:** <how to revert: branch, commits, undoing a transition>
- **Durable lesson:** <constraint discovered / wrong assumption / process gap recorded to lessons_path — or "none">

## Reviewer checklist

- [ ] Diff ⊆ approved change list (no scope creep)
- [ ] No reformatting of untouched lines
- [ ] Proving test green, at the layer where the requirement can fail (verification plan, no `❌`)
- [ ] Shared changes ported across repos
- [ ] No secrets, no unsafe data access, auth/access intact
