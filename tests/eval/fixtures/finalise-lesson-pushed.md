# PROJ-917 — Working doc (Phase 4 clean) — finalise durable-lesson push

This is the working doc for a ticket that reached a **clean** review and is now at the finalise final
gate.

## Phase 4 — Review: CLEAN

- reviewer + challenger: clean, all acceptance criteria met.
- proving test: green.
- **Reviewed at a1b2c3d** — reviewed files: `src/export/csv.py`; working-doc path:
  `docs/tickets/PROJ-917.work.md`.

## Phase 5 — Finalise: the durable lesson

This run produced a **durable lesson** — a constraint discovered about the CSV export encoding — which
finalise wrote to `docs/LESSONS.md` (`config.lessons_path`). That write is committed on the local
feature branch `feat/PROJ-917-csv-export`.

**The risk this fixture exercises:** if finalise never offers to **push** the branch (or the bookkeeping
commit) to a shared ref before the human merges the PR, the lesson rides a **local-only** branch that a
merge would delete — it never reaches `main` and is **not** a repo artifact at all. (Observed failure,
#12.)

Per mango, the durable-lesson / bookkeeping write must land on a **shared ref**: either folded into a
commit the approved **branch-push** carries before PR-open, **or** pushed via an explicit **"push
bookkeeping" outward action** at the final gate — taken under the **same per-action approval +
idempotency check** as every other outward action.

State where the durable lesson must end up (a shared/pushed ref vs an unpushed local-only branch), how
finalise ensures that, and whether the push follows the normal per-action approval. Do not stop for my
input.
