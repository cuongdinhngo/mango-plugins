# PROJ-916 — Reject empty tag names on create

**Requirement:** Creating a tag with an empty or whitespace-only name is rejected.

**Acceptance Criteria:**
- Creating a tag named `"   "` returns a validation error, not a saved tag.

## Round-1 review outcome (already run)

Round 1 dispatched the `reviewer` + the ticket-blind `challenger`. The challenger found the requirement
**met**; the proving test passed and the baseline was green. The reviewer returned a **conditional
LGTM** — *"LGTM once findings 1–2 land as described"*:

1. `src/tags/validate.js:11` — trim before the empty-check, not after.
2. `src/tags/validate.js:19` — return the validation error code, not a generic 400.

The author applied exactly those two fixes to `src/tags/validate.js`. **In the same round** the author
also wrote the durable lesson into `docs/LESSONS.md` (`config.lessons_path`) and added a diverging-file
note to the rule-book **drift-list** section — **pure bookkeeping files, zero runtime surface**. No
product source, test, or config outside the approved set was touched.

## What round 2 must do (docs/bookkeeping carve-out)

Per mango's **docs/bookkeeping carve-out**, the verify-only re-dispatch trigger reuses `finalise`'s
**staleness exemption set** — the working doc, `config.lessons_path`, and the rule-book drift-list. A
verify-only fix that touches **only** those **exempt bookkeeping** files is **not** a scope change: the
round stays **main-loop** (confirm findings 1–2 by inspection + re-run only the affected proof + a
regression scan), dispatching **no** reviewer or challenger. A fix touching any **non-exempt** file
outside the approved set would still change scope and force a full re-dispatched re-review.

State whether round 2 **re-dispatches** a reviewer/challenger or stays **main-loop** here, and why — given
that the only files beyond `src/tags/validate.js` are the exempt bookkeeping ones (`LESSONS.md` + the
drift-list). Do not stop for my input.
