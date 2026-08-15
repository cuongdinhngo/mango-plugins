---
name: refine
description: Phase 0 of the mango ticket lifecycle — the FIRST phase. Use when a request arrives raw. Scans the project for context, TRIES to expose the unresolved product-decisions, classifies each as a how-decision (HOW → self-resolve + cite) or a want-decision (WANT → ask the user), and emits a refined ticket as counted artifacts for analysis. Self-skips when the ticket is already clear. Detects an epic and routes to the epic path.
---

**`<mango>` = this plugin's root:** `${CLAUDE_PLUGIN_ROOT}` when the host sets it, else the plugin root
this skill file sits in, else a read-only search for a directory holding `PRINCIPLES.md` and
`.claude-plugin/plugin.json` — **more than one hit → take the HIGHEST `version` in its `plugin.json`
(semver compare, never `find` order, never a lexicographic sort) and report the candidate count** —
never a hardcoded path. Unresolvable → say so and use the inline fallback
named at the point of use (`<mango>/PRINCIPLES.md`, *Resolving a mango-shipped path*).

Operate under `<mango>/PRINCIPLES.md` — especially its **expose / ask / never-author**
boundary for intent. refine is the **first** phase of the lifecycle; it runs before `analysis`. Its
whole job is to turn a raw request into a **refined ticket** without ever authoring the user's intent:
it **exposes** the product-decisions and puts the WANT ones to the human, resolving the HOW ones itself
with a citation. **Every decision refine makes is a counted artifact** (visible, challengeable at the
next gate) — never buried in prose.

**Ground rules.** Read `${CLAUDE_PROJECT_DIR}/.harness.json` first. If it is missing, STOP and tell the
user to create one from `<mango>/config/harness.example.json`. refine writes **no code**
and makes **no tracker write**. It reads the project read-only and records its output in the working
doc's Phase-0 block (from `<mango>/templates/ticket.md`).

