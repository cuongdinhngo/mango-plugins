# PROJ-717 — Add a "compact" density option to the report table

**Requirement:** Add a "compact" row-density option to the report table.

## Context

The report table is one of several consumers built from a single **documented shared table recipe**
(the project docs describe one table-config recipe that every report/list table is generated from). The
decision refine faces is a **scope / consistency question**: *"apply the compact-density option to this
one consumer, or to all consumers sharing the recipe?"*

Per refine's tie-breaker, this is **answerable from a documented convention** — the shared recipe
dictates the answer: a change to the shared recipe means **"apply to ALL consumers"** by construction.
So this is a **how-decision**: refine must **resolve-by-citation** (cite the documented shared recipe)
and **flag it for ratification** — it must **NOT** put it to the user as an open want-decision. A
"please suggest / your call" bounce from the user would be the tell that it was resolvable without them.

This fixture exercises the consistency branch of the tie-breaker: a scope question answerable from a
documented recipe is **resolved-by-citation (how-decision), NOT asked as a want-decision.**
