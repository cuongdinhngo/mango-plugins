## The learning loop — recall, propose, never self-modify

> **A lesson becomes an atomic CLAIM; a claim is recalled ADVISORILY; and only a claim that RECURRED
> and then SURVIVED FALSIFICATION is PROPOSED for promotion — into a PROJECT file, at a human
> ratification gate. No lesson, however ratified, ever edits mango.**

The loop is the descriptive/normative boundary above applied to what a run *learned*: mango
**describes** what it observed (the claim, its type, its evidence), **facilitates** the human deciding
whether it becomes a rule, and **never authors** the rule itself.

**The unit is the atomic claim, not the lesson entry.** `finalise` splits every captured lesson into
atomic claims first; classification, recall, recurrence, falsification, and promotion all operate on
**claims**. A bundled entry classified as one thing routes its other halves to the wrong destination.

### The six claim types — the type decides the destination and the recall key

| # | Type | Destination (all PROJECT-owned) | Recalled by |
|---|------|---------------------------------|-------------|
| 1 | **tool-constraint** — a named library/tool at a named API behaves unexpectedly | stays in `config.lessons_path` | **symbol** (the import / API) |
| 2 | **generalisable heuristic** — a principle that holds across tools | **routed by subject:** code → `config.rulebook_path`; process → `config.agent_brief_path` | **handle** (a class slug — a heuristic holds across tools, so neither a symbol nor an area can key it) |
| 3 | **skill-gap SIGNAL** — a mango phase demonstrably skipped a check it could have made in that run | `config.skill_gap_path` — **never a mango skill** | — (a signal for mango's maintainer) |
| 4 | **irreducible world-fact** — no gate could pre-empt it | `config.gotchas_path` | — |
| 5 | **project/domain ground-truth** — a hard-won fact about THIS system or domain | **split by sub-shape:** descriptive → `config.design_doc_path`; normative (a MUST) → `config.rulebook_path` as an entry with an **ID + blocking status**; environment (it rots) → carries a **`verified-at:`** stamp | **area** (not symbol) |
| 6 | **adjudicated non-defect** — a deviation examined and ACCEPTED, recorded so it is not re-litigated | `config.drift_path`, carrying an **`expiry:`** condition | **the finding that would otherwise be re-raised** |

**Two tiebreaks, applied during classification — not after:**
- **1 vs 4** — if a mango gate can be *imagined* that would have caught it → **type 1**. Only when
  **no** gate could ever pre-empt it → **type 4**. Type 4 is rare; do not over-build for it.
- **2 vs 3** — **type 3** only when a phase **demonstrably skipped a doable check in that run**;
  otherwise the general principle is **type 2**. A **preventive** process-lesson learned with nothing
  skipped fits neither — route it to `config.agent_brief_path`, **not** a rule.

**A process claim never lands in the code rule book.** `config.agent_brief_path` is a **project-owned**
process brief; it is **not** one of mango's own `agents/*.md` briefs, which no loop output may touch.

### The five invariants (binding — none is optional)

1. **The classifier PROPOSES; the human confirms.** A type, a destination, and a promotion are each a
   **proposal**. mango never classifies-and-acts, never promotes on its own, and never auto-applies or
   self-patches a rule.
2. **Recall is advisory.** It **SURFACES** matching claims at `refine`/`analysis` and does nothing
   else: it never injects a requirement, never adds an acceptance criterion, never blocks a gate, and
   never edits a file. A claim marked `retired:` is **SKIPPED** by recall — a human marks it retired,
   there is no auto-retire — and its history stays in the file. **Surfacing is advisory; ACCOUNTING for
   what was surfaced is not.** A type-2 handle that recall surfaced must be **answered by name** at
   `design`'s blast-radius step — traced, or explicitly `does not apply because <reason>`. Recall still
   adds no requirement and no matrix row; the gate is on the *answer count*, never on the claim's
   content. Surfacing without accounting is what makes an advisory recall fire zero times.
3. **Falsification precedes ratification.** Recurrence measures how often a belief was **restated**,
   not whether it was ever **CHECKED**, so a recurring claim faces a falsification check — *is it still
   true? is it cheaply verifiable? was it checked, or only repeated?* — **before** it reaches the human
   ratification gate. A claim that fails, or that cannot be cheaply checked, is **BLOCKED from
   promotion** and stays a recorded lesson.
4. **Lessons never modify mango.** No lesson — however recurrent, however ratified — edits a mango
   skill, agent brief, template, or this file. A **type-3 skill-gap is a SIGNAL** recorded in the
   project's `config.skill_gap_path` for mango's maintainer; mango changes only through a normal
   version (build + `validate.py` + the behavioural eval + retro). A lesson flowing into a skill would
   make mango carry one project's context — breaking *harness, not rules* — and would destroy
   provenance, since mango's own design could no longer be told apart from an injected check.
5. **Everything is project-local.** Every loop output — claims, promoted rules, skill-gap signals,
   drift entries — lives in the **PROJECT's** repo. mango reads them in-project and **carries nothing
   home**: project A's claims never reach project B, and nothing is ever written into mango-plugins.

### Rules live in the rule book; `CLAUDE.md` only points at it

A promoted rule is written into `config.rulebook_path` (the rule book is created there if absent) and
is **never copied into `CLAUDE.md`** — a copy goes stale and competes with its source. `init` already
scaffolds the rule book and hoists a **pointer** to it into `CLAUDE.md`, and `doctor` already checks
both; the loop **REUSES** that and rebuilds none of it. A promotion is **not done** until the rule is
in the rule book **and** `doctor` is green on the `CLAUDE.md` → rule-book pointer.

Enforced at `finalise` (split → classify → recurrence/supersession → falsification → the per-action
ratification gate), `refine`/`analysis` (advisory recall), and `codify` (the rule-book write stays
`PROVISIONAL (awaiting ratification)`); guarded by `scripts/validate.py` and the behavioural eval.
