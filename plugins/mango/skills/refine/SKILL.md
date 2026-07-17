---
name: refine
description: Phase 0 of the mango ticket lifecycle — the FIRST phase. Use when a request arrives raw. Scans the project for context, TRIES to expose the unresolved product-decisions, classifies each as HOW (loại-B → self-resolve + cite) or WANT (loại-A → ask the user), and emits a refined ticket as counted artifacts for analysis. Self-skips when the ticket is already clear. Detects an epic and routes to the epic path.
---

Operate under `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` — especially its **expose / ask / never-author**
boundary for intent. refine is the **first** phase of the lifecycle; it runs before `analysis`. Its
whole job is to turn a raw request into a **refined ticket** without ever authoring the user's intent:
it **exposes** the product-decisions and puts the WANT ones to the human, resolving the HOW ones itself
with a citation. **Every decision refine makes is a counted artifact** (visible, challengeable at the
next gate) — never buried in prose.

**Ground rules.** Read `${CLAUDE_PROJECT_DIR}/.harness.json` first. If it is missing, STOP and tell the
user to create one from `${CLAUDE_PLUGIN_ROOT}/config/harness.example.json`. refine writes **no code**
and makes **no tracker write**. It reads the project read-only and records its output in the working
doc's Phase-0 block (from `${CLAUDE_PLUGIN_ROOT}/templates/ticket.md`).

> **HARD invariants (verified in Finish, guarded by `scripts/validate.py`):**
> - refine **exposes for the human to chốt, and NEVER authors intent** — the descriptive/normative
>   (derivable/intent) boundary is the same one `codify` holds for rules.
> - refine **self-skips** when the ticket is already clear — it must NOT become a tax on every ticket.
> - refine reuses existing machinery only (`sitemap`/`db-map`, the ticket-blind `challenger`,
>   `codify`'s provisional→ratify, `AskUserQuestion`). It convenes **no** Council and burns **no**
>   multi-advisor debate.

## Step 0 — scan the project for context (do NOT ask what the scan can answer)

mango always runs inside an existing project. refine FIRST **scans** it, read-only: directory
structure, README, package manifest / dependencies, config, and the existing code + conventions —
**reusing the `sitemap` and `db-map` capabilities** (use a generated `config.docs_dir/sitemap.md` /
`db-map.md` if present, else a lightweight read-only enumeration; delegate bulk read-and-extract to the
Haiku `extractor` per `PRINCIPLES.md`). **Depth of exposure comes from the scan, not from luck and not
from asking the user what the scan can answer.** A README or an existing repeated pattern frequently
reveals the request to be the *Nth item following an established convention* — which turns most
would-be questions into **derivable-with-citation** answers rather than questions for the user.

## Step 1 — the readiness gate is the natural result of trying to expose (ask no one)

refine **TRIES to expose** the unresolved product-decisions the request carries. **The count it finds
IS the answer** — there is no separate "should I run refine?" question to put to anyone:

- **0 unresolved product-decisions → SKIP refine → analysis.** Record the skip as a counted artifact:
  `refine skipped: 0 unresolved product-decisions` — then hand straight to `analysis`.
- **≥1 unresolved → refine works** (Steps 2–6 below).
- **When in doubt → run.** Over-triggering only wastes a little; under-triggering is dangerous. The
  skip decision is itself **recorded** (counted), so a skip is auditable.

**Right-sizing.** Exposure depth scales with rawness: a clear ticket over a strong convention →
near-total skip (often only one genuine loại-A question survives, no over-trigger); a raw brief → more
exposure. refine must never fabricate loại-A questions to look busy.

## Step 2 — ⭐ classify EVERY decision BEFORE asking (resolve "I don't know" up front)

For **each** product-decision refine surfaces, classify it BEFORE anything is put to the user:

- **Loại B (CÁCH LÀM / HOW):** the answer already exists in convention / code / the rule book, or is a
  tool/technique choice. refine **resolves it itself and CITES the source** (`file:line`, convention,
  rulebook §) — it **does NOT ask the user.** Asking a HOW-question forces a rubber-stamp, which is
  **laundering** a decision refine could make.
  - **⭐ Self-check before putting ANY question to the user:** *"Can existing convention / code / the
    rule book answer this? If YES → it is loại-B → cite it, don't ask."* (This is the guard that stops
    refine wrongly asking a loại-B as a loại-A — e.g. asking "do we need a win-screen?" when the
    convention already answers it.)
