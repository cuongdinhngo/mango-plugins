# PROJ-904 — Ratify the split of the reporting-suite epic

**Requirement:** This epic has cleared `analysis(epic)` and `design(epic)`. `breakdown` has drawn the
ticket boundaries and is at its split-gate: 5 tickets, each with an enumerated six-letter INVEST
self-check. One proposed ticket bundled two deliverables and was **re-split** before the gate. Two
tickets **overlapped** on the same export module and the boundary was ruled in favour of the writer
ticket owning it.

## Context — where the epic ends

An epic **ends at `breakdown`**. Its child tickets each run their own full lifecycle, but the **epic
itself** never reaches `finalise` — so `finalise`'s *"always capture a durable lesson to
`config.lessons_path`"* rule never fires for the epic. In a field run this meant the **split rationale**
and the **overlap rulings** existed only in the conversation and were **lost** when the run ended.

`config.lessons_path` is set in `.harness.json`.

Walk the ratification and state, concretely: who owns capturing the epic's **durable lesson**, at what
point it is written, **where** it is written, and what it must contain. Emit any counted artifact that
proves it happened rather than describing it in prose. Do not stop for my input.
