# PROJ-601 — Toolbar buttons must meet touch-target size AND spacing

**Requirement:** The action buttons in the toolbar are usable on touch devices.

**Acceptance Criteria:**
- Each toolbar button meets the M4 touch-target gate: `size ≥ 44×44 CSS px` **and**
  `spacing ≥ 8 px` between adjacent buttons.

## Proposed proof (as submitted for review)

The proof manifest for the M4 gate asserts **only the size clause**: it measures each button's
bounding box for `width ≥ 44 px` and `height ≥ 44 px`. There is **no assertion on the spacing
between adjacent buttons** — the 8 px-gap clause is unproven.