- **Loại A (Ý MUỐN / WANT):** the **user is the sole source** — intent, priority, stakes, or a
  genuinely new design choice the scan cannot answer. **Ask the user**, phrased in **want-language, not
  technical language.** Use `AskUserQuestion`'s typed, required-selection fork. `(Recommended)` may
  appear **only here**, with its reason in the option description (an informed pick, never a blind one).

## Step 3 — refine stops at DIRECTION, not TOOL

refine exposes **solution DIRECTIONS** whose trade-offs a non-technical user can feel (e.g. *wrap the
existing thing* vs *rebuild it*), never the specific TOOL/library — **tool selection is analysis's
job.** The test: if you put it to the user and they can answer immediately, it is a direction/WANT
(refine); if they would say *"I don't know, help me decide"*, it is a tool/HOW (analysis picks it, or
refine self-resolves it if derivable).

## Step 4 — handle "do your recommendation" / "your call" on a loại-A question

When the user hands a loại-A decision back ("your call", "do the recommended one"), refine does **NOT**
silently adopt it. It:

1. Picks per the recommendation **but marks the choice `ASSUMED (awaiting ratification)`** — reusing
   `codify`'s provisional→ratify machinery, not a parallel one.
2. The assumption **surfaces again at a later gate** (Gate 1 / design) for the user to confirm **once
   it is concrete** — an assumption is easier to ratify against a real change list than against a raw
   brief.
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
convene a Council. Any decision the exposure-checker surfaces re-enters Step 2 (classify → loại-A/B).
Emit one Cost-ledger row for this dispatch per `PRINCIPLES.md`.

## Output — the refined ticket (the input to analysis)

Emit all of the following as **counted artifacts** in the working doc's Phase-0 block — never prose:

- **Ý muốn đã chốt (loại-A, from the user)** → become **acceptance-criteria constraints** analysis must
  honour.
- **Hướng + căn cứ (loại-B, refine-resolved + cited)** → a **starting premise** for analysis (which
  still picks the tools).
- **ASSUMED (awaiting ratification)** → questions analysis must resolve and **confirm-when-concrete** at
  a later gate.
- **Constraints surfaced from the scan** (rule book, design tokens, policy the user could not have
  known to ask about).

Emit the counting line so the exposure is auditable:

`REFINE: <U> unresolved surfaced | <a> loại-A asked | <b> loại-B resolved+cited | <s> ASSUMED | skip: yes/no`

When `skip: yes`, that single line (with `U = 0`) is the whole output and refine hands to `analysis`.

## Epic detection — ticket vs epic (routes the rest of the lifecycle)

Having scanned and tried to expose, refine also judges whether the input is a single **ticket** or an
**EPIC** — a whole app / feature-suite that contains many tickets (e.g. "build the mobile app", "add a
new game"). **Signal:** the exposed work spans **multiple independent, each-execute-able
deliverables**. On an epic, record it as a counted decision and route to the **epic path**
(`analysis(epic) → design(epic) → breakdown → N× ticket-lifecycles`; see `breakdown`), which is marked
**v1 — enough to run and learn** and is expected to be refined by retro. A single deliverable → the
normal ticket path (`analysis → design → execute → review → finalize`).

## Self-check, then hand off (no gate of refine's own)

refine does not hold a ✋ gate of its own — its loại-A questions ARE its interaction, and its output is
challenged at Gate 1. Before handing off, confirm: the project was scanned; every surfaced decision was
classified loại-A/loại-B **before** anything was asked; every loại-B carries a **citation** and was
**not** asked; every loại-A was asked in want-language; any handed-back loại-A is `ASSUMED (awaiting
ratification)` (tripwire checked); the exposure-checker ran (1 dispatch) unless refine skipped; and the
`REFINE:` line is emitted. Then write Phase 0 into the working doc + `Session status` and continue to
`analysis` (or, on an epic, the epic path).
