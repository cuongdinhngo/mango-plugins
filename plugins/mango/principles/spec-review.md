## Spec review — lenses, conduct, resolve, convergence

Shared by `brainstorm`, `spec` and `spec-review`. Each lens is one `spec-reviewer` dispatch with a fresh
context; the lens name in the brief selects the questions below.

### Lenses

| Lens | Used by | Asks |
|---|---|---|
| `comprehension` | spec-review | First paraphrase two things: *what is proposed* and *how the current system works, per the document*. A paraphrase the document contradicts is a finding. A project term used without a definition is a finding. |
| `zoom-out` | spec-review, brainstorm | Is this needed at all? Can existing code or a library do it? YAGNI; premature optimisation; does it fix the symptom or the cause? |
| `critic` | spec-review, brainstorm | Missing alternatives; failure modes; migration and rollback; security; operations and observability; cost. |
| `readiness` | spec-review, only when the document has an implementation section | Every implementation step is decided (no choice left to the implementer); every file in the boundary has a reason; every user journey has a planned test; every step leaves the build green. |
| `ergonomics` | brainstorm | Is the API, CLI or UI obvious to use? Is every error actionable? |

Severity: **Blocker** (the document cannot be built or would build the wrong thing), **Major** (a real
gap a reader would hit), **Nit** (wording, polish).

### Conduct

- Challenge before agreeing. Praise nothing that is not a finding.
- Never restate the author's framing as a conclusion.
- A finding names its scope (section and line) and its evidence (`path:line` where it exists).

### Resolve

Every Blocker and Major gets one of four outcomes; a Nit may also be declined.

| Outcome | When |
|---|---|
| **CONTEST** | The author shows evidence a reviewer could read: a file and symbol, or a decision already written in the document. |
| **ESCALATE** | The evidence sits outside anything a reviewer can read — a human decides. "It is intentional" with nothing written is an ESCALATE. |
| **PROPOSE FIX** | The author proposes a change to the document; it is applied only when the human agrees. |
| **DECLINE** | Nits only. |

Never add context to a document only to satisfy a reviewer. Never contest a comprehension finding: a
reader misunderstood, so the document needs the fix. Never change a finding's severity.

### A lens that does not report

A lens whose result has no `LENS RESULT` line (an error, a cut-off or partial output, a turn limit) is
dispatched once more. Still none → that lens is `not run` for the round. `not run` is never zero
findings, and a round with any lens `not run` is not clean.

### Convergence

- **Settled** — contested or accepted as a risk; never reopened.
- **Reappeared** — fixed in an earlier round and found again; reopened.
- **Churn** — a new finding inside the scope of the last fix, which reverting that fix would remove;
  report it and stop.
- A round is clean when it has no open Blocker, Major or ESCALATE and no lens `not run`, judged before
  that round's fixes are applied.
- **Converged** = one clean round after the last applied fix. Stop at `spec_review.max_rounds`
  (default 3) whether converged or not.
