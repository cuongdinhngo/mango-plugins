# PROJ-832 — Commit the epic scaffold before a child branches

**Requirement:** This epic (a search suite) has cleared analysis(epic) and design(epic), and
`breakdown` has proposed a **counted** ticket list that the human is ratifying at the split-gate.

## Context — scaffold ordering vs the first child branch

After the split ratifies, `breakdown` creates the **epic scaffold**: the **child-ticket stubs** plus the
epic **BACKLOG / roadmap** (the list of ratified tickets). Per mango, that scaffold must be **committed
to a shared ref BEFORE any child ticket starts its own branch.**

Why the ordering matters: when a child ticket later runs its lifecycle and **edits its stub**, the
ticket-blind **`challenger`** reviews the child's diff. If the scaffold was committed first, the child's
diff reads as a genuine **edit of a committed file** — the challenger can tell a real retarget-edit from
brand-new authorship. If the scaffold was created but **not committed**, the child's edit shows up as
**net-new** authorship, and the challenger cannot distinguish the two and must caveat its verdict.
*(Observed, n=1 epic 013: the scaffold was created but not committed, and a child's challenger had to
caveat.)*

State exactly **when** the scaffold is committed relative to the first child branch, and **why** that
ordering preserves the challenger's net-new-vs-edit evidence.
