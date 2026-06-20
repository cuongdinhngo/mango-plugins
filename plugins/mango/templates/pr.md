# <KEY> — <short title>

## Summary

<What changed and why, derived from the working doc. Do not paste raw commit messages.>

**Ticket:** <KEY> · <tracker link>

## Changes

- <change 1, traced to its requirement>
- <change 2>

## Testing

- **Proving test:** <name / location>
- **Invocation:** `<config.test_command ...>`
- **Result:** <pass/fail output summary>
- **Would it fail without the change?** <yes — evidence>

## Data / DB

<Any data or schema change, and the migration workflow used. "None" if not applicable.>

## Risk & rollback

- **Risk:** <blast radius, affected repos>
- **Rollback:** <how to revert: branch, commits, undoing a transition>

## Reviewer checklist

- [ ] Diff ⊆ approved change list (no scope creep)
- [ ] No reformatting of untouched lines
- [ ] Proving test green
- [ ] Shared changes ported across repos
- [ ] No secrets, no unsafe data access, auth/access intact