> **HARD invariants (verified in Finish, guarded by `scripts/validate.py`):**
> - refine **exposes for the human to decide, and NEVER authors intent** — the descriptive/normative
>   (derivable/intent) boundary is the same one `codify` holds for rules. The tie-breaker below changes
>   WHICH bucket a decision lands in, never whether the human owns intent.
> - refine **self-skips** when the ticket is already clear — it must NOT become a tax on every ticket.
> - refine reuses existing machinery only (`sitemap`/`db-map`, the ticket-blind `challenger`,
>   `codify`'s provisional→ratify, `AskUserQuestion`). It convenes **no** Council and burns **no**
>   multi-advisor debate.

## Step 0 — scan the project for context (do NOT ask what the scan can answer)

**READ `<mango>/principles/refine.md` NOW, before Step 0 runs.** It is the binding expose/ask/never-author
contract for this phase — the derivable/intent boundary, the acceptance-bar tie-breaker, the readiness
gate, and the epic-path rules. The read is unconditional, not consult-if-relevant. If `<mango>` does not
resolve, say so and apply the steps below, which restate the load-bearing directives.

mango always runs inside an existing project. refine FIRST **scans** it, read-only: directory
structure, README, package manifest / dependencies, config, and the existing code + conventions —
**reusing the `sitemap` and `db-map` capabilities** (use a generated `config.docs_dir/sitemap.md` /
`db-map.md` if present, else a lightweight read-only enumeration; delegate bulk read-and-extract to the
Haiku `extractor` per `PRINCIPLES.md`). **Depth of exposure comes from the scan, not from luck and not
from asking the user what the scan can answer.** A README or an existing repeated pattern frequently
reveals the request to be the *Nth item following an established convention* — which turns most
would-be questions into **derivable-with-citation** answers rather than questions for the user.

### ⭐ Premise check — resolve the ticket's referenced sources BEFORE any investigation

As the FIRST thing the scan does, resolve every source the ticket references **as already existing** —
a path, file, module, symbol, config key, table, route, command. Classify each reference from the
ticket's **own framing**:

- **referenced-as-existing** ("the handler in `<path>`", "the current `<X>` job", "as `<symbol>`
  already does", "update/fix/extend `<thing>`") → it **MUST** resolve in the checkout.
- **to-be-created** ("add", "new", "introduce", "create", "a `<path>` that will hold …") → it is **not
  expected to exist** and **NEVER** counts as missing.
- **ambiguous** (the framing does not settle which) → **surface it as an item; never block on it.**

**Only a RESOLVABLE IDENTIFIER counts.** A reference is checkable only when a grep can decide it: a
**path, file name, module, symbol, config key, table, route, or command**. A **prose noun** describing
behaviour or a surface — *"the dashboard banner"*, *"the export button"*, *"the existing hashing
algorithm"* — is **not** a resolvable reference: locating it is ordinary analysis work, not a falsified
premise. Classify a prose noun **ambiguous** (surfaced, never blocking) and **continue**.
`PREMISE FALSIFIED` fires **only** on a missing resolvable identifier.

If any **referenced-as-existing** source does not resolve — and the ticket does not declare it
synthetic (a fixture, an example, a hypothetical) — **STOP for the human immediately, before any
further investigation**, and emit:

`PREMISE FALSIFIED: <n> referenced-as-existing source(s) missing — <ref> (<ticket line naming it>), …`

Then **STOP**. Do **NOT** hunt for a renamed or moved equivalent, reconstruct history, search for what
the ticket "probably meant", or continue into Steps 1–6 on a falsified premise. The human resolves it:
confirm the reference, correct the ticket, or declare it synthetic. Emit the counting line on **every**
run — zero included — so the check is auditable and cannot silently not-happen:

`PREMISE: <r> reference(s) checked | <m> missing | <a> ambiguous (surfaced, not blocking)`

**Emit both lines verbatim, prefix included, as the FIRST thing in the response** — the
`PREMISE FALSIFIED:` line (when `m > 0`) then the `PREMISE:` line — before any table, list or prose. A
table or a narrated count is an **addition, never a substitute**: an unprefixed count is **not** the
counted artifact, exactly as for `REFINE:` / `SECTIONS:` / `DRIFT:`. Per-reference detail (which
reference, where the ticket names it, what the scan found) goes **after** the two lines.

`m = 0` (or every miss classified to-be-created) → continue to Step 1 normally; the check adds no gate
to a ticket whose premise holds.

### Advisory recall — SURFACE the matching claims from past runs (never inject, never block)

Once the premise holds, read the claim records in `config.lessons_path` (the shape is
`<mango>/templates/claim-record.md`) and **surface** the ones this ticket matches, keyed
per type:

- **type 1 (tool-constraint) by SYMBOL** — a claim whose `handle: symbol:<import/API>` appears in the
  ticket, the change area, or the imports the scan found. A symbol that does **not** appear surfaces
  nothing.
- **type 2 (generalisable heuristic) by HANDLE** — a claim whose `handle: <class-slug>` names a class the
  change-list touches. A heuristic is keyed by **neither symbol nor area**, so match it on the **shape of
  the change**: surface the handle when the change-list touches a **shared vocabulary** (a shared/generated
  type, symbol, enum, or schema name), introduces or edits a **new core module** (a module other modules
  will import), or **threads a value through callers** (a value produced in one place and consumed
  downstream). None of those three present → surface nothing.
- **type 5 (project ground-truth) by AREA** — a claim whose `area:` matches the ticket's area. Type 5 is
  matched by **area, not symbol**; on an environment sub-shape, surface its `verified-at:` stamp so a
  rotted fact is visible as rotted.
- **type 6 (adjudicated non-defect) by THE FINDING that would otherwise be re-raised** — surface it with
  its `expiry:` condition when this ticket is about to re-raise that finding.

**A claim marked `retired:` is SKIPPED** — it is not surfaced, and it is never auto-retired (a human
marks it retired; the record stays for history).

**Recall is ADVISORY and that is the whole of it.** It **surfaces** claims for the human and the later
phases to weigh: it **never** injects a requirement or an acceptance criterion, **never** adds a matrix
row, **never** blocks or gates the phase, and **never** edits a file. A surfaced claim that turns out to
be irrelevant costs a line of output. Emit the counted artifact on every run, zero included:

`RECALL: <n> claim(s) surfaced | <s> by symbol | <h> by handle | <a> by area | <f> by finding | <r> retired skipped — advisory (blocks nothing)`

If `config.lessons_path` is unset or absent, emit the line with zeros and say so — never skip it
silently.

## Step 1 — the readiness gate is the natural result of trying to expose (ask no one)

refine **TRIES to expose** the unresolved product-decisions the request carries. **The count it finds
IS the answer** — there is no separate "should I run refine?" question to put to anyone:

- **0 unresolved product-decisions → SKIP refine → analysis.** Record the skip as a counted artifact:
  `refine skipped: 0 unresolved product-decisions` — then hand straight to `analysis`.
- **≥1 unresolved → refine works** (Steps 2–6 below).
- **When in doubt → run.** Over-triggering only wastes a little; under-triggering is dangerous. The
  skip decision is itself **recorded** (counted), so a skip is auditable.

**Right-sizing.** Exposure depth scales with rawness: a clear ticket over a strong convention →
near-total skip (often only one genuine want-decision survives, no over-trigger); a raw brief → more
exposure. refine must never fabricate want-decisions to look busy.

## Step 2 — ⭐ classify EVERY decision BEFORE asking (resolve "I don't know" up front)

For **each** product-decision refine surfaces, classify it BEFORE anything is put to the user:

- **how-decision (HOW):** the answer already exists in convention / code / the rule book / the ticket
  text itself, or is a tool/technique choice. refine **resolves it itself and CITES the source**
  (`file:line`, convention, rulebook §, ticket line) — it **does NOT ask the user.** Asking a
  HOW-question forces a rubber-stamp, which is **laundering** a decision refine could make.
- **want-decision (WANT):** the **user is the sole source** — intent, priority, stakes, or a
  genuinely new design choice the scan cannot answer. **Ask the user**, phrased in **want-language, not
  technical language.** Use the **host's typed question UI if it has one** (on Claude Code,
  `AskUserQuestion`'s typed, required-selection fork); **if the host has no such tool, ask in plain chat
  as a numbered list of options** and require the user to pick one. **Never assume a specific host
  tool exists, and never skip the question because it is missing** — the mechanism varies, the
  required selection does not. `(Recommended)` may
  appear **only here**, with its reason in the option description (an informed pick, never a blind one).

### ⭐ The tie-breaker — apply DURING classification, before a decision is filed

Before a decision is filed as a want-decision or a how-decision:

> *"Before asking: can the ticket text / a documented convention / the rulebook plausibly answer this?
> If YES → **how-decision**, resolve-by-citation, flag for ratify. BUT if the decision is about the
> acceptance BAR itself (what counts as done / a threshold / a sourcing standard / an evidence type),
> it is a **want-decision** even when it looks derivable — the user owns the bar."*

- **(a) Acceptance-bar → want-decision by default, even if it looks derivable.** If the decision is
  about WHAT COUNTS AS SATISFYING an AC — a sourcing standard, a threshold definition, an evidence
  type, "what counts as done" — the **user owns the acceptance bar.** refine MAY propose a reading, but
  must **ASK** it (want-decision) or mark it `ASSUMED (awaiting ratification)` and surface it — it must
  **NOT** silently resolve it as a how-decision with a citation.
- **(b) Consistency / scope answerable-from-convention → how-decision, cite, don't ask.** If a
  documented recipe / rulebook / the ticket text itself dictates the answer — e.g. a shared recipe
  means "apply to ALL consumers", or the ticket says "insert" (not "toggle") so the change is not
  reversible — **resolve-by-citation and flag for ratification.** Do **NOT** put it to the user as an
  open want.
- **Guard against the quiet failure:** a how-decision resolution **MUST carry a citation.** An
  **UNCITED how-decision resolution is itself a gate finding** — it means refine settled a HOW with no
  source, which is almost always a **mis-classified want-decision** (an acceptance-bar decision the
  user owns). This directly catches the leak in (a).

## Step 3 — refine stops at DIRECTION, not TOOL

refine exposes **solution DIRECTIONS** whose trade-offs a non-technical user can feel (e.g. *wrap the
existing thing* vs *rebuild it*), never the specific TOOL/library — **tool selection is analysis's
job.** The test: if you put it to the user and they can answer immediately, it is a direction/WANT
(refine); if they would say *"I don't know, help me decide"*, it is a tool/HOW (analysis picks it, or
refine self-resolves it if derivable).

## Step 4 — handle "do your recommendation" / "your call" on a want-decision (ASSUMED is MANDATORY)

When the user hands a want-decision back ("your call", "do the recommended one"), or when refine
resolves a want-decision as an assumption of its own, refine does **NOT** silently adopt it. **The
`ASSUMED` handling is mechanically enforced, not incidental:**

1. Pick per the recommendation, but the choice **MUST be recorded as `ASSUMED (awaiting
   ratification)`** — reusing `codify`'s provisional→ratify tag, not a parallel one. **Recording a
   handed-back (or assumed) decision as settled prose is a finding** — it must carry the `ASSUMED` tag.
2. The next gate **MUST get an explicit human confirm before that decision counts as ratified** — an
   `ASSUMED` decision is **not** ratified because "the gate happened to re-mention it" or the user gave
   an organic "approve." The assumption surfaces again at Gate 1 / design **for an explicit confirm**
   once it is concrete (easier to ratify against a real change list than a raw brief).
- **Tripwire:** if adopting the recommendation would **reverse a prior human decision**, refine MUST
  flag it `ASSUMED (awaiting ratification)` and surface it loudly — **never silent-settle** over a
  decision a human already made.

## Step 5 — split mixed input

If the input mixes an **open brainstorm** ("what could improve X?") with a **targeted task** ("add
multi-platform support"), refine **separates them**: it answers the open part separately (if at all)
and **refines only the targeted part** into the ticket. A brainstorm is not silently promoted into
scope.

## Step 6 — backstop: completeness-of-exposure (the newbie can't self-check)

A user who brings a raw requirement **cannot tell whether refine exposed too FEW decisions.** So refine
reuses the **ticket-blind `challenger`** as an **exposure-checker** — **exactly one dispatch**. It is
**not** asked to argue answers; it is asked only: *"Given this raw request and the project, is any
product-decision still un-exposed?"* This is where council-style machinery's real value sits
(ensure-nothing-missed) — achieved with **1 dispatch**, not a multi-advisor debate. refine does **NOT**
convene a Council. Any decision the exposure-checker surfaces re-enters Step 2 (classify →
want-decision/how-decision, tie-breaker applied). Emit one Cost-ledger row for this dispatch per
`PRINCIPLES.md`.

> **This backstop runs on BOTH paths — the epic path is NOT exempt.** Whether the input is a single
> ticket or an epic, the exposure-checker is the same **1 dispatch**. On an epic it runs **BEFORE
> `breakdown`** (see Epic detection below) — an un-exposed decision is *most* costly at epic scale, so
> the epic path may never be the one that skips the backstop.

## Output — the refined ticket (the input to analysis)

Emit all of the following as **counted artifacts** in the working doc's Phase-0 block — never prose:

- **Settled wants (want-decision, from the user)** → become **acceptance-criteria constraints**
  analysis must honour.
- **Resolved direction + citation (how-decision, refine-resolved + cited)** → a **starting premise**
  for analysis (which still picks the tools). Every how-decision carries a citation (an uncited one is
  a finding — see the Step-2 guard).
- **ASSUMED (awaiting ratification)** → questions analysis must resolve and **confirm-when-concrete**
  at a later gate, via an explicit human confirm (Step 4).
- **Constraints surfaced from the scan** (rule book, design tokens, policy the user could not have
  known to ask about).

- **Recalled claims (advisory)** → surfaced context for analysis and the human to weigh. A recalled
  claim is **never** promoted into an acceptance criterion or a matrix row by recall itself; it becomes
  one only if the human or a later phase decides so on its merits.

Emit **all three** counting lines so the exposure is auditable — the premise and recall lines
**always**, on every run, zero included, even when nothing is missing:

`PREMISE: <r> reference(s) checked | <m> missing | <a> ambiguous (surfaced, not blocking)`
`RECALL: <n> claim(s) surfaced | <s> by symbol | <h> by handle | <a> by area | <f> by finding | <r> retired skipped — advisory (blocks nothing)`
`REFINE: <U> unresolved surfaced | <a> want-decision asked | <b> how-decision resolved+cited | <s> ASSUMED | skip: yes/no`

A run that emits `REFINE:` without `PREMISE:` or without `RECALL:` is **incomplete** — neither check is
optional and neither count is inferable from the other lines.

When `skip: yes`, the `REFINE:` line (with `U = 0`) plus the `PREMISE:` and `RECALL:` lines are the whole
output and refine hands to `analysis`. A skip still recalls: the advisory surface costs nothing and is
most useful exactly on the ticket refine had nothing to expose about.

## Epic detection — ticket vs epic (routes the rest of the lifecycle)

Having scanned and tried to expose, refine also judges whether the input is a single **ticket** or an
**EPIC** — a whole app / feature-suite that contains many tickets (e.g. "build the mobile app", "add a
new game"). **Signal:** the exposed work spans **multiple independent, each-execute-able
deliverables**. On an epic, record it as a counted decision and route to the **epic path**
(`analysis(epic) → design(epic) → breakdown → N× ticket-lifecycles`; see `breakdown`), which is thin by
design (only enough to split) — its re-ratification behaviour is **Experimental** and expected to
be refined by retro (see `<mango>/PRINCIPLES.md`, Maturity). A single deliverable → the
normal ticket path (`analysis → design → execute → review → finalize`).

**Epic path is not exempt from the exposure-checker (dispatch it BEFORE breakdown).** On the epic
path, refine dispatches the **SAME 1-dispatch ticket-blind exposure-checker** the ticket path uses
(Step 6) — **exactly one dispatch, not a debate** — over the epic's exposed set, asking only *"is any
product-decision still un-exposed?"* This runs **before `breakdown`**, and any decision it surfaces
re-enters Step 2 (classify → want-decision/how-decision, tie-breaker applied). Its findings **surface
for the human to ratify along with the breakdown** — so the epic, the costliest place for an
un-exposed decision, gets the same backstop the ticket path already has, never zero.

## Self-check, then hand off (no gate of refine's own)

refine does not hold a ✋ gate of its own — its want-decision questions ARE its interaction, and its
output is challenged at Gate 1. Before handing off, confirm: the project was scanned; the premise check
ran and its `PREMISE:` line is emitted (any referenced-as-existing miss having halted the phase with
`PREMISE FALSIFIED`);
the advisory recall ran and its `RECALL:` line is emitted (type 1 by symbol, **type 2 by handle**, type 5 by area, type 6 by
the re-raised finding, `retired:` claims skipped) having **injected and blocked nothing**; every surfaced
decision was classified want-decision/how-decision (tie-breaker applied) **before** anything was asked;
every how-decision carries a **citation** (an uncited how-decision is flagged as a finding) and was
**not** asked; every acceptance-bar decision was treated as a want-decision (asked or `ASSUMED`), never
silently cited as a how-decision; every want-decision was asked in want-language; any handed-back
want-decision is `ASSUMED (awaiting ratification)` (never settled prose) and requires an explicit
next-gate confirm (tripwire checked); the exposure-checker ran (1 dispatch) unless refine skipped; and
the `REFINE:` line is emitted. Then write Phase 0 into the working doc + `Session status` and continue
to `analysis` (or, on an epic, the epic path).
