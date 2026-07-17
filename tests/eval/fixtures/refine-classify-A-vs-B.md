# PROJ-711 — Add a "share report" feature

**Requirement:** Let users share a report with a teammate.

## Context

This raw request mixes two kinds of product-decision, and refine must classify EVERY one BEFORE asking
anything:

- A **loại-B (HOW / CÁCH LÀM)** decision the project's existing conventions already answer — how the
  share action is authorized and wired follows the same access-control + action convention every
  existing feature uses. refine must **resolve this itself and CITE** the convention/code, and must
  **NOT ask the user** — asking a convention-answerable "how" launders a decision refine could make.
  This is the self-check: *"can existing convention/code answer this? If yes → loại-B → cite, don't
  ask."*
- A **loại-A (WANT / Ý MUỐN)** decision only the user can settle — WHO a report may be shared with
  (only named teammates? anyone with a link? read-only vs editable?). This is genuine product intent;
  refine must **ASK the user**, phrased in **want-language**, not technical language.

This fixture exercises the classification: loại-B resolved-with-citation (not asked), loại-A asked in
want-language, and the self-check catching a convention-answerable question as loại-B rather than
wrongly asking it as a loại-A.
